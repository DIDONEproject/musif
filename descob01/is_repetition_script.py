import glob
from os import path
from colorama import Fore

from musif.musicxml import MUSICXML_FILE_EXTENSION


def extract_xml_files(obj):
    if not (isinstance(obj, list) or isinstance(obj, str)):
        raise TypeError(f"Unexpected argument {obj} should be a directory, a file path or a list of files paths")
    if isinstance(obj, str):
        if path.isdir(obj):
            return sorted(glob.glob(path.join(obj, f"*.{MUSICXML_FILE_EXTENSION}")), key=str.lower)
        elif path.isfile(obj):
            return [obj] if obj.rstrip().endswith(f".{MUSICXML_FILE_EXTENSION}") else []
        else:
            raise ValueError(f"File {obj} doesn't exist")
    return sorted([mxml_file for obj_path in obj for mxml_file in extract_xml_files(obj_path)])


def is_repetition(path_name, direc, names):
    """
    copy files that has repetition brackets into specified directory and writes the names in given file.

    Parameters
    ---------
    path_name:
        A path or a list of paths
    direc:
        Saving directory
    names:
        File to save files with repetitions
    """
    paths = extract_xml_files(path_name)
    cont = 0
    resul = []
    for file in paths:
        try:
            f_read = open(file, encoding="utf8")
            list_lines = f_read.readlines()
        finally:
            f_read.close()
        cont += 1
        i = 0
        for line in list_lines:
            if any(word in line for word in ['dalsegno', 'segno', 'capo', 'dacapo', 'repeat', 'coda']):
                break
            i += 1
        if i != len(list_lines):
            resul.append('\n' + file)
            copy(file, direc)
            print(Fore.GREEN + file)
        else:
            print(Fore.RED + file)

    print(cont)
    if len(resul) > 0:
        try:
            save_name = open(names, 'w', encoding="utf-8")
            save_name.writelines(resul)
        finally:
            save_name.close()


def is_segno_beginning(path_name, names):
    """
    copy files that has segno in the first brankets and write the names in the given file.

    Parameters
    ---------
    path_name:
        A path or a list of paths
    names:
        File to save files with repetitions
    """
    paths = extract_xml_files(path_name)
    cont = 0
    resul = []
    for file in paths:
        try:
            f_read = open(file, encoding="utf8")
            list_lines = f_read.readlines()
        finally:
            f_read.close()
        cont += 1
        i = 0
        find = False
        for line in list_lines:
            if 'measure number="1"' in line:
                find = True
            elif 'segno' in line:
                break
            elif find and '</measure>' in line:
                find = False
                break
            i += 1
        if i != len(list_lines) and find:
            resul.append('\n' + file)
            print(Fore.GREEN + file)
        else:
            print(Fore.RED + file)

    print(cont)
    if len(resul) > 0:
        try:
            save_name = open(names, 'w', encoding="utf-8")
            save_name.writelines(resul)
        finally:
            save_name.close()