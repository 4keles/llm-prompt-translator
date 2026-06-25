import sys
import requests
from providers.base import Provider

class OllamaProvider(Provider):
    def _get_keep_alive(self) -> str:
        """
        Determine keep_alive duration based on config or available RAM.
        If free RAM > 5GB → keep model loaded for 30m.
        Otherwise → default 5m.
        Config override takes priority.
        """
        # Config override (e.g. keep_alive: "1h" or keep_alive: "-1")
        configured = self.config.get("keep_alive")
        if configured is not None:
            return str(configured)
        
        # Smart RAM check
        try:
            import os
            mem_info = {}
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    parts = line.split()
                    if len(parts) >= 2:
                        mem_info[parts[0].rstrip(":")] = int(parts[1])  # kB
            
            free_kb = mem_info.get("MemAvailable", 0)
            free_gb = free_kb / (1024 * 1024)
            
            from core.logger import get_logger
            get_logger().debug(f"[OLLAMA] Available RAM: {free_gb:.1f} GB")
            
            if free_gb > 5.0:
                return "30m"   # Plenty of RAM → keep loaded 30 min
            elif free_gb > 3.0:
                return "10m"   # Moderate RAM → 10 min
            else:
                return "5m"    # Low RAM → default 5 min
        except Exception:
            return "5m"  # Fallback

    def complete(self, system: str, user: str) -> str:
        api_url = self.config.get("api_url", "http://localhost:11434")
        url = f"{api_url}/api/chat"
        
        keep_alive = self._get_keep_alive()
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ],
            "stream": True,
            "options": {"temperature": 0.0},
            "logprobs": True,
            "keep_alive": keep_alive
        }
        
        try:
            import json
            response = requests.post(url, json=payload, timeout=120, stream=True)
            response.raise_for_status()
            
            full_content = ""
            total_logprob = 0.0
            logprob_count = 0
            
            # Read streaming response
            print("", file=sys.stderr, flush=True) # start fresh line
            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line.decode('utf-8'))
                    
                    if "message" in chunk and "content" in chunk["message"]:
                        content_piece = chunk["message"]["content"]
                        full_content += content_piece
                        print(content_piece, end="", file=sys.stderr, flush=True)
                        
                    # Calculate Average Logprob (Entropy)
                    logprobs_list = chunk.get("logprobs", [])
                    if logprobs_list:
                        for item in logprobs_list:
                            total_logprob += item.get("logprob", 0.0)
                            logprob_count += 1
                            
                    if chunk.get("done"):
                        # Parse token usage from the final chunk
                        self.last_input_tokens = chunk.get("prompt_eval_count", 0)
                        self.last_output_tokens = chunk.get("eval_count", 0)
                        print("\n", file=sys.stderr, flush=True)
                        break
            
            if logprob_count > 0:
                self.last_entropy = total_logprob / logprob_count
            else:
                self.last_entropy = 0.0

            return full_content
        except requests.exceptions.RequestException as e:
            from core.logger import get_logger
            get_logger().error(f"[OLLAMA] API Request failed: {e}")
            print(f"Ollama API error: {e}", file=sys.stderr)
            if 'response' in locals() and response is not None and hasattr(response, 'text'):
                get_logger().debug(f"[OLLAMA] Response body: {response.text}")
                print(response.text, file=sys.stderr)
            raise RuntimeError(f"Ollama completion failed: {e}")
