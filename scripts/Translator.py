import json
import pickle
from googletrans import Translator
# t = Translator()
# words = ["oboe", 'violin', 'trumpet', 'horn', 'basso', 'voice', 'bassoon', 'piccolo']

# languages = ['af','sq','am','ar','hy','az','eu','be','bn','bs','bg','ca','ceb','ny','zh-cn','zh-tw','co','hr','cs','da','nl','eo','et','tl','fi','fr','fy','gl','ka','de','el','gu','ht','ha','haw','iw','he','hi','hmn','hu','is','ig','id','ga','it','ja','jw','kn','kk','km','ko','ku','ky','lo','la','lv','lt','lb','mk','mg','ms','ml','mt','mi','mr','mn','my','ne','no','or','ps','fa','pl','pt','pa','ro','ru','sm','gd','sr','st','sn','sd','si','sk','sl','so','es','su','sw','sv','tg','ta','te','th','tr','uk','ur','ug','uz','vi','cy','xh','yi','yo','zu']
# dictionary={}
# for word in words:
#     translations=[]
#     for lang in languages:
#         translation = t.translate(word, src='en', dest=lang).text
#         translations.append(translation)
        
#     translations = list(set(translations))
#     dictionary[word] = translations

# with open('translations.pkl', 'wb') as f:
#     pickle.dump(dictionary, f)
    
with open('translations.pkl', 'rb') as f:
    loaded_dict = pickle.load(f)
    
with open("all_translations.json", "w", encoding='utf8') as outfile:
    json.dump(loaded_dict, outfile, sort_keys=True, ensure_ascii=False)
    
i=1
     