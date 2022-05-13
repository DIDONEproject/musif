from ms3.score import MSCX

from musif.logs import ldebug, lerr


# TODO: document this function
def extract_harmonic_analysis(mscx_file: str):
    ldebug(f"Extracting harmonic analysis from musescore file '{mscx_file}'")
    harmonic_analysis = None
    try:
        musescore_score = MSCX(mscx_file, level='c')
        harmonic_analysis = musescore_score.expanded
    except Exception as e:
        lerr(f"Error found while parsing the musescore file {mscx_file} {str(e)}")
    return harmonic_analysis

