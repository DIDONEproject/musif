from typing import Dict

from googletrans import Translator

# import nltk
# nltk.download('wordnet', quiet=True)
# from nltk.corpus import wordnet as wn

# TODO: do we also need googletrans?

def translate_word(word: str, language: str = None, translations_cache: Dict[str, str] = None):
    t = Translator()
    translator_x_eng = ''
    parenthesis = word.find('(') # Remove instrument specifications (Re), (Do), ...
    word = word[:parenthesis] if '(' in word else word
    translations_cache = translations_cache or {}
    cached_translation = translations_cache.get(word.lower().strip())
    if cached_translation:
        return cached_translation
    for _ in range(3):  # to support errors in the API call
        try:
            translator_x_eng = translations_cache.get(word.lower().strip(), t.translate(word, src='auto' if language == None else language))
            translator_x_eng_text = translator_x_eng.text
            break
        except:
            translator_x_eng_text = word
            
    main_possibility = translator_x_eng_text.replace('-', ' ').lower()
    if translator_x_eng.extra_data['all-translations']:
        return translator_x_eng.extra_data['all-translations'][0] if translator_x_eng.extra_data['all-translations'][0][0] == 'noun' else translator_x_eng.extra_data['all-translations'[0]][1][0].replace('-', ' ').lower()
    
    return main_possibility
