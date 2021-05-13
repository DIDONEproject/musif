from musif.extract.features.tempo import TEMPO_GROUPED_1, TEMPO_GROUPED_2
from musif.extract.features.scoring import FAMILY_SCORING, SCORING
import openpyxl
import musif.extract.features.interval as interval
# The structure shows the grouping name as key, and as value a tuple containing its subgroupings and the sorting methods

ARIA_LABEL = 'AriaLabel'
OPERA = 'AriaOpera'
ARIA_ID = 'AriaId'
TITLE = 'AriaName'
COMPOSER = 'Composer'
DECADE = 'Decade'
ACT = 'Act'
SCENE = 'Scene'
ACTANDSCENE = 'ActAndScene'
NAME = 'FileName'
LIBRETTIST = 'Librettist'
FORM = 'Form'
CHARACTER = 'Character'
ROLE = 'RoleType'
GENDER ='Gender'
CITY = 'City'
TERRITORY = 'Territory'
CLEF1 = 'Clef1'
CLEF2 = 'Clef2'
CLEF3 = 'Clef3'
KEY = 'Key'
KEYSIGNATURE = 'KeySignature'
KEY_SIGNATURE_TYPE = 'KeySignatureType'
MODE = 'Mode'
TEMPO = 'Tempo'
TIMESIGNATURE = 'TimeSignature'
TIMESIGNATUREGROUPED = 'TimeSignatureGrouped'
DATE = 'Date'
YEAR = 'Year'
DECADE = "Decade"
CITY = "City"
metadata_columns = [OPERA, ARIA_LABEL, ARIA_ID, TITLE, COMPOSER, YEAR, DECADE, ACT, SCENE, ACTANDSCENE, NAME, LIBRETTIST, FORM, CHARACTER, GENDER, ROLE, CITY, TERRITORY, CLEF1, CLEF2, CLEF3, KEY, KEYSIGNATURE, KEY_SIGNATURE_TYPE, MODE, TEMPO, TIMESIGNATURE, TIMESIGNATUREGROUPED, TEMPO_GROUPED_1, TEMPO_GROUPED_2, SCORING, FAMILY_SCORING]
rows_groups = {OPERA: ([], "Alphabetic"),
               ARIA_LABEL: ([], "Alphabetic"),
               TITLE: ([], "Alphabetic"),
               COMPOSER: ([], "Alphabetic"),
               NAME: ([], "Alphabetic"),
               DATE: ([
                   YEAR,
                   DECADE,
               ], ["Alphabetic", "Alphabetic"]),
               "Geography": ([
                   CITY,
                   "Territory"
               ], ["Alphabetic", "Alphabetic"]),
               "Drama": ([
                   "Act",
                   "Scene",
                   ACTANDSCENE
               ], ["Alphabetic", "Alphabetic", "Alphabetic"]),
               CHARACTER: ([
                   CHARACTER,
                   ROLE,
                   GENDER
               ], ["CharacterSorting", "Alphabetic", "Alphabetic"]),
               "Form": ([], "FormSorting"),
               "Clef1": ([], "Alphabetic"),
               "Clef2": ([], "Alphabetic"),
               "Clef3": ([], "Alphabetic"),
               "Librettist": ([], "Alphabetic"),
               "Key": ([
                   "Key",
                   "Mode",
                   "KeySignature",
                   "KeySignatureType"], ["KeySorting", "Alphabetic", "Alphabetic", "KeySignatureSorting", "KeySignatureGroupedSorted"]),
               "Metre": ([
                   TIMESIGNATURE,
                   TIMESIGNATUREGROUPED
               ], ["TimeSignatureSorting", "Alphabetic"]),
               "Tempo": ([
                   "Tempo",
                   "TempoGrouped1",
                   "TempoGrouped2"
               ], ["TempoSorting", "TempoGroupedSorting1", "TempoGroupedSorting2"]),
               SCORING: ([
                   SCORING,
                   FAMILY_SCORING
               ], ["ScoringSorting", "ScoringFamilySorting"])
               }

not_used_cols = [ARIA_ID, SCORING, 'Total analysed', CLEF2, CLEF3]

alfa = "abcdefghijklmnopqrstuvwxyz"

# Some combinations are not needed when using more than one factor
forbiden_groups = {OPERA: [OPERA],
                   ARIA_LABEL: [OPERA, ARIA_LABEL],
                   TITLE: [TITLE, OPERA],
                   "Composer": ['Composer'],
                   YEAR: [YEAR, DECADE],
                   DECADE: [DECADE],
                   CITY: [CITY, TERRITORY],
                   TERRITORY: [TERRITORY],
                   ACT: [ACT, ACTANDSCENE],
                   SCENE: [SCENE, ACTANDSCENE],
                   ACTANDSCENE: [ACT, SCENE, ACTANDSCENE],
                   ROLE: [ROLE, GENDER],
                #    'RoleType': ["RoleType", "Gender"],
                   GENDER: [GENDER],
                   FORM: [FORM],
                   CLEF1: [CLEF1],
                   CLEF2: [CLEF2],
                   CLEF3: [CLEF3],
                   KEY: ['Form', 'Mode', 'Final', 'KeySignature', KEY_SIGNATURE_TYPE],
                   MODE: ['Mode', 'Final'],
                   'Final': ['Final', 'Key', 'KeySignature'],
                   KEYSIGNATURE: ['Key', 'Final', 'KeySignature', KEY_SIGNATURE_TYPE],
                   KEY_SIGNATURE_TYPE: [KEY_SIGNATURE_TYPE],
                   TIMESIGNATURE: [TIMESIGNATURE, TIMESIGNATUREGROUPED],
                   TIMESIGNATUREGROUPED: [TIMESIGNATUREGROUPED],
                   TEMPO: [TEMPO, "TempoGrouped1", "TempoGrouped2"],
                   'TempoGrouped1': ['TempoGrouped1', "TempoGrouped2"],
                   'TempoGrouped2': ['TempoGrouped2'],
                   "AbrScoring": ["AbrScoring", "RealScoringGrouped"],
                   "RealScoringGrouped": ["RealScoringGrouped"]
                   }

intervals_list = [interval.REPEATED_NOTES, interval.LEAPS_ASCENDING, interval.LEAPS_DESCENDING, interval.LEAPS_ALL, interval.STEPWISE_MOTION_ALL, interval.STEPWISE_MOTION_ASCENDING, interval.STEPWISE_MOTION_DESCENDING, interval.INTERVALS_PERFECT_ASCENDING, interval.INTERVALS_PERFECT_DESCENDING, interval.INTERVALS_PERFECT_ALL, interval.INTERVALS_MAJOR_ALL,
                  interval.INTERVALS_MAJOR_ASCENDING, interval.INTERVALS_MAJOR_DESCENDING, interval.INTERVALS_MINOR_ALL, interval.INTERVALS_MINOR_ASCENDING, interval.INTERVALS_MINOR_DESCENDING, interval.INTERVALS_AUGMENTED_ALL, interval.INTERVALS_AUGMENTED_ASCENDING, interval.INTERVALS_AUGMENTED_DESCENDING, interval.INTERVALS_DIMINISHED_ALL, interval.INTERVALS_DIMINISHED_ASCENDING, interval.INTERVALS_DIMINISHED_DESCENDING]

yellowFill = openpyxl.styles.PatternFill(
    start_color='F9E220', end_color='F9E220', fill_type='solid')
greenFill = openpyxl.styles.PatternFill(
    start_color='98E891', end_color='98E891', fill_type='solid')
orangeFill = openpyxl.styles.PatternFill(
    start_color='EE6513', end_color='EE6513', fill_type='solid')
titles1Fill = openpyxl.styles.PatternFill(
    start_color='F97626', end_color='F97626', fill_type='solid')
titles2Fill = openpyxl.styles.PatternFill(
    start_color='FA9455', end_color='FA9455', fill_type='solid')
titles3Fill = openpyxl.styles.PatternFill(
    start_color='FBBA93', end_color='FBBA93', fill_type='solid')
factors_Fill = [openpyxl.styles.PatternFill(start_color='06CAFF', end_color='06CAFF', fill_type='solid'),
                openpyxl.styles.PatternFill(
                    start_color='18ADD5', end_color='18ADD5', fill_type='solid'),
                openpyxl.styles.PatternFill(
                    start_color='1B94B4', end_color='1B94B4', fill_type='solid'),
                openpyxl.styles.PatternFill(start_color='11718A', end_color='11718A', fill_type='solid')]

bold = openpyxl.styles.Font(bold=True)
center = openpyxl.styles.Alignment(horizontal='center')
