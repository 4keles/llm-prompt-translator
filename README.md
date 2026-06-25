# Prompt Translator

A deterministic terminal layer that translates Turkish or broken-English prompts into clean, context-complete English. It resolves domain terminology and dangling references without polluting the receiving agent's context.

## Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (recommended for dependency management)

## Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/llm-prompt-translator.git
   cd llm-prompt-translator
   ```

2. **Install dependencies:**
   Using `uv`:
   ```bash
   uv sync
   ```
   Or using `pip`:
   ```bash
   pip install -r agent-translator/requirements.txt
   ```

3. **Configuration:**
   ```bash
   cp agent-translator/config.example.yaml agent-translator/config.yaml
   ```
   *Note: Edit `config.yaml` or `.env` to include your provider API keys (Groq, Gemini, etc.).*

## Usage

Use the `pt` wrapper script to interact with the translator from your terminal.

**Basic Translation:**
```bash
./pt "video geçişi kötü, jump cut gibi, 0.3sn smooth geçiş istiyorum, kontrol et"
```

**With specific modes:**
```bash
./pt translate "veritabanı bağlantısı koptu, loglara bak"
```

**Inside other agentic tools (e.g., Claude Code):**
```bash
!translate "assetler nasıl sorun oluyor"
```

### Clarifying References

If the input has dangling references (e.g., "assetler" without specifying which ones), the tool might prompt you for clarification (in interactive environments) or mark them as `[[UNCLEAR: ...]]` when run in non-interactive pipelines. You can bypass this by supplying context directly:

```bash
./pt -c "v1 sprite assets" "assetlerde sorun var"
```
