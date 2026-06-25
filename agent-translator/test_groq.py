from core.config import load_config
from providers.groq import GroqProvider

config = load_config()
groq_config = next(p for p in config['providers'] if p['name'] == 'groq')
provider = GroqProvider(groq_config)

print(provider.complete("You are a helpful translator.", "Translate to English: video geçişi kötü, düzelt"))
