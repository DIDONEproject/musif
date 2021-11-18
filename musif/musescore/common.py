from logging import getLogger

from ms3.score import MSCX

from musif.config import LOGGER_NAME


def extract_harmonic_analysis(mscx_file: str):
    logger = getLogger(LOGGER_NAME)
    logger.debug(f"Extracting harmonic analysis from musescore file '{mscx_file}'")
    harmonic_analysis = None
    try:
        musescore_score = MSCX(mscx_file, level='c')
        harmonic_analysis = musescore_score.expanded
    except Exception as e:
        logger.error(f"Error found while parsing the musescore file {mscx_file} {str(e)}")
    return harmonic_analysis

