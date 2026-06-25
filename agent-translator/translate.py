#!/usr/bin/env python3
import sys
import argparse
try:
    import readline
except ImportError:
    pass
from core.pipeline import run_pipeline

def main():
    parser = argparse.ArgumentParser(
        description="Prompt-Translator: Converts Turkish or broken English into clean, structured English prompts for LLM agents.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    parser.add_argument("args", nargs="*", help="The message to translate. You can optionally prefix with a mode (e.g. 'translate', 'problem', 'reply').")
    parser.add_argument("-c", "--clarify", type=str, help="Pre-supply a clarification for a dangling reference to skip interactive questioning.")
    parser.add_argument("-m", "--model", type=str, help="Force a specific provider (e.g., 'groq', 'ollama', 'gemini'). Overrides the smart router.")
    parser.add_argument("-t", type=int, default=0, choices=[0, 1, 2],
                        help="Translation Direction:\n  0 = TR -> EN (Default)\n  1 = EN -> TR\n  2 = EN -> EN (Cleanup/Refactor)")
    parser.add_argument("-p", "--profile", type=str, default="default", help="Profile name to load specific prompt rules from (e.g., 'video', 'ai-videom'). Default is 'default'.")
    parser.add_argument("--manage-profiles", action="store_true", help="Launch the interactive Profile Manager to create or delete prompt profiles.")
    parser.add_argument("--stats", action="store_true", help="Display usage statistics from logs and exit.")
    parser.add_argument("--no-copy", action="store_true", help="Print the result to stdout but do NOT copy it to the clipboard.")
    parser.add_argument("--raw", action="store_true", help="Print ONLY the compiled translated text. Suppresses the footer and domain metadata.")
    parser.add_argument("-q", "--max-questions", type=int, default=5,
                        help="Maximum clarification rounds (default: 5). Set to 0 for unlimited.")
    
    args = parser.parse_args()

    if args.stats:
        from core.stats import print_stats
        print_stats()
        return

    if args.manage_profiles:
        from core.profile_manager import manage
        manage()
        return
        
    if not args.args:
        print("Error: The message argument is required unless --manage-profiles or --stats is used.", file=sys.stderr)
        parser.print_help()
        sys.exit(1)
    
    DIRECTION_MAP = {0: "tr-en", 1: "en-tr", 2: "en-en"}
    direction = DIRECTION_MAP[args.t]
    profile = args.profile
    
    mode = "auto"
    message = ""
    
    if len(args.args) >= 2 and args.args[0] in ["auto", "problem", "translate", "reply"]:
        mode = args.args[0]
        message = " ".join(args.args[1:])
    else:
        message = " ".join(args.args)
        
    from core.logger import get_logger
    logger = get_logger()
    logger.info("="*40)
    logger.info(f"[NEW REQUEST] Mode: {mode} | Direction: {direction} | Profile: {profile}")
    logger.debug(f"[RAW INPUT]: {message}")
        
    try:
        # Run the minimal pipeline with optional model override
        parsed_json = run_pipeline(message, mode, provider_override=args.model, direction=direction, profile=profile)
        
        # Interactive Clarification Loop
        max_clarifications = args.max_questions  # 0 = unlimited
        clarification_count = 0
        
        while isinstance(parsed_json, dict) and parsed_json.get("unclear") and len(parsed_json["unclear"]) > 0:
            if max_clarifications > 0 and clarification_count >= max_clarifications:
                print(f"\n[WARNING] Maximum clarifications ({max_clarifications}) reached. Forcing completion.", file=sys.stderr)
                logger.warning(f"[PIPELINE] Max clarifications ({max_clarifications}) reached. Breaking loop.")
                break
                
            limit_label = f"/{max_clarifications}" if max_clarifications > 0 else "/∞"
            print(f"\n--- Clarification Needed (Round {clarification_count + 1}{limit_label}) ---", file=sys.stderr)
            clarifications_made = False
            for item in parsed_json["unclear"]:
                question = item.get("question")
                if question:
                    print(f"? {question}", file=sys.stderr)
                    try:
                        ans = input("> ")
                        ans_lower = ans.strip().lower()
                        if ans_lower == "exit":
                            clarification_count = max_clarifications # Force exit
                            break
                        if not ans.strip() or ans_lower == "skip":
                            continue
                            
                        message += f"\n[Clarification: {question} -> {ans.strip()}]"
                        clarifications_made = True
                    except EOFError:
                        clarification_count = max_clarifications
                        break
                    except KeyboardInterrupt:
                        print("\n[CANCELLED] Translation aborted.", file=sys.stderr)
                        sys.exit(0)
            
            if clarifications_made:
                clarification_count += 1
                print("\n[ROUTER] Re-running pipeline with clarifications...", file=sys.stderr)
                logger.info(f"[PIPELINE] Re-running (Round {clarification_count}).")
                
                next_override = args.model
                if isinstance(parsed_json, dict) and "_provider" in parsed_json:
                    used_provider = parsed_json["_provider"]
                    if used_provider != "ollama" and next_override is None:
                        next_override = used_provider
                        
                parsed_json = run_pipeline(message, mode, provider_override=next_override, direction=direction, profile=profile)
            else:
                break # No answers given, break the loop

        result = parsed_json.get("compiled", str(parsed_json)) if isinstance(parsed_json, dict) else str(parsed_json)

        logger.info("[SUCCESS] Translation complete.")
        logger.debug(f"[FINAL OUTPUT]: {result}")
        print(result)
        
        # Copy to clipboard unless --no-copy is set
        if not args.no_copy:
            try:
                import subprocess
                process = subprocess.Popen(
                    ["xclip", "-selection", "clipboard"],
                    stdin=subprocess.PIPE
                )
                process.communicate(result.encode("utf-8"))
                print("-- Copied to clipboard! --", file=sys.stderr)
                logger.info("[CLIPBOARD] Copied to clipboard.")
            except FileNotFoundError:
                # xclip not installed, try xsel
                try:
                    process = subprocess.Popen(
                        ["xsel", "--clipboard", "--input"],
                        stdin=subprocess.PIPE
                    )
                    process.communicate(result.encode("utf-8"))
                    print("-- Copied to clipboard! --", file=sys.stderr)
                    logger.info("[CLIPBOARD] Copied to clipboard (xsel).")
                except FileNotFoundError:
                    print("-- Clipboard not available (install xclip or xsel). --", file=sys.stderr)
                    logger.warning("[CLIPBOARD] No clipboard tool found.")
    except Exception as e:
        logger.error(f"[FATAL] Failed to translate: {e}")
        print(f"Failed to translate: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
