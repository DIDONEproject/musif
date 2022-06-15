from typing import Dict
import requests
from bs4 import BeautifulSoup

from musif.common.translate import translate_word
from musif.common.utils import write_object_to_json_file


def create_instrument_abbreviations_file(file_path: str) -> Dict[str,str]:
    """
    Function to generate a JSON file indicating the relationshipe between
    all the instruments present in the score and their abbreviations.
    New Grove abbreviations
    
    Examples
    
    {"violoncello": "vc",
    "violino": "vn"}
    """
    instrumentName_abbreviation = {}

    url = 'https://imslp.org/wiki/IMSLP:Abbreviations_for_Instruments'
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    table = soup.find("table").get_text()
    table_rows = table.split('\n\n\n')
    # Parse text
    for row in table_rows[1:]:
        row_tokens = row.split('\n\n')
        abbrev = row_tokens[0].strip()

        for i in [1, 4]:  # ABBREVIATION ENGLISH [FRENCH GERMAN] ITALIAN [SPANISH]
            for word in row_tokens[i].split('('):
                word = word.replace(')', '')
                instrument = translate_word(word.strip(), 'Italian') if i != 1 else word.strip()
                instrumentName_abbreviation[instrument.lower()] = abbrev

    # Stores it in a json for future uses
    write_object_to_json_file(instrumentName_abbreviation, file_path)
    return instrumentName_abbreviation


def create_instrument_families_file(file_path: str) -> Dict[str,str]:
    """
    Function to generate a JSON file indicating the relationships between
    all the instruments present in the score (IN ENGLISH) and their families,
    i.e. str (strings), ww (woodwinds), etc.
    
    Example
    {"woodwind instruments": "ww"}
    
    """
    instrumentName_family = {}

    url = 'https://opac.rism.info/index.php?id=15'
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    content = soup.find('div', {'id': 'c32'})  # where the headers and tables are found
    headers_tables = content.findAll(['h1', 'tbody'])

    for element in headers_tables:
        if element.name == 'h1':
            header = element.getText().strip().lower()
            instr_family = header if header != 'vocal (voice) terms' else 'voice'
            instr_family = instr_family.replace('and other', '').replace('instruments', '').strip()
        else:  # parse table
            for row in element.findAll('tr'):
                try:
                    inst = row.findAll('p')[-1].getText()
                    if not inst.strip():
                        inst = row.findAll('p')[-2].getText()
                except:
                    inst = row.findAll('td')[-1].getText()
                inst = inst.split(';')[0]
                for i in inst.split(','):
                    index_parenthesis = i.find('(')
                    i = i[:index_parenthesis].strip() if index_parenthesis != -1 else i.strip()
                    instrumentName_family[i.replace('-', ' ').lower()] = instr_family

    write_object_to_json_file(instrumentName_family, file_path)
    return instrumentName_family
