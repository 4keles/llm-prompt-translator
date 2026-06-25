import os
import glob
from collections import defaultdict

def print_stats():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    logs_dir = os.path.join(base_dir, "logs")
    
    if not os.path.exists(logs_dir):
        print(f"No logs directory found at {logs_dir}.")
        return

    log_files = glob.glob(os.path.join(logs_dir, "translator_*.log"))
    if not log_files:
        print("No log files found.")
        return

    import yaml
    from datetime import datetime

    # Load config limits
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.yaml")
    limits = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                for provider in config.get("providers", []):
                    name = str(provider.get("name", "")).upper()
                    limit = provider.get("free_daily_limit")
                    limits[name] = limit if limit is not None else "Unlimited"
        except Exception:
            pass

    provider_counts_total = defaultdict(int)
    provider_counts_today = defaultdict(int)
    profile_counts = defaultdict(int)
    total_requests = 0

    today_str = datetime.now().strftime("%Y-%m-%d")

    for log_file in log_files:
        is_today = today_str in log_file
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    if "[PIPELINE] Invoking" in line:
                        total_requests += 1
                        parts = line.split("[PIPELINE] Invoking")
                        if len(parts) > 1:
                            info = parts[1].strip()
                            info_parts = info.split(" with profile ")
                            provider_name = info_parts[0].strip().upper()
                            
                            provider_counts_total[provider_name] += 1
                            if is_today:
                                provider_counts_today[provider_name] += 1
                                
                            if len(info_parts) > 1:
                                profile_name = info_parts[1].strip()
                                profile_counts[profile_name] += 1
        except Exception as e:
            print(f"Error reading {log_file}: {e}")

    print("=" * 60)
    print(" LLM PROMPT TRANSLATOR - USAGE STATISTICS")
    print("=" * 60)
    print(f"Total Requests Processed All Time: {total_requests}")
    print("\n--- Provider Usage ---")
    for provider, total_count in sorted(provider_counts_total.items(), key=lambda item: item[1], reverse=True):
        today_count = provider_counts_today[provider]
        limit = limits.get(provider, "Unknown")
        print(f"  {provider:<10}: {total_count:<5} Total Requests | Today: {today_count} / {limit}")
        
    print("\n--- Profile Usage (All Time) ---")
    for profile, count in sorted(profile_counts.items(), key=lambda item: item[1], reverse=True):
        print(f"  {profile:<10}: {count} requests")
    print("=" * 60)

if __name__ == "__main__":
    print_stats()
