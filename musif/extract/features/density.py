from copy import deepcopy
from typing import List

from musif.common.sort import sort_dict
from musif.config import Configuration
from pandas import DataFrame

from musif.musicxml import Measure, Note, Part


set_total_measures = False  # TODO: WTH!?!?


def get_single_part_features(notes: List[Note], measures: List[Measure]) -> dict:
    features = {
        "Notes": len(notes),
        "Measures": len(measures),
        "Density": len(notes) / len(measures),
    }
    return features


def get_aggregated_parts_features(parts_features: List[dict]) -> List[dict]:
    parts_features = deepcopy(parts_features)

    df = DataFrame(parts_features)
    df_sound = df.groupby("Sound").aggregate({"Notes": "sum", "Measures": "sum"})
    df_family = df.groupby("Family").aggregate({"Notes": "sum", "Measures": "sum"})

    for features in parts_features:
        sound = features["Sound"]
        features["SoundNotes"] = df_sound.loc[sound, 'Notes']
        features["SoundMeasures"] = df_sound.loc[sound, 'Measures']
        features["SoundDensity"] = features["SoundNotes"] / features["SoundMeasures"]
        family = features["Family"]
        features["FamilyNotes"] = df_family.loc[family, 'Notes']
        features["FamilyMeasures"] = df_family.loc[family, 'Measures']
        features["FamilyDensity"] = features["SoundNotes"] / features["SoundMeasures"]

    return parts_features


def get_global_features(parts: List[Part], parts_features: List[dict], cfg: Configuration) -> dict:

    sound_features = {}
    family_features = {}
    global_features = []

    df = DataFrame(parts_features)
    df_sound = df.groupby("Sound").aggregate({"Notes": "sum", "Measures": "sum"})
    df_family = df.groupby("Family").aggregate({"Notes": "sum", "Measures": "sum"})
    df_all = df.aggregate({"Notes": "sum", "Measures": "sum"})
    for features in parts_features:
        sound = features["Sound"]
        features["SoundNotes"] = df_sound.loc[sound, 'Notes']
        features["SoundMeasures"] = df_sound.loc[sound, 'Measures']
        features["SoundDensity"] = features["SoundNotes"] / features["SoundMeasures"]
        family = features["Family"]
        features["FamilyNotes"] = df_family.loc[family, 'Notes']
        features["FamilyMeasures"] = df_family.loc[family, 'Measures']
        features["FamilyDensity"] = features["SoundNotes"] / features["SoundMeasures"]

    sound_density_features = {}
    for sound, features_list in sound_features.items():
        sound_features[sound] = {
            "Notes": sum([f["Notes"] for f in features_list]),
            "Measures": sum([f["Measures"] for f in features_list]),
        }

    return {}


def set_ties(subjct, len_notes):
    if isinstance(subjct, Note):
        if (subjct.tie is not None) and (subjct.tie.type == "stop" or subjct.tie.type == "continue"):
            if isinstance(len_notes[-1], Note):
                # sum tied notes' length
                len_notes[-1].duration.quarterLength += subjct.duration.quarterLength
            else:
                back_counter = -1
                while isinstance(len_notes[back_counter], tuple):
                    back_counter -= - 1
                else:
                    # sum tied notes' length across measures
                    len_notes[back_counter].duration.quarterLength += subjct.duration.quarterLength
        else:
            len_notes.append(subjct)

def get_note_list(partVoice):
    elem = partVoice.elements
    len_notes = []
    for n in elem:
        if isinstance(n, Measure):
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
            [f for f in i.elements if isinstance(f, Note)] != [])])
    return len(len_notes), total_measures


def calculate_densities(notes_list, measures_list, names_list, cfg: Configuration):
    density_list = []
    try:
        for i, part in enumerate(names_list):
            density = round(notes_list[i]/measures_list[i], 3)
            density_list.append({f'{names_list[i]}': density})

        density_dict = dict((key, d[key]) for d in density_list for key in d)
        density_sorting = cfg.scoring_order
        density_dict = sort_dict(density_dict, density_sorting)
        return density_dict
    except:
        cfg.read_logger.error('Densities problem found: ', exc_info=True)
        return {}


    #
    #
    # for i, _ in enumerate(parts):
    #     # Criteria: split anything that might have two voices in the same part and is not a violin or a voice
    #     if (df.names[i].replace('I','') not in ['vn', 'voice'] and df['names'][i].endswith('I')):
    #         df['notes'][i] = df['notes'][i]+df['notes'][i+1]
    #         df['measures'][i] = df['measures'][i]+df['measures'][i+1]
    #         df['names'][i] = df.names[i].replace('I', '')
    #         df = df.drop([i+1], axis=0)
    #         df.reset_index(drop=True, inplace=True)
    #         del partVoices[i+1]
    #         continue
    #     if (df.names[i].startswith('voice') and num_voices > 1):
    #         df['notes'][i] = sum(df['notes'][i:i+num_voices])
    #         df['measures'][i] = sum(df['measures'][i:i+num_voices])
    #         df = df.drop([i+1], axis=0)
    #         df.reset_index(drop=True, inplace=True)
    #         del partVoices[i+1]
    #         continue
    #
    # return calculate_densities(notes_list, measures_list, names_list)
