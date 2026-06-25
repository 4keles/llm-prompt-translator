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

4. **Global Installation (Linux/macOS):**
   To run `pt` from anywhere, create a symbolic link to your `/usr/local/bin` (or any directory in your `$PATH`):
   ```bash
   sudo ln -s $(pwd)/pt /usr/local/bin/pt
   ```
   Now you can use `pt "your prompt"` directly from any directory!

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

## Customizing Languages & Profiles

By default, the tool is optimized to translate **Turkish or broken-English** into **technical English**. However, you can easily adapt it to other languages (e.g., French, Russian, German) by modifying the prompt profiles.

**Using the Profile Manager:**
You can interactively manage and create new profiles:
```bash
./pt --manage-profiles
```

**Creating Multi-Language Profiles Manually:**
We provide an empty template for creating your own multi-language configurations.

1. Copy the template folder:
   ```bash
   cp -r agent-translator/prompts/profiles/_template_language agent-translator/prompts/profiles/fr-to-en
   ```
2. Open `system.md` inside your new profile and replace the `[SOURCE LANGUAGE]` and `[TARGET LANGUAGE]` placeholders (e.g., French -> English).
3. Open `rules.md` to add your own dictionary mappings for technical terms in that language.
4. Run the translator using your new profile:
   ```bash
   ./pt --profile fr-to-en "le problème de transition vidéo"
   ```

---

<p align="center">
  <i>Vibecoded & crafted by Gemini</i>
</p>
