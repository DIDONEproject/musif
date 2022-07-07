
from musif.extract.features.composer.constants import COMPOSER
from musif.extract.features.core.constants import FILE_NAME
from musif.extract.features.metadata.constants import *
from musif.extract.features.file_name.constants import *
from musif.extract.features.key.constants import KEY, KEY_SIGNATURE, KEY_SIGNATURE_TYPE
from musif.extract.features.prefix import get_part_prefix
from musif.extract.features.scoring.constants import VOICES, INSTRUMENTATION, SCORING

from musif.extract.constants import VOICES_LIST

# TODO: document these constants

PRESENCE='Presence_of'

label_by_col = {
        "Basic_passion": "Label_BasicPassion",
        "PassionA": "Label_PassionA",
        "PassionB": "Label_PassionB",
        "Value": "Label_Value",
        "Value2": "Label_Value2",
        "Time": "Label_Time",
    }

voices_list_prefixes = [get_part_prefix(i) for i in VOICES_LIST]

priority_columns = [FILE_NAME, ARIA_OPERA, ARIA_LABEL, ARIA_NAME,
            ARIA_ACT, ARIA_SCENE, ACTANDSCENE, ARIA_YEAR, ARIA_DECADE, COMPOSER, ARIA_CITY, 
            TERRITORY, CHARACTER, GENDER, FORM, KEY, KEY_SIGNATURE, KEY_SIGNATURE_TYPE, INSTRUMENTATION, SCORING, VOICES
            ]

metadata_columns = [FILE_NAME, ARIA_OPERA, ARIA_LABEL, ARIA_NAME,
            ARIA_ACT, ARIA_SCENE, ACTANDSCENE, ARIA_YEAR, ARIA_DECADE, COMPOSER, ARIA_CITY, 
            TERRITORY, CHARACTER, GENDER
            ]
