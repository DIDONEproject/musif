from musif.scoreinfo import ScoreInfo


def get_basic_features(score_info: ScoreInfo) -> dict:
    return {
        'Id': score_info.id,
        'Composer': score_info.composer,
        'Year': score_info.year,
        'Decade': score_info.decade,
        'City': score_info.city,
        'Country': score_info.country,
        'Form': score_info.form,
        'OldClef': score_info.old_clef,
        'Key': score_info.key,
        'Mode': score_info.mode,
        'KeySignature': score_info.key_signature,
        'Tempo': score_info.tempo,
        'TimeSignature': score_info.time_signature,
        'RealScoring': score_info.real_scoring,
        'AbbrScoring': score_info.family_scoring,
        'RealScoringGrouped': score_info.grouped_family_scoring,
    }


def join_ivalues(dictionary_list):
    result_dictionary = {}
    for k in dictionary_list[0]:  # traverse each key
        # MEAN
        if k in ['Intervallic ratio', 'Trimmed intervallic ratio', 'dif. Trimmed', '% Trimmed', 'Absolute intervallic ratio', 'Std', 'Absolute Std',
                 'Syllabic ratio']:
            result_dictionary[k] = sum([d[k] for d in dictionary_list]) / len(dictionary_list)
        # MAX
        elif k in ['HighestNote', 'HighestIndex', 'HighestMeanNote', 'HighestMeanIndex']:
            mean = 'Mean' in k
            indexes = [d['HighestIndex' if not mean else 'HighestMeanIndex'] for d in dictionary_list]
            max_index = max(indexes)
            result_dictionary[k] = max_index if k in ['HighestIndex', 'HighestMeanIndex'] else \
                [d['HighestNote' if not mean else 'HighestMeanNote'] for d in dictionary_list][indexes.index(max_index)]
        elif k in ['AmbitusLargestInterval', 'AmbitusLargestSemitones', 'AscendingInterval', 'AscendingSemitones']:
            ascending = 'Ascending' in k
            semitones = [d['AmbitusLargestSemitones' if not ascending else 'AscendingSemitones'] for d in dictionary_list]
            max_semitones = max(semitones)
            result_dictionary[k] = max_semitones if k in ['AmbitusLargestSemitones', 'AscendingSemitones'] else \
                [d['AmbitusLargestInterval' if not ascending else 'AscendingInterval'] for d in dictionary_list][semitones.index(max_semitones)]
        # MIN
        elif k in ['LowestNote', 'LowestIndex', 'LowestMeanNote', 'LowestMeanIndex']:
            mean = 'Mean' in k
            indexes = [d['LowestIndex' if not mean else 'LowestMeanIndex'] for d in dictionary_list]
            lowest_index = min(indexes)
            result_dictionary[k] = lowest_index if k in ['LowestIndex', 'LowestMeanIndex'] else \
                [d['LowestNote' if mean else 'LowestMeanNote'] for d in dictionary_list][indexes.index(lowest_index)]
        elif k in ['AmbitusSmallestInterval', 'AmbitusSmallestSemitones', 'DescendingInterval', 'DescendingSemitones']:
            descending = 'Descending' in k
            semitones = [d['AmbitusSmallestSemitones' if not ascending else 'DescendingSemitones'] for d in dictionary_list]
            lowest_semitones = min(semitones)
            result_dictionary[k] = lowest_semitones if k in ['AmbitusSmallestSemitones', 'DescendingSemitones'] else \
                [d['AmbitusSmallestInterval' if not descending else 'DescendingInterval'] for d in dictionary_list][semitones.index(lowest_semitones)]
        # OTHER
        elif k in ['AmbitusAbsoluteInterval', 'AmbitusAbsoluteSemitones', 'AmbitusMeanInterval', 'AmbitusMeanSemitones']:
            result_dictionary[k] = ','.join([result_dictionary['LowestNote'], result_dictionary['HighestNote']])
    return result_dictionary
