import os
import yaml
import sys
import re

def load_dotenv(path=".env"):
    """Minimal .env loader so we don't need python-dotenv as a dependency."""
    # Also check parent directory if run from inside core/
    if not os.path.exists(path):
        path = "../.env"
        if not os.path.exists(path):
            return
            
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip("'\"")
                if k not in os.environ:
                    os.environ[k] = v

def interpolate_env_vars(data):
    """Recursively resolves ${ENV_VAR} strings in the loaded YAML dict."""
    if isinstance(data, dict):
        return {k: interpolate_env_vars(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [interpolate_env_vars(item) for item in data]
    elif isinstance(data, str):
        # Find ${VAR} patterns and replace them with os.environ.get(VAR, "")
        def replacer(match):
            var_name = match.group(1)
            return os.environ.get(var_name, "")
        return re.sub(r"\$\{([^}]+)\}", replacer, data)
    return data

def load_config():
    """Loads config.yaml, parses it, and interpolates environment variables."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Load .env from project root (next to config.yaml), not from CWD
    project_env = os.path.join(base_dir, "..", ".env")
    load_dotenv(project_env)
    
    config_path = os.path.join(base_dir, "config.yaml")
    if not os.path.exists(config_path):
        print("Error: config.yaml not found.", file=sys.stderr)
        print("Please copy config.example.yaml to config.yaml and configure your settings.", file=sys.stderr)
        sys.exit(1)
        
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            raw_config = yaml.safe_load(f)
            
        config = interpolate_env_vars(raw_config)
        return config
    except Exception as e:
        print(f"Error parsing config.yaml: {e}", file=sys.stderr)
        sys.exit(1)
