import openpyxl
# The structure shows the grouping name as key, and as value a tuple containing its subgroupings and the sorting methods
metadata_columns = ['FileName', 'AriaOpera', 'AriaLabel', 'AriaId', 'AriaTitle', 'Composer', 'Year', 'Decade', 'Act', 'Scene', 'ActAndScene', 'AriaName', 'Librettist', 'Form',
                    'Character', 'Role', 'City', 'Territory', 'Opera', 'Clef1', 'Clef2', 'Clef3', 'Key', 'KeySignature', 'KeySignatureGrouped', 'Mode', 'Tempo', 'TimeSignature', 'TimeSignatureGrouped']

rows_groups = {"Opera": ([], "Alphabetic"),
               "AriaLabel": ([], "Alphabetic"),
               "AriaTitle": ([], "Alphabetic"),
               "Composer": ([], "Alphabetic"),
               "Date": ([
                   "Year",
                   "Decade"
               ], ["Alphabetic", "Alphabetic"]),
               "Geography": ([
                   "City",
                   "Territory"
               ], ["Alphabetic", "Alphabetic"]),
               "Drama": ([
                   "Act",
                   "Scene",
                   "Act&Scene"
               ], ["Alphabetic", "Alphabetic", "Alphabetic"]),
               "Character": ([
                   "Character",
                   "Role",
                   "RoleType"
                   "Gender"
               ], ["CharacterSorting", "Alphabetic", "Alphabetic", "Alphabetic"]),
               "Form": ([], "FormSorting"),
               "Clef": ([], "Alphabetic"),
               "Key": ([
                   "Key",
                   "Mode",
                   "KeySignature",
                   "KeySignatureGrouped"], ["KeySorting", "Alphabetic", "Alphabetic", "KeySignatureSorting", "KeySignatureGroupedSorted"]),
               "Metre": ([
                   "TimeSignature",
                   "TimeSignatureGrouped"
               ], ["TimeSignatureSorting", "Alphabetic"]),
               "Tempo": ([
                   "Tempo",
                   "TempoGrouped1",
                   "TempoGrouped2"
               ], ["TempoSorting", "TempoGroupedSorting1", "TempoGroupedSorting2"]),
               "Scoring": ([
                   "AbrScoring",
                   "RealScoringGrouped"
               ], ["ScoringSorting", "ScoringFamilySorting"])
               }
not_used_cols = ['AriaId', 'RealScoring', 'Total analysed', 'OldClef']


# Some combinations are not needed when using more than one factor
forbiden_groups = {"Opera": ['Opera'],
                   "AriaLabel": ['Opera', 'Label'],
                   "AriaTitle": ['Aria', 'Opera'],
                   "Composer": ['Composer'],
                   "Year": ['Year', 'Decade'],
                   "Decade": ['Decade'],
                   "City": ['City', 'Territory'],
                   "Territory": ['Territory'],
                   "Act": ["Act", 'Act&Scene'],
                   "Scene": ["Scene", "Act&Scene"],
                   "Act&Scene": ["Act", 'Scene', 'Act&Scene'],
                   'Role': ["Role", "RoleType", "Gender"],
                   'RoleType': ["RoleType", "Gender"],
                   'Gender': ["Gender"],
                   'Form': ['Form'],
                   "Clef1": ['Clef1'],
                   "Clef2": ['Clef2'],
                   "Clef3": ['Clef3'],
                   'Key': ['Form', 'Mode', 'Final', 'KeySignature', 'KeySignatureGrouped'],
                   'Mode': ['Mode', 'Final'],
                   'Final': ['Final', 'Key', 'KeySignature'],
                   'KeySignature': ['Key', 'Final', 'KeySignature', 'KeySignatureGrouped'],
                   'KeySignatureGrouped': ['KeySignatureGrouped'],
                   'TimeSignature': ['TimeSignature', 'TimeSignatureGrouped'],
                   "TimeSignatureGrouped": ['TimeSignatureGrouped'],
                   'Tempo': ['Tempo', "TempoGrouped1", "TempoGrouped2"],
                   'TempoGrouped1': ['TempoGrouped1', "TempoGrouped2"],
                   'TempoGrouped2': ['TempoGrouped2'],
                   "AbrScoring": ["AbrScoring", "RealScoringGrouped"],
                   "RealScoringGrouped": ["RealScoringGrouped"]
                   }

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
