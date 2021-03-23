from enum import Enum


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
