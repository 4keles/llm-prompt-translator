import sys
import requests
from providers.base import Provider

class GeminiProvider(Provider):
    def complete(self, system: str, user: str) -> str:
        # Gemini API v1beta - generateContent endpoint
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:streamGenerateContent?alt=sse&key={self.api_key}"
        )
        
        payload = {
            "contents": [
                {"role": "user", "parts": [{"text": user}]}
            ],
            "systemInstruction": {
                "parts": [{"text": system}]
            },
            "generationConfig": {
                "temperature": 0.0,
                "responseMimeType": "text/plain",
                "responseLogprobs": True,
                "logprobs": 2
            }
        }
        
        try:
            import json
            response = requests.post(url, json=payload, timeout=60, stream=True)
            
            if response.status_code == 400 and "Logprobs is not enabled" in response.text:
                from core.logger import get_logger
                get_logger().warning("[GEMINI] Model doesn't support logprobs. Retrying without.")
                payload["generationConfig"].pop("responseLogprobs", None)
                payload["generationConfig"].pop("logprobs", None)
                response = requests.post(url, json=payload, timeout=60, stream=True)
                
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
                            candidate = chunk.get("candidates", [{}])[0]
                            
                            content_part = candidate.get("content", {}).get("parts", [{}])[0]
                            content_piece = content_part.get("text", "")
                            if content_piece:
                                full_content += content_piece
                                print(content_piece, end="", file=sys.stderr, flush=True)
                                
                            # Aggregate logprobs if available in the chunk
                            logprobs_result = candidate.get("logprobsResult", {})
                            top_candidates = logprobs_result.get("topCandidates", [])
                            if top_candidates:
                                for tc in top_candidates:
                                    candidates_list = tc.get("candidates", [])
                                    if candidates_list:
                                        total_logprob += candidates_list[0].get("logProbability", 0.0)
                                        logprob_count += 1
                            
                            # Parse token usage from usageMetadata
                            usage_meta = chunk.get("usageMetadata", {})
                            if usage_meta:
                                self.last_input_tokens = usage_meta.get("promptTokenCount", self.last_input_tokens)
                                self.last_output_tokens = usage_meta.get("candidatesTokenCount", self.last_output_tokens)
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
            get_logger().error(f"[GEMINI] API Request failed: {e}")
            print(f"Gemini API error: {e}", file=sys.stderr)
            if 'response' in locals() and response is not None and hasattr(response, 'text'):
                get_logger().debug(f"[GEMINI] Response body: {response.text}")
                print(response.text, file=sys.stderr)
            raise RuntimeError(f"Gemini completion failed: {e}")
