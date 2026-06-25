import sys
import json
import os
from core.config import load_config
from core.router import select_provider

def _load_prompt(filename: str, profile: str = "default", fallback: str = "") -> str:
    base_dir = os.path.join(os.path.dirname(__file__), "..", "prompts", "profiles")
    profile_path = os.path.join(base_dir, profile, filename)
    default_path = os.path.join(base_dir, "default", filename)
    
    if os.path.exists(profile_path):
        with open(profile_path, "r", encoding="utf-8") as f:
            return f.read()
    elif os.path.exists(default_path):
        with open(default_path, "r", encoding="utf-8") as f:
            return f.read()
            
    return fallback

def _load_system_prompt(direction: str = "tr-en", profile: str = "default") -> str:
    # Core Constitution
    system_core = _load_prompt("system.md", profile, "You are prompt-translator. Output valid JSON.")
    
    # Auxiliary Prompts
    default_rules = _load_prompt("rules.md", "default", "")
    profile_rules = _load_prompt("rules.md", profile, "")
    
    if profile != "default" and profile_rules and profile_rules != default_rules:
        combined_rules = f"{default_rules}\n\n## Specific Profile Rules ({profile})\n{profile_rules}"
    else:
        combined_rules = default_rules
        
    compiler_ctx = _load_prompt("compiler.md", profile, "")
    
    # Direction-specific instruction injected before core prompt
    direction_instructions = {
        "tr-en": (
            "The user will write in Turkish (or broken English). "
            "Translate their message into clean, professional English."
        ),
        "en-tr": (
            "CRITICAL: The user will write in English. "
            "You MUST translate their message into Turkish. "
            "The 'compiled' field in your JSON output MUST be entirely in Turkish. "
            "Do NOT output English in the 'compiled' field. "
            "Use native Turkish technical terminology where appropriate."
        ),
        "en-en": (
            "The user will write in English (possibly broken or informal). "
            "Rephrase and clean up their message into clear, professional English. "
            "Fix grammar, improve clarity, and use proper technical terminology."
        ),
    }
    
    dir_prompt = direction_instructions.get(direction, direction_instructions["tr-en"])
    
    return f"## Translation Direction\n{dir_prompt}\n\n{system_core}\n\n## Profile Rules & Context\n{combined_rules}\n\n{compiler_ctx}"

def run_pipeline(message: str, mode: str, provider_override: str = None, direction: str = "tr-en", profile: str = "default") -> str:
    """
    Main Pipeline using the Smart Router.
    """
    from core.logger import get_logger
    logger = get_logger()
    
    config = load_config()
    
    # 1. Select initial provider based on complexity & availability or manual override
    provider = select_provider(config, message, force_api=False, provider_override=provider_override)
    system_prompt = _load_system_prompt(direction, profile)
    logger.info(f"[PIPELINE] Direction: {direction} | Profile: {profile}")
    
    # 2. Get completion
    print(f"[{provider.name.upper()}] Translating (Profile: {profile})...", file=sys.stderr)
    logger.info(f"[PIPELINE] Invoking {provider.name.upper()} with profile {profile}")
    result_text = provider.complete(system=system_prompt, user=f"<user_input>\n{message}\n</user_input>")
    logger.debug(f"[PIPELINE] Raw response received: {result_text}")
    
    # 3. Check for JSON validity and Confidence Fallback
    parsed_json = None
    try:
        # Simple extraction in case the model wraps it in markdown ```json ... ```
        clean_text = result_text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
            
        parsed_json = json.loads(clean_text)
        logger.info("[PIPELINE] Successfully parsed JSON response.")
    except json.JSONDecodeError as e:
        logger.error(f"[PIPELINE] JSON Parse Error: {e}")
        pass # Handle parsing error in later goal (J2.3)

    if parsed_json and isinstance(parsed_json, dict):
        # Confidence fallback logic using TRUE MATHEMATICAL ENTROPY (Logprobs)
        # Threshold: -0.2 (approx 82% confidence per token on average)
        if provider.last_entropy < -0.2 and provider.last_entropy != 0.0 and provider_override is None:
            logger.warning(f"[PIPELINE] Model entropy is LOW ({provider.last_entropy:.3f}). Triggering fallback to API.")
            print(f"[ROUTER] Model entropy is LOW ({provider.last_entropy:.3f}). Falling back...", file=sys.stderr)
            fallback_provider = select_provider(config, message, force_api=True)
            print(f"[{fallback_provider.name.upper()}] Translating (Fallback)...", file=sys.stderr)
            result_text = fallback_provider.complete(system=system_prompt, user=message)
            
            # Re-parse if needed
            try:
                clean_text = result_text.strip()
                if clean_text.startswith("```json"): clean_text = clean_text[7:]
                if clean_text.endswith("```"): clean_text = clean_text[:-3]
                parsed_json = json.loads(clean_text)
                logger.info("[PIPELINE] Fallback JSON parsed successfully.")
            except Exception as e: 
                logger.error(f"[PIPELINE] Fallback JSON parse failed: {e}")
                
            # Use the fallback provider's entropy and token counts
            final_entropy = fallback_provider.last_entropy
            final_input_tokens = fallback_provider.last_input_tokens
            final_output_tokens = fallback_provider.last_output_tokens
            parsed_json["_provider"] = fallback_provider.name
        else:
            final_entropy = provider.last_entropy
            final_input_tokens = provider.last_input_tokens
            final_output_tokens = provider.last_output_tokens
            parsed_json["_provider"] = provider.name

    # Print output
    if parsed_json and "compiled" in parsed_json:
        # Also print the domain/entropy/tokens nicely to stderr
        domain = parsed_json.get("domain", "unknown")
        logger.info(f"[PIPELINE] Translation completed. Domain: {domain}, Entropy: {final_entropy:.3f}, Tokens: {final_input_tokens}→{final_output_tokens}")
        print(f"--- [Domain: {domain} | Entropy: {final_entropy:.3f} | Tokens: {final_input_tokens}→{final_output_tokens}] ---", file=sys.stderr)
        
        # Attach token metadata to parsed_json for upstream consumers
        parsed_json["_tokens"] = {
            "input": final_input_tokens,
            "output": final_output_tokens,
            "total": final_input_tokens + final_output_tokens
        }
        return parsed_json
        
    logger.warning("[PIPELINE] Failed to extract 'compiled' field. Returning raw text.")
    return result_text
