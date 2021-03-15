
from ms3.score import MSCX

from config import read_logger


def extract_harmonic_analysis(mscx_file: str):
    read_logger.debug(f"Extracting harmonic analysis from musescore file '{mscx_file}'")
    harmonic_analysis = None
    try:
        musescore_score = MSCX(mscx_file, level='c')
        harmonic_analysis = musescore_score.expanded
    except Exception as e:
        read_logger.error(f"Error found while parsing the musescore file {mscx_file} {str(e)}")
    return harmonic_analysis

