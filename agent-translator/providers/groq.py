import sys
import requests
from providers.base import Provider

class GroqProvider(Provider):
    def complete(self, system: str, user: str) -> str:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "temperature": 0.0,
            "logprobs": True,
            "top_logprobs": 3,
            "stream": True,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ]
        }
        
        try:
            import json
            response = requests.post(url, headers=headers, json=payload, timeout=60, stream=True)
            
            # If the model doesn't support logprobs, retry without it
            if response.status_code == 400 and "logprobs" in response.text:
                from core.logger import get_logger
                get_logger().warning("[GROQ] Model doesn't support logprobs. Retrying without.")
                payload.pop("logprobs", None)
                payload.pop("top_logprobs", None)
                response = requests.post(url, headers=headers, json=payload, timeout=60, stream=True)
            
            response.raise_for_status()
            
            full_content = ""
            total_logprob = 0.0
            logprob_count = 0
            
            print("", file=sys.stderr, flush=True) # start fresh line
            for line in response.iter_lines():
                if line:
                    decoded = line.decode('utf-8')
                    if decoded.startswith("data: "):
                        data_str = decoded[6:]
                        if data_str.strip() == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data_str)
                            choice = chunk.get("choices", [{}])[0]
                            delta = choice.get("delta", {})
                            content_piece = delta.get("content", "")
                            if content_piece:
                                full_content += content_piece
                                print(content_piece, end="", file=sys.stderr, flush=True)
                                
                            # Parse logprobs if available
                            logprobs = choice.get("logprobs", {})
                            if logprobs:
                                content_lp = logprobs.get("content", [])
                                if content_lp:
                                    for t in content_lp:
                                        total_logprob += t.get("logprob", 0.0)
                                        logprob_count += 1
                            
                            # Parse token usage (available in final chunks or x-groq usage)
                            usage = chunk.get("usage") or chunk.get("x_groq", {}).get("usage", {})
                            if usage:
                                self.last_input_tokens = usage.get("prompt_tokens", self.last_input_tokens)
                                self.last_output_tokens = usage.get("completion_tokens", self.last_output_tokens)
                        except json.JSONDecodeError:
                            pass
                            
            print("\n", file=sys.stderr, flush=True)
            
            if logprob_count > 0:
                self.last_entropy = total_logprob / logprob_count
            else:
                self.last_entropy = 0.0
            
            return full_content
        except requests.exceptions.RequestException as e:
            from core.logger import get_logger
            get_logger().error(f"[GROQ] API Request failed: {e}")
            print(f"Groq API error: {e}", file=sys.stderr)
            if 'response' in locals() and response is not None and hasattr(response, 'text'):
                get_logger().debug(f"[GROQ] Response body: {response.text}")
                print(response.text, file=sys.stderr)
            raise RuntimeError(f"Groq completion failed: {e}")
