MUSIC21_FILE_EXTENSIONS = [".xml", ".mxl", ".musicxml", ".mid", ".mei"]
"""Extensions used by music21. Defaults to `[".xml", ".mxl", ".musicxml", ".mid", ".mei"]`"""

DATA_PART = "part"
DATA_PART_NUMBER = "part_number"
DATA_PART_ABBREVIATION = "abbreviation"
DATA_SOUND = "sound"
DATA_SOUND_ABBREVIATION = "sound_abbreviation"
DATA_FAMILY = "family"
DATA_FAMILY_ABBREVIATION = "family_abbreviation"
DATA_SCORE = "score"
DATA_MUSESCORE_SCORE = "MS3_score"
DATA_FILE = "file"
DATA_FILTERED_PARTS = "parts"
DATA_NUMERIC_TEMPO = "numeric_tempo"

HARMONY_FEATURES = "harmony"
SCALE_RELATIVE_FEATURES = "scale_relative"
REQUIRE_MSCORE = [HARMONY_FEATURES, SCALE_RELATIVE_FEATURES]

"""Names of modules taht require harmonic analysis in a .mscx file"""

VOICES_LIST = ["sop", "ten", "alt", "bar", "bbar", "bass"]
"""List of prefixes of singers's names that might appear in the scores"""

PLAYTHROUGH = "playthrough"
"""Constant for playthrough (count fo measures) added to ms3 dataframe"""

GLOBAL_TIME_SIGNATURE = "global_ts"
"""The name used for the column indicating the global time signature"""

WINDOW_RANGE = "WindowRange"
"""The name used for the column indicating the start and end of a window"""

WINDOW_ID = "WindowId"
"""The name used for the column of the window's id"""

ID = "Id"
"""The name used for the column of the music score's id"""
