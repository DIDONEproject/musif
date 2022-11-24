"""Constants used as keys in dictionaris score_features and score data throughout the extraction process."""
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

"""Names of modules taht require harmonic analysis in a .mscx file"""
HARMONY_FEATURES = "harmony"
SCALE_RELATIVE_FEATURES = "scale_relative"
REQUIRE_MSCORE = [HARMONY_FEATURES, SCALE_RELATIVE_FEATURES]

"""List of prefixes of singers's names that might appear in the scores"""
VOICES_LIST = ["sop", "ten", "alt", "bar", "bbar", "bass"]

"""Constant for playthrough (count fo measures) added to ms3 dataframe"""
PLAYTHROUGH = "playthrough"


GLOBAL_TIME_SIGNATURE = "global_ts"
WINDOW_RANGE = "WindowRange"
THEME_A_METADATA = "theme_a_per_aria.csv"
END_OF_THEME_A = "EndOfThemeA"

WINDOW_ID = "WindowId"
