
from descob01.change_birth_date import change_date_xml
from musif.extract.extract import parse_musicxml_file


if __name__ == "__main__":
    # change_date_xml("Pietro Metastasio", "1689", "1698", "../arias/xml/Dem01M-O_piu-1735-Leo[1.01][0430].xml")
    score1 = parse_musicxml_file("../arias/xml/Dem01M-O_piu-1735-Leo[1.01][0430].xml", [])
    score2 = parse_musicxml_file("resul.xml", [])
    print(score1.notes.activeElementList[3].content)
    print(score2.notes.activeElementList[3].content)
