from enum import Enum


class Features(Enum):
    MELODIC = "melodic"
    HARMONIC = "harmonic"
    TEXTURE = "texture"
    OPERATIC = "operatic"
    ROLE = "role"


MF = Features.MELODIC
HF = Features.HARMONIC
TF = Features.TEXTURE
OF = Features.OPERATIC
