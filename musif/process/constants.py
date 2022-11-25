from musif.extract.basic_modules.file_name.constants import *
from musif.extract.basic_modules.metadata.constants import *
from musif.extract.basic_modules.scoring.constants import (
    INSTRUMENTATION,
    ROLE_TYPE,
    SCORING,
    VOICES,
)
from musif.extract.basic_modules.composer.constants import COMPOSER
from musif.extract.features.core.constants import FILE_NAME
from musif.extract.features.harmony.constants import HARMONY_AVAILABLE
from musif.extract.features.key.constants import KEY, KEY_SIGNATURE, KEY_SIGNATURE_TYPE
from musif.extract.features.prefix import get_part_prefix


'''Constant to create columns regarding presenc of an instrument or not.'''
PRESENCE='Presence_of'

'''Dictionary to assing label prefix to columns that need to bein the _labels.csv file to run analysis.'''
label_by_col = {
    "Basic_passion": "Label_BasicPassion",
    "PassionA": "Label_PassionA",
    "PassionB": "Label_PassionB",
    "Value": "Label_Value",
    "Value2": "Label_Value2",
    "Time": "Label_Time",
}

'''List of prefixes for singers used to find voices columns'''
voices_list = ['sop', 'ten', 'alt', 'bar', 'bbar', 'bass']

'''List of prefixes 'Part_' + each element of voices_list'''
voices_list_prefixes = [get_part_prefix(i) for i in voices_list]

'''Columns to be placed at the beginning of the exported DataFrame'''
priority_columns = [FILE_NAME, ARIA_OPERA, ARIA_LABEL, ARIA_NAME,
            ARIA_ACT, ARIA_SCENE, ACTANDSCENE, ARIA_YEAR, ARIA_DECADE, COMPOSER, ARIA_CITY, 
            TERRITORY, CHARACTER, GENDER, FORM, KEY, KEY_SIGNATURE, KEY_SIGNATURE_TYPE, INSTRUMENTATION, SCORING, VOICES
            ]

'''Columns that will be included in the _metadata.csv exported file'''
metadata_columns = [FILE_NAME, ARIA_OPERA, ARIA_LABEL, ARIA_NAME,
            ARIA_ACT, ARIA_SCENE, ACTANDSCENE, ARIA_YEAR, ARIA_DECADE, COMPOSER, ARIA_CITY, 
            TERRITORY, CHARACTER, GENDER, HARMONY_AVAILABLE
            ]
