from music21 import musicxml
from music21.converter import Converter

from musif.extract.extract import extract_files, parse_musicxml_file


def change_date_xml(person, old_date, new_date, path_name, dest):
    """
    Changes person's date(year of birth or death) from old_date to new_date and saves it in de file dest.
    """
    files = extract_files(path_name)
    for name in files:
        score = parse_musicxml_file(name, [])
        for note in score.notes.activeElementList:
            if person in note.content:
                i = note.content.find(person)
                j = note.content[i:].find(')') + i
                note.content = note.content[:i] + note.content[i:j].replace(old_date, new_date) + note.content[j:]
                break
        score.write(fp=dest)
