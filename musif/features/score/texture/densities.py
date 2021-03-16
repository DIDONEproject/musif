from music21.stream import Measure, Score, Part
from ....common.sort import sort_dict 


def get_note_list(partVoice):
    elem = partVoice.elements
    len_notes = []
    for n in elem:
        if isinstance(n, stream.Measure):
            for x in n.elements:
                set_ties(x, len_notes)
    return len_notes

def get_notes_measures(partVoice):
    len_notes = get_note_list(partVoice)
    if set_total_measures:
        total_measures = len(partVoice.getElementsByClass('Measure'))
    else:
        # we get the list of measures that contain at least one note, which means they are not full silences.
        total_measures = len([i for i in partVoice.getElementsByClass('Measure') if (
            [f for f in i.elements if isinstance(f, note.Note)] != [])])
    return len(len_notes), total_measures


def calculate_densities(notes_list, measures_list, names_list):
    density_list = []
    try:
        for i, part in enumerate(names_list):
            density = round(notes_list[i]/measures_list[i], 3)
            density_list.append({f'{names_list[i]}': density})

        density_dict = dict((key, d[key]) for d in density_list for key in d)
        # density_sorting = general_sorting.get_instruments_sorting()
        density_dict = sort_dict(density_dict, density_sorting)
        return density_dict
    except:
        logger.error('Densities problem found: ', exc_info=True)
        return {}

def get_densities(score: Score, parts: Part, repetition_elements, scoring) -> dict:
    amount_notes_list = []
    amount_measures = []
    names_list = []
    # num_voices = len([i for i in partVoices if i.partName.startswith('voice')])

    for i, partVoice in enumerate(parts):
        partVoice_expanded = remove_repeats.expand_part(
            partVoice, repeat_elements)
        # Calculate total notes and measures
        len_notes, measures = get_notes_measures(partVoice_expanded)

        names_list.append(partVoice_expanded.partName)
        amount_notes_list.append(len_notes)
        amount_measures.append(measures)

    # Once collected all info for all parts, we iterate to calculate densities and textures
    df = pd.DataFrame(list(zip(names_list, amount_notes_list,
                               amount_measures)), columns=['names', 'notes', 'measures'])

    try:
        for i, _ in enumerate(partVoices):
            # Criteria: split anything that might have two voices in the same part and is not a violin or a voice
            if (df.names[i].replace('I','') not in ['vn', 'voice'] and df['names'][i].endswith('I')):
                df['notes'][i] = df['notes'][i]+df['notes'][i+1]
                df['measures'][i] = df['measures'][i]+df['measures'][i+1]
                df['names'][i] = df.names[i].replace('I', '')
                df = df.drop([i+1], axis=0)
                df.reset_index(drop=True, inplace=True)
                del partVoices[i+1]
                continue
            if (df.names[i].startswith('voice') and num_voices > 1):
                df['notes'][i] = sum(df['notes'][i:i+num_voices])
                df['measures'][i] = sum(df['measures'][i:i+num_voices])
                df = df.drop([i+1], axis=0)
                df.reset_index(drop=True, inplace=True)
                del partVoices[i+1]
                continue
    except IndexError:
        print('Problem with the instrument numeration')
    
    return calculate_densities((notes_list, measures_list, names_list))