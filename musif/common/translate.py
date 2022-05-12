from typing import Dict

import nltk
from googletrans import Translator

nltk.download('wordnet', quiet=True)
from nltk.corpus import wordnet as wn

# TODO: do we really need the whole nltk? it's a rather huge library...
# TODO: do we also need googletrans?

def translate_word(word: str, language: str = None, translations_cache: Dict[str, str] = None):
    t = Translator()
    translator_x_eng = ''
    # Remove instrument specifications (Re), (Do), ...
    parenthesis = word.find('(')
    word = word[:parenthesis] if '(' in word else word
    translations_cache = translations_cache or {}
    cached_translation = translations_cache.get(word.lower().strip())
    if cached_translation:
        return cached_translation
    for i in range(3):  # to support errors in the API call
        try:
            translator_x_eng = translations_cache.get(word.lower().strip(), t.translate(word, src='auto' if language == None else language))
            translator_x_eng_text = translator_x_eng.text
            break
        except:
            translator_x_eng_text = word
    # from the list of possible translations -> take nouns only
    main_possibility = translator_x_eng_text.replace('-', ' ').lower()
    # singularize(main_possibility)
    if len(wn.synsets(main_possibility)) > 0 and wn.synsets(main_possibility)[0].pos() != 'n':  # if not noun: look for a noun translation
        try:
            # if there is more than one possible translation:
            for translation in translator_x_eng.extra_data['all-translations']:
                type_word = translation[0]
                if type_word == 'noun':
                    main_possibility = translation[1][0].replace('-', ' ').lower()
        except:
            pass
    return main_possibility
