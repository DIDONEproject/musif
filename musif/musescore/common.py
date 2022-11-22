from ms3.score import MSCX

from musif.logs import ldebug, lerr


def extract_harmonic_analysis(mscx_file: str):
    """
    Given a mscx file name, parses the file using ms3 library and returns a dataframe containing all harmonic information.
    Adds Playthrough column that contains number of every measure in the cronological order
    Parameters
    ----------
    file_path: str
        Path to mscx file
    expand_repeats: bool
        Directory path to musescore file
    Returns
    -------
    harmonic_analysis: str
        Dataframe containing harmonic information

    """
    ldebug(f"Extracting harmonic analysis from musescore file '{mscx_file}'")
    harmonic_analysis = None
    try:
        musescore_score = MSCX(mscx_file, level="c")
        harmonic_analysis = musescore_score.expanded
    except Exception as e:
        lerr(f"Error found while parsing the musescore file {mscx_file} {str(e)}")
    return harmonic_analysis
