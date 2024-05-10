import time

from googletrans import Translator

def translate(text, dest='en'):
    print(f"Translating {text} to {dest}")
    translator = Translator()
    translation = translator.translate(text, dest=dest)
    time.sleep(0.5)
    return translation.text