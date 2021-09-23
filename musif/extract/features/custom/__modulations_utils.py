# ### MODULATIONS ###
from pandas.core.frame import DataFrame
import roman
from music21 import scale, pitch
# REVIEW
def get_modulations(lausanne_table: DataFrame, sections, major = True):
    keys = lausanne_table.localkey.dropna().tolist()
    modulations_sections = {g:[] for g in grouping}
    grouping, _ = get_keys_functions(keys, mode = 'M' if major else 'm')

    # Count the number of sections in each key
    last_key = ''
    for i, k in enumerate(keys):
        if (k.lower() != 'i') and k != last_key: #premisa
            # section = sections[i]
            last_key = k
            modulation = grouping[i]
            # modulations_sections[modulation].append(section)
        # if last_key == k and sections[i] != section:
        #     section = sections[i]
        #     modulations_sections[modulation].append(section)
    
    #borramos las modulaciones con listas vacías y dejamos un counter en vez de una lista
    ms = {}
    for m in modulations_sections:
        if len(modulations_sections[m]) != 0:
            ms['Modulations'+str(m)] = len(list(set(modulations_sections[m])))
    return ms

def get_keys_functions(keys: list, mode: str= 'm'):
    grouping=[]
    return grouping, None

def IsAnacrusis(harmonic_analysis):
    return harmonic_analysis.mn.dropna().tolist()[0] == 0
    
def get_tonality_for_measure(harmonic_analysis, tonality, renumbered_measures):
    tonality_map = {}
    for index, grado in enumerate(harmonic_analysis.localkey):
        tonality_map[renumbered_measures[index]] = get_localTonalty(tonality, grado.strip())
    return tonality_map


def get_localTonalty(globalkey, degree):
    accidental=''

    if '#' in degree:
        accidental = '#'
        degree = degree.replace('#', '')

    elif 'b' in degree:
        accidental = '-'
        degree = degree.replace('b', '')

    degree_int = roman.fromRoman(degree.upper())

    if globalkey.replace('b', '').isupper():
        pitch_scale = scale.MajorScale(globalkey.split()[0]).pitchFromDegree(degree_int).name 
    else:
        pitch_scale = scale.MinorScale(globalkey.split(' ')[0]).pitchFromDegree(degree_int).name 
    
    modulation = pitch_scale + accidental

    # modulation = modulation.replace('#', '', 1)
    # modulation = modulation.replace('-', '', 1)

    return modulation.upper() if degree.isupper() else modulation.lower()
###########################################################################
# Function created to obtain the scale degree of a note in a given key #
###########################################################################
def get_note_degree(key, note):
  if 'major' in key:
    scl = scale.MajorScale(key.split(' ')[0])
  else:
    scl = scale.MinorScale(key.split(' ')[0])

  degree = scl.getScaleDegreeAndAccidentalFromPitch(pitch.Pitch(note))
  accidental = degree[1].fullName if degree[1] != None else ''

  acc = ''
  if accidental == 'sharp':
    acc = '#'
  elif accidental == 'flat':
    acc = 'b'
  elif accidental == 'double-sharp':
    acc = 'x'
  elif accidental == 'double-flat':
    acc = 'bb'

  return acc + str(degree[0])
