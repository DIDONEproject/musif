from music21.stream import Measure, Score
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


def calculate_textures(len_partvoices, names_list, amount_notes_list):
    textures_list = []
    try:
        for f in range(0, len_partvoices):
            texture = [round(amount_notes_list[f]/amount_notes_list[i], 3)
                        for i in range(f, len(amount_notes_list)) if f != i]
            textures_list.append(
                [{f'{names_list[f]}/{names_list[i+f+1]}': texture[i]} for i in range(0, len(texture))])
            textures_dict = dict((key, d[key]) for d in [i for d in textures_list for i in d] for key in d)
            # textures_sorting = general_sorting.get_texture_sorting()
            textures_dict = sort_dict(textures_dict, textures_sorting)
    except:
        logger.error('Densities problem found: ', exc_info=True)
        return {}

    return textures_dict


def get_textures(score: Score) -> dict:
    pass