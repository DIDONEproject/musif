import glob
from os import path
from musif.musicxml import MUSESCORE_FILE_EXTENSION, MUSICXML_FILE_EXTENSION
from PyPDF2 import PdfFileWriter, PdfFileReader


def extract_musecore_files(obj):
    if not (isinstance(obj, list) or isinstance(obj, str)):
        raise TypeError(f"Unexpected argument {obj} should be a directory, a file path or a list of files paths")
    if isinstance(obj, str):
        if path.isdir(obj):
            return sorted(glob.glob(path.join(obj, f"*.{MUSESCORE_FILE_EXTENSION}")), key=str.lower)
        elif path.isfile(obj):
            return [obj] if obj.rstrip().endswith(f".{MUSESCORE_FILE_EXTENSION}") else []
        else:
            raise ValueError(f"File {obj} doesn't exist")
    return sorted([musecore_file for obj_path in obj for musecore_file in extract_musecore_files(obj_path)])


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


def change_year_xml(person, old_date, new_date, origin_paths):
    """
    Changes person's date(year of birth or death) from old_date to new_date and saves it in the original file.

    Parameters
    ----------
    person : str
      Name of person wich year of death or birt want to be changed
    old_date : str
      Year that will be changed
    new_date : str
      New year that will replace the old one
    origin_paths : Union[str, List[str]]
      A path or a list of paths
    """
    files = extract_xml_files(origin_paths)
    cont = 0
    for name in files:
        print(name)
        f = open(name, encoding="utf8")
        list_lines = f.readlines()
        cont += 1
        i = 0
        for line in list_lines:
            if person + " (" in line and old_date in line:
                break
            i += 1
        if i != len(list_lines):
            name_position = list_lines[i].find(person + " (")
            end_dates = list_lines[i][name_position:].find(')') + name_position
            list_lines[i] = list_lines[i][:name_position] + list_lines[i][name_position:end_dates].replace(old_date, new_date) + list_lines[i][end_dates:]
            f = open(name, "w", encoding="utf8")
            f.writelines(list_lines)
        f.close()
    print(cont)


def change_year_musecore(person, old_date, new_date, origin_paths):
    """
    Changes person's date(year of birth or death) from old_date to new_date and saves it in the original file.

    Parameters
    ----------
    person : str
      Name of person wich year of death or birt want to be changed
    old_date : str
      Year that will be changed
    new_date : str
      New year that will replace the old one
    origin_paths : Union[str, List[str]]
      A path or a list of paths
    """
    files = extract_musecore_files(origin_paths)
    cont = 0
    for name in files:
        print(name)
        f = open(name, encoding="utf8")
        list_lines = f.readlines()
        cont += 1
        i = 0
        for line in list_lines:
            if person + " (" in line and old_date in line:
                break
            i += 1

        if i != len(list_lines):
            name_position = list_lines[i].find(person + " (")
            end_dates = list_lines[i][name_position:].find(')') + name_position
            list_lines[i] = list_lines[i][:name_position] + list_lines[i][name_position:end_dates].replace(old_date, new_date) + list_lines[i][end_dates:]
            f = open(name, "w", encoding="utf8")
            f.writelines(list_lines)
        f.close()
    print(cont)
