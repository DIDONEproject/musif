from music21.features import jSymbolic, native
from music21.features.base import extractorsById

all_columns = [x.id for x in extractorsById("all")]
ERRORED_NAMES = {
    "T1",
    "T2",
    "T3",
    "CS1",
    "CS2",
    "CS3",
    "CS4",
    "CS5",
    "CS6",
    "CS7",
    "CS8",
    "CS9",
    "CS10",
    "CS11",
}
COLUMNS = [c for c in all_columns if c not in ERRORED_NAMES]

# COLUMNS = [x.id for x in extractorsById("native")]
