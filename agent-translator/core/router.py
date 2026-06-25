import sys
import requests
from providers.groq import GroqProvider
from providers.ollama import OllamaProvider
from providers.gemini import GeminiProvider

def check_ollama_status(model_name: str) -> bool:
    """Check if Ollama is running and has the requested model ALREADY LOADED in memory.
       If it is not loaded in memory, trigger a background load and return False."""
    import threading
    from core.logger import get_logger
    logger = get_logger()
    try:
        # Check if loaded in memory
        resp = requests.get("http://localhost:11434/api/ps", timeout=2)
        if resp.status_code == 200:
            loaded_models = [m["name"] for m in resp.json().get("models", [])]
            if model_name in loaded_models:
                return True
                
        # If we reach here, it's either not loaded or /api/ps failed but server is up.
        # Let's verify if the model even exists on disk before attempting to load it.
        tags_resp = requests.get("http://localhost:11434/api/tags", timeout=2)
        if tags_resp.status_code == 200:
            disk_models = [m["name"] for m in tags_resp.json().get("models", [])]
            if model_name in disk_models:
                logger.info(f"[ROUTER] Ollama model '{model_name}' is on disk but NOT loaded. Triggering background load.")
                
                # Use subprocess to detach the background load from the main python process
                import subprocess
                try:
                    subprocess.Popen(
                        ["curl", "-s", "-X", "POST", "http://localhost:11434/api/generate", 
                         "-d", f'{{"model": "{model_name}", "keep_alive": "30m"}}'],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        start_new_session=True # Fully detach
                    )
                    logger.info(f"[ROUTER] Spawned background curl to load '{model_name}'.")
                except Exception as e:
                    logger.error(f"[ROUTER] Background load spawn failed: {e}")
                
    except requests.exceptions.RequestException:
        pass
    return False

def analyze_complexity(message: str) -> bool:
    """
    Returns True if the message is deemed 'complex'.
    Complex messages are routed to the API. Simple messages go to local.
    """
    # Heuristic 1: Word count
    words = message.split()
    if len(words) > 50:
        return True
        
    # Heuristic 2: Character count
    if len(message) > 400:
        return True
        
    # Heuristic 3: Code snippets or JSON markers
    if any(c in message for c in ["{", "}", "`", "def ", "function "]):
        return True
        
    return False

def _make_provider(config: dict):
    """Factory: create the right provider instance from a config dict."""
    name = config.get("name", "")
    if name == "ollama":
        return OllamaProvider(config)
    elif name == "groq":
        return GroqProvider(config)
    elif name == "gemini":
        return GeminiProvider(config)
    raise ValueError(f"Unknown provider: {name}")

def select_provider(config: dict, message: str, force_api: bool = False, provider_override: str = None):
    """
    Selects the best provider based on configuration, message complexity, or manual override.
    Returns an instance of a Provider subclass.
    """
    from core.logger import get_logger
    logger = get_logger()
    
    providers_list = config.get("providers", [])
    
    if provider_override:
        override_config = next((p for p in providers_list if p.get("name") == provider_override), None)
        if override_config:
            logger.info(f"[ROUTER] Manual override selected: {provider_override}")
            return _make_provider(override_config)
        else:
            logger.warning(f"[ROUTER] Override provider '{provider_override}' not found in config. Falling back to auto.")
            print(f"Warning: Override provider '{provider_override}' not found in config. Falling back to auto.", file=sys.stderr)

    ollama_config = next((p for p in providers_list if p.get("name") == "ollama"), None)
    groq_config = next((p for p in providers_list if p.get("name") == "groq"), None)
    gemini_config = next((p for p in providers_list if p.get("name") == "gemini"), None)
    
    # Build API cascade: Groq > Gemini
    api_configs = [c for c in [groq_config, gemini_config] if c]
    if not api_configs:
        logger.critical("[ROUTER] No API provider configured!")
        raise RuntimeError("No API provider configured (need groq or gemini).")

    if force_api:
        # Try each API in cascade order
        for api_cfg in api_configs:
            logger.info(f"[ROUTER] Forced API routing → trying {api_cfg.get('name')}.")
            return _make_provider(api_cfg)
    
    # Strategy: Always try Ollama first if available, unless the message is too complex.
    # The pipeline's entropy check will fallback to API if quality is low.
    is_complex = analyze_complexity(message)
    if ollama_config and not is_complex:
        ollama_ready = check_ollama_status(ollama_config.get("model", ""))
        if ollama_ready:
            logger.info("[ROUTER] Ollama is READY. Routing to Local (entropy fallback will catch bad quality).")
            return OllamaProvider(ollama_config)
        else:
            logger.warning("[ROUTER] Ollama is NOT READY. Falling back to API cascade.")
    elif ollama_config and is_complex:
        logger.info("[ROUTER] Message is COMPLEX (>50 words or code). Skipping Ollama and routing to API directly.")
    
    # Cascade through API providers
    logger.info(f"[ROUTER] Routing to API cascade: {[c.get('name') for c in api_configs]}")
    return _make_provider(api_configs[0])
