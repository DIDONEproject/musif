import os
from os import path
from shutil import copyfile

source_path_xml=r"../../../_Ana/Music Analysis/xml/corpus_github/xml/"
source_path_mscx=r"../../../_Ana/Music Analysis/xml/corpus_github/musescore/"

target_path=r"../../Corpus/corpus_filtrado/"
target_path2=r"../../Corpus\corpus_filtrado(15-09)/"


for dirpath, subdirs, files in os.walk(source_path_mscx):
    for x in files:
        if x.endswith(".mscx"):
            print(path.join(target_path, x.replace(".xml", ".mscx")))
            if not path.exists(path.join(target_path, x.replace(".xml", ".mscx"))):
                try:
                    if path.exists(source_path_xml + x.replace(".mscx", ".xml")) and path.exists(source_path_mscx + x):
                        copyfile(source_path_xml + x.replace(".mscx", ".xml"), target_path2+ x.replace(".mscx", ".xml"))
                        copyfile(source_path_mscx + x,target_path2+ x)
                        print("copied ", x)
                    else:
                        with open('not_found.txt', 'a') as f:
                            f.write(x + '\n')
                        raise Exception('file not found! ', x)
                except Exception as e:
                    print(e)
