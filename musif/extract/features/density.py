from copy import deepcopy
from typing import List, Tuple

from pandas import DataFrame

from musif.common.sort import sort_dict
from musif.config import Configuration
from musif.musicxml import Measure, Note, Part


def get_single_part_features(notes: List[Note], sounding_measures: List[Measure], measures: List[Measure]) -> dict:
    features = {
        "Notes": len(notes),
        "SoundingMeasures": len(sounding_measures),
        "Measures": len(measures),
        "SoundingDensity": len(notes) / len(sounding_measures),
        "Density": len(notes) / len(measures),
    }
    return features


def get_aggregated_parts_features(parts_features: List[dict]) -> List[dict]:
    parts_features = deepcopy(parts_features)

    df = DataFrame(parts_features)
    df_sound = df.groupby("SoundAbbreviation").aggregate({"Notes": "sum", "Measures": "sum", "SoundingMeasures": "sum"})
    df_family = df.groupby("FamilyAbbreviation").aggregate({"Notes": "sum", "Measures": "sum", "SoundingMeasures": "sum"})

    for features in parts_features:
        sound = features["SoundAbbreviation"]
        features["SoundNotes"] = df_sound.loc[sound, 'Notes']
        features["SoundMeasures"] = df_sound.loc[sound, 'Measures']
        features["SoundSoundingMeasures"] = df_sound.loc[sound, 'SoundingMeasures']
        features["SoundDensity"] = features["SoundNotes"] / features["SoundMeasures"]
        features["SoundSoundingDensity"] = features["SoundNotes"] / features["SoundSoundingMeasures"]
        family = features["FamilyAbbreviation"]
        features["FamilyNotes"] = df_family.loc[family, 'Notes']
        features["FamilyMeasures"] = df_family.loc[family, 'Measures']
        features["FamilySoundingMeasures"] = df_family.loc[family, 'SoundingMeasures']
        features["FamilyDensity"] = features["SoundNotes"] / features["SoundMeasures"]
        features["FamilySoundingDensity"] = features["SoundNotes"] / features["SoundSoundingMeasures"]

    return parts_features


def get_global_features(parts_features: List[dict], cfg: Configuration) -> dict:

    features = {}
    df = DataFrame(parts_features)
    df_sound = df.groupby("SoundAbbreviation").aggregate({"Notes": "sum", "Measures": "sum", "SoundingMeasures": "sum"})
    df_family = df.groupby("FamilyAbbreviation").aggregate({"Notes": "sum", "Measures": "sum", "SoundingMeasures": "sum"})
    df_all = df.aggregate({"Notes": "sum", "Measures": "sum", "SoundingMeasures": "sum"})
    for sound in df_sound.index:
        sound_prefix = f"Sound{sound.capitalize()}"
        features[f"{sound_prefix}Notes"] = df_sound.loc[sound, 'Notes']
        features[f"{sound_prefix}SoundingMeasures"] = df_sound.loc[sound, 'SoundingMeasures']
        features[f"{sound_prefix}Measures"] = df_sound.loc[sound, 'Measures']
        features[f"{sound_prefix}SoundingDensity"] = features[f"{sound_prefix}Notes"] / features[f"{sound_prefix}SoundingMeasures"]
        features[f"{sound_prefix}Density"] = features[f"{sound_prefix}Notes"] / features[f"{sound_prefix}Measures"]
    for family in df_family.index:
        family_prefix = f"Family{family.capitalize()}"
        features[f"{family_prefix}Notes"] = df_family.loc[family, 'Notes']
        features[f"{family_prefix}SoundingMeasures"] = df_family.loc[family, 'SoundingMeasures']
        features[f"{family_prefix}Measures"] = df_family.loc[family, 'Measures']
        features[f"{family_prefix}SoundingDensity"] = features[f"{family_prefix}Notes"] / features[f"{family_prefix}SoundingMeasures"]
        features[f"{family_prefix}Density"] = features[f"{family_prefix}Notes"] / features[f"{family_prefix}Measures"]
    features["Notes"] = df_all['Notes']
    features["SoundingMeasures"] = df_all['SoundingMeasures']
    features["Measures"] = df_all['Measures']
    features["SoundingDensity"] = features["Notes"] / features["SoundingMeasures"]
    features["Density"] = features["Notes"] / features["Measures"]

    return features


def get_measures(part: Part) -> List[Measure]:
    return [element for element in part.getElementsByClass('Measure')]


def get_notes_and_measures(part: Part) -> Tuple[List[Note], List[Measure], List[Measure]]:
    notes = []
    measures = get_measures(part)
    sounding_measures = []
    for measure in measures:
        if len(measure.notes) > 0:
            sounding_measures.append(measure)
        for note in measure.notes:
            set_ties(note, notes)
    return notes, sounding_measures, measures


def set_ties(subject, my_notes_list):
    """
    This function converts tied notes into a unique note
    """
    if not isinstance(subject, Note):
        return
    if subject.tie is None:
        my_notes_list.append(subject)
        return
    if subject.tie.type != "stop" and subject.tie.type != "continue":
        my_notes_list.append(subject)
        return
    if isinstance(my_notes_list[-1], Note):
        my_notes_list[-1].duration.quarterLength += subject.duration.quarterLength  # sum tied notes' length
        return
    back_counter = -1
    while isinstance(my_notes_list[back_counter], tuple):
        back_counter -= -1
    else:
        my_notes_list[
            back_counter
        ].duration.quarterLength += subject.duration.quarterLength  # sum tied notes' length across measures


def calculate_densities(notes_list, measures_list, names_list, cfg: Configuration):
    density_list = []
    try:
        for i, part in enumerate(names_list):
            density = round(notes_list[i]/measures_list[i], 3)
            density_list.append({f'{names_list[i]}': density})

        density_dict = dict((key, d[key]) for d in density_list for key in d)
        density_sorting = cfg.scoring_order
        density_dict = sort_dict(density_dict, density_sorting, cfg)
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