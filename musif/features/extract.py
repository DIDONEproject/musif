import glob
from os import path

import pandas as pd

from musif.config import default_features, default_sequential, default_split
from musif.features.score.custom.file_name import get_file_name_features
from musif.features.score.general import get_general_features
from musif.features.score.scoring import get_scoring_features
from musif.musicxml import *


class FeaturesExtractor:

    def __init__(self, sequential: bool = None, split: bool = None):
        self._sequential = sequential or default_sequential
        self._features_filter = set(features or default_features)
        self._split_parts = split or default_split

    def from_dir(self, musicxml_scores_dir: str, parts_filter: List[str] = None) -> DataFrame:
        musicxml_files = glob.glob(path.join(musicxml_scores_dir, f'*.{MUSICXML_FILE_EXTENSION}'))
        return self.from_files(musicxml_files, parts_filter)

    def from_files(self, musicxml_score_files: List[str], parts_filter: List[str] = None) -> DataFrame:
        features_dfs = [self.from_file(musicxml_file, parts_filter) for musicxml_file in musicxml_score_files]
        return pd.concat(features_dfs, axis=1)

    def from_file(self, musicxml_file: str, parts_filter: List[str] = None) -> DataFrame:
        score, repetition_elements, tonality = self._parse_file(musicxml_file)

        score_features, map_to_musicxml_parts = self._extract_score_features(musicxml_file, score)

        matching_parts = self._find_matching_parts(score, parts_filter, map_to_musicxml_parts)
        if len(matching_parts) == 0:
            read_logger.warning(f"No parts were found for file {musicxml_file}")
        parts_features = [self._extract_part_features(part, repetition_elements, tonality, score_features, map_to_musicxml_parts)
                          for part in matching_parts]

        return self._combine_score_and_part_features(score_features, parts_features)

    def _parse_file(self, musicxml_file: str) -> Tuple[Score, List[str], str]:
        score = parse(musicxml_file)
        split_wind_layers(score)
        repetition_elements = get_repetition_elements(score)
        tonality = get_key(score)
        return score, repetition_elements, tonality

    def _extract_score_features(self, musicxml_file: str, score: Score) -> Tuple[dict, dict]:
        features, map_to_musicxml_parts = get_scoring_features(score)
        features.update(get_file_name_features(musicxml_file))
        features.update(get_general_features(score))
        return features, map_to_musicxml_parts

    def _find_matching_parts(self, score: Score, parts_filter: List[str], abbreviation_to_part: Dict[str, str]) -> List[Part]:
        parts_filter = set(parts_filter)
        chosen_score_part_names = {score_part_name for abbreviation, score_part_name in abbreviation_to_part.items() if abbreviation in parts_filter}
        return [part for part in score.parts if part.partName in chosen_score_part_names]

    def _combine_score_and_part_features(self, score_features: dict, part_features: List[dict]) -> DataFrame:
        return DataFrame({})

    def _extract_part_features(self, part: Part, repetition_elements: List[str], tonality: str, score_features: dict, map_to_musicalxml_parts: Dict[str, str]) -> dict:
        return {}
    #     features = {}
    #     features.update(get_basic_features(score_info))
    #     voice_part_expanded = musicxml.expand_part(part, repetition_elements)
    #     role = score_info.role
    #     character = score_info.role.split('&')
    #     # if 'voice' in parts_filter:
    #     #     role = character[i] if character != '' and len(character) > i else ''
    #
    #     tg1 = get_TempoGrouped1(score_info.tempo)
    #     grouped_variables = {
    #         "KeySignatureGrouped": get_KeySignatureType(score_info.key_signature),
    #         "TimeSignatureGrouped": get_TimeSignatureType(score_info.time_signature),
    #         "TempoGrouped1": tg1,
    #         "TempoGrouped2": get_TempoGrouped2(tg1)
    #     }
    #
    #     ############# Extract information related to every excel that we need to obtain: From I to V #############
    #
    #     notes = musicxml.get_notes(voice_part_expanded)
    #     numeric_intervals, text_intervals = musicxml.get_intervals(notes)
    #
    #     i_values = get_lyrics_features(voice_part_expanded, notes)
    #     i_values.update(get_interval_features(numeric_intervals))
    #     i_values.update(get_ambitus_features(voice_part_expanded))
    #
    #     text_intervals_count = Counter(text_intervals)
    #     ii_a_values = text_intervals_count
    #
    #     iii_values = get_interval_type_features(text_intervals_count)
    #
    #     iv_a_values = get_emphasized_scale_degrees_features(notes, tonality)
    #
    #     if score_info.old_clef and score_info.old_clef != '':
    #         v_clefs = {c: 1 for c in score_info.old_clef.split(',')}
    #     else:
    #         v_clefs = {musicxml.get_part_clef(voice_part_expanded): 1}
    #
    #     return i_values, ii_a_values, iii_values, iv_a_values, v_clefs

        # IVb.EMPHASISED SCALE DEGREES
        iv_b_Emph_list = []
        iv_b_EmphDict = {}
        # if has_table:
        #     if modulations is not None:  # The user may have written only the not-expanded version
        #         harmonic_analysis = compute_modulations(voice_part, voice_part_expanded, modulations)
        #     if harmonic_analysis is not None:
        #         ivB_EmphDict, error = ivEmphasised_scale_degrees_relative(notes, tonality, harmonic_analysis)
        #         ivB_Emph_list.append(ivB_EmphDict)
        #         if len(error) != 0:
        #             self._logger.error(f'Error in "{xml_name}" part number: {str(i + 1)}. The missing measures are: {error}')

    #     # only if it is a voice duo we separate the information in several rows:
    #     if len(parts) > 1 and all(i == 'voice' for i in parts):  # only if it is a duo, trio, etc
    #         all_at_a_time = False
    #         name_variables["Id"] = str(id_label) + ALPHA[i] if str(id_label) != '' else ''
    #         total = {"Total analysed": 1 / len(parts)}
    #         general_variables_dict = dict(name_variables, **excel_variables, **general_variables, **grouped_variables, **scoring_variables, **clef_dic,
    #                                       **total)
    #         append_solutions_to_dfs(general_variables_dict, vclefs, iValues_dict, iiaIntervals_dict, iiiintervals_types_dict, ivA_EmphDict, ivB_EmphDict,
    #                                 clefs_info, all_info, intervals_info, intervals_types, emphasised_scale_degrees_info_A, emphasised_scale_degrees_info_B)
    #     else:
    #         all_at_a_time = True
    #
    #         # put all the dictionaries into the dataframes

    # def _append_solutions_to_dfs(self,
    #     general_variables_dict: dict,
    #     i_values: dict,
    #     ii_a_intervals: dict,
    #     iii_intervals_types: dict,
    #     iv_a_emph: dict,
    #     iv_b_emph: dict,
    #     v_clefs: dict,
    #     clefs_info: dict,
    #     all_info,
    #     intervals_info,
    #     intervals_types,
    #     emphasised_scale_degrees_info_A,
    #     emphasised_scale_degrees_info_B
    # ) -> DataFrame:
    #     # Perform cleaning over general_variables_dict: drop empty
    #     general_variables_dict = {k:general_variables_dict[k] for k in general_variables_dict if general_variables_dict[k] != ''}
    #     clefs_info.append(dict(general_variables_dict, **vclefs))
    #     all_info.append(dict(general_variables_dict, **iValues_dict))
    #     intervals_info.append(dict(general_variables_dict, **iiaIntervals_dict))
    #     intervals_types.append(dict(general_variables_dict, **iiiintervals_types_dict))
    #     emphasised_scale_degrees_info_A.append(dict(general_variables_dict, **ivA_EmphDict))
    #     emphasised_scale_degrees_info_B.append(dict(general_variables_dict, **ivB_EmphDict))

    # def join_ivalues(self, dictionary_list):
    #     result_dictionary = {}
    #     for k in dictionary_list[0]:  # traverse each key
    #         # MEAN
    #         if k in ['Intervallic ratio', 'Trimmed intervallic ratio', 'dif. Trimmed', '% Trimmed', 'Absolute intervallic ratio', 'Std', 'Absolute Std',
    #                  'Syllabic ratio']:
    #             result_dictionary[k] = sum([d[k] for d in dictionary_list]) / len(dictionary_list)
    #         # MAX
    #         elif k in ['HighestNote', 'HighestIndex', 'HighestMeanNote', 'HighestMeanIndex']:
    #             mean = 'Mean' in k
    #             indexes = [d['HighestIndex' if not mean else 'HighestMeanIndex'] for d in dictionary_list]
    #             max_index = max(indexes)
    #             result_dictionary[k] = max_index if k in ['HighestIndex', 'HighestMeanIndex'] else \
    #                 [d['HighestNote' if not mean else 'HighestMeanNote'] for d in dictionary_list][indexes.index(max_index)]
    #         elif k in ['AmbitusLargestInterval', 'AmbitusLargestSemitones', 'AscendingInterval', 'AscendingSemitones']:
    #             ascending = 'Ascending' in k
    #             semitones = [d['AmbitusLargestSemitones' if not ascending else 'AscendingSemitones'] for d in dictionary_list]
    #             max_semitones = max(semitones)
    #             result_dictionary[k] = max_semitones if k in ['AmbitusLargestSemitones', 'AscendingSemitones'] else \
    #                 [d['AmbitusLargestInterval' if not ascending else 'AscendingInterval'] for d in dictionary_list][semitones.index(max_semitones)]
    #         # MIN
    #         elif k in ['LowestNote', 'LowestIndex', 'LowestMeanNote', 'LowestMeanIndex']:
    #             mean = 'Mean' in k
    #             indexes = [d['LowestIndex' if not mean else 'LowestMeanIndex'] for d in dictionary_list]
    #             lowest_index = min(indexes)
    #             result_dictionary[k] = lowest_index if k in ['LowestIndex', 'LowestMeanIndex'] else \
    #                 [d['LowestNote' if mean else 'LowestMeanNote'] for d in dictionary_list][indexes.index(lowest_index)]
    #         elif k in ['AmbitusSmallestInterval', 'AmbitusSmallestSemitones', 'DescendingInterval', 'DescendingSemitones']:
    #             descending = 'Descending' in k
    #             semitones = [d['AmbitusSmallestSemitones' if not ascending else 'DescendingSemitones'] for d in dictionary_list]
    #             lowest_semitones = min(semitones)
    #             result_dictionary[k] = lowest_semitones if k in ['AmbitusSmallestSemitones', 'DescendingSemitones'] else \
    #                 [d['AmbitusSmallestInterval' if not descending else 'DescendingInterval'] for d in dictionary_list][semitones.index(lowest_semitones)]
    #         # OTHER
    #         elif k in ['AmbitusAbsoluteInterval', 'AmbitusAbsoluteSemitones', 'AmbitusMeanInterval', 'AmbitusMeanSemitones']:
    #             result_dictionary[k] = ','.join([result_dictionary['LowestNote'], result_dictionary['HighestNote']])
    #     return result_dictionary
