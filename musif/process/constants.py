
from musif.extract.features.composer.constants import COMPOSER
from musif.extract.features.core.constants import FILE_NAME
from musif.extract.features.file_name.constants import ARIA_NAME, ARIA_OPERA
from musif.extract.features.key.constants import KEY, KEY_SIGNATURE, KEY_SIGNATURE_TYPE
from musif.extract.features.scoring.constants import VOICES
from musif.reports.constants import ACT, ACTANDSCENE, CHARACTER, CITY, DECADE, FORM, GENDER, ROLE_TYPE, SCENE, TERRITORY, YEAR
from musif.reports.constants import ARIA_ID, ARIA_LABEL

from musif.extract.features.scoring.constants import INSTRUMENTATION, ROLE_TYPE, SCORING, VOICES

PRESENCE='Presence_of'

label_by_col = {
        "Basic_passion": "Label_BasicPassion",
        "PassionA": "Label_PassionA",
        "PassionB": "Label_PassionB",
        "Value": "Label_Value",
        "Value2": "Label_Value2",
        "Time": "Label_Time",
    }

voices_list = ['sop','ten','alt','bar','bbar', 'bass']
voices_list_prefixes = ['Part' + i.capitalize() for i in voices_list]

columns_order= [ARIA_ID, FILE_NAME, ARIA_OPERA, ARIA_LABEL, ARIA_NAME, ACT, SCENE, ACTANDSCENE, YEAR, DECADE, COMPOSER, CITY, TERRITORY, CHARACTER, ROLE_TYPE, GENDER, FORM, KEY, KEY_SIGNATURE, KEY_SIGNATURE_TYPE, INSTRUMENTATION, SCORING, TYPE, VOICES]
