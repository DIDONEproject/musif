from enum import Enum


class Level(Enum):
    CORPUS = "corpus"
    SCORE = "score"
    FAMILY = "family"
    SOUND = "sound"
    PART = "part"


class Features(Enum):
    COMMON = "common"
    MELODIC = "melodic"
    HARMONIC = "harmonic"
    TEXTURE = "texture"
    OPERATIC = "operatic"
    ROLE = "role"


CM = Features.COMMON
MF = Features.MELODIC
HF = Features.HARMONIC
TF = Features.TEXTURE
OF = Features.OPERATIC
