import warnings
from typing import List

from musif.config import Configuration


def sort(list_to_sort: List[str], reference_list: List[str]) -> List[str]:
    sort_dictionary = {elem: i for i, elem in enumerate(reference_list)}
    found = [elem for elem in list_to_sort if elem in sort_dictionary]
    orphans = [elem for elem in list_to_sort if elem not in sort_dictionary]
    return sorted(found, key=lambda x: sort_dictionary[x]) + orphans


def sort_dict(dict_to_sort, main_list, cfg: Configuration):
    indexes = []
    huerfanos = []
    for i in dict_to_sort:
        if i in main_list:
            indexes.append(main_list.index(i))
        else:
            huerfanos.append({i: dict_to_sort[i]})
            cfg.logger.warning(
                'We do not have the appropiate sorting for {}'.format(i))
    indexes = sorted(indexes)
    list_sorted = [{main_list[i]: dict_to_sort[main_list[i]]} for i in indexes]
    list_sorted = list_sorted + huerfanos
    dict_sorted = dict((key, d[key]) for d in list_sorted for key in d)
    return dict_sorted

def sort_columns(data, sorting_list):
    cols = sort(data.columns.tolist(), [i for i in sorting_list])
    data=data[cols]
    return data
    
def sort_dataframe(data, column, sorting_lists, key_to_sort):
    if key_to_sort == "Alphabetic":
        dataSorted = data.sort_values(by=[column])
    else:
        form_list = sorting_lists[key_to_sort]  # es global
        indexes = []
        for i in data[column]:
            if str(i).lower().strip() not in ["nan", 'nd']:
                value = i.strip() if key_to_sort not in [
                    'FormSorting', 'CharacterSorting'] else i.strip().lower()
                try:
                    # index = form_list.index(value)
                    index = form_list.index(value) if value in form_list else 999
                except ValueError:
                    index = 999
                    warnings.warn('We do not have the value {} in the sorting list {}'.format(
                        value, key_to_sort))
                indexes.append(index)
            else:
                indexes.append(999)  # at the end of the list

        data.loc[:, "Ranks"] = indexes
        dataSorted = data.sort_values(by=["Ranks"])
        dataSorted.drop("Ranks", 1, inplace=True)
    return dataSorted

# class Sorting:
#     """
#     This class contains the most appropriate sortings for piece grouping criteria (1st columns in reports)
#     """
#
#     @property
#     def final(self) -> List[str]:
#         # returns sorting for root notes of the scale, by ascending semitones
#         return ['C', 'C#', 'Db', 'D', 'D#', 'Eb', 'E', 'F', 'F#', 'Gb', 'G', 'G#', 'Ab', 'A', 'A#', 'Bb', 'B']
#
#     @property
#     def instrument(self) -> List[str]:
#         # returns list of abbreviated instrument names in customary order in modern orchestral scores, from 1st to last staff
#         return ['fl', 'ob', 'eh', 'cl', 'bn', 'hn', 'tpt', 'tb', 'clno', 'timp', 'tamb', 'triang', 'mand', 'salt', 'vnI', 'vnII', 'va', 'bs']
#
#     @property
#     def instruments(self) -> List[str]:
#         # returns sorting for groups of instruments (already abbreviated)
#         return ['fls', 'fts', 'obs', 'ehs', 'cls', 'fags', 'cfags', 'hns', 'hncs', 'tpts', 'tptcs', 'tbs', 'tbcs', 'clnos', 'timp', 'tamb', 'tambno', 'triang',
#                 'arp', 'mands', 'salts', 'lts', 'tiors', 'cembs', 'orgs', 'fp', 'vne', 'cb']
#
#     @property
#     def families(self) -> List[str]:  # TODO: not used
#         return ['ww', 'br', 'perc', 'pluc', 'str']
#
#     @property
#     def families_combinations(self) -> List[str]:
#         return ['str', 'ww,str', 'br,str', 'perc,str', 'ww,br,str', 'ww,perc,str', 'br,perc,str', 'ww,br,perc,str']
#
#     @property
#     def scoring(self):
#         strings_combinations = ['str']
#         only_instr = self.instrument[:-4]
#         # resolved = ['fls', 'obs', 'ehs', 'cls', 'bns', 'hns', 'tpts', 'tbs', 'clnos', 'timp', 'tamb', 'triang', 'mand', 'salt', 'str'][:-1]
#         resolved = self.instruments
#         possibilities = ['str']
#         for n in range(1, len(only_instr) + 1):  # combinations of 1-x instruments + combinations of strings
#             for i in range(len(only_instr)):
#                 all_others = only_instr[i + 1:]
#                 all_others_r = resolved[i + 1:]
#
#                 all_others_combinations = [','.join(x) for x in combinations(all_others, n - 1)]
#                 all_others_resolved_combinations = [','.join(x) for x in combinations(all_others_r, n - 1)]
#
#                 for e in range(len(all_others_combinations)):
#                     subgroup_possibilities = []
#
#                     only_comb = combine_lists(only_instr[i], all_others_combinations[e],
#                                                     strings_combinations)  # combinations of strings + other instruments
#                     resolved_comb = combine_lists(resolved[i], all_others_resolved_combinations[e],
#                                                         strings_combinations)  # combinations of the grouping + strings
#
#                     subgroup_possibilities += only_comb
#                     subgroup_possibilities += resolved_comb  # luego lo quitaremos, es solo para comprobar que no se repite de aquí en adelante
#
#                     if len(all_others_combinations) != 1 or all_others_combinations[0] != '':  # if we are not combining single instruments
#                         # it creates combinations: ob, eh + ob, ehs (combinaciones1) and obs, eh, obs, ehs (combinaciones2) and then goes through all these combinations
#                         combinaciones1 = [all_others_combinations[e]]
#                         initial_comb = all_others_combinations[e].split(",")
#                         for c in range(len(initial_comb)):
#                             index = all_others.index(initial_comb[c])
#                             if all_others_r[index] != all_others[index]:
#                                 list_c = [','.join(initial_comb[: c]), all_others_r[index], ','.join(initial_comb[c + 1:])]
#                                 if '' in list_c:
#                                     list_c = [lc for lc in list_c if lc != '']
#                                 if ','.join(list_c) not in combinaciones1:
#                                     combinaciones1.append(','.join(list_c))
#                         combinaciones1 = list(dict.fromkeys(combinaciones1))
#                         combinaciones2 = [all_others_resolved_combinations[e]]
#                         initial_comb = all_others_resolved_combinations[e].split(",")
#                         for c in range(len(initial_comb)):
#                             index = all_others_r.index(initial_comb[c])
#                             if all_others[index] != all_others_r[index]:  # no duplicates
#                                 list_c = [','.join(initial_comb[: c]), all_others[index], ','.join(initial_comb[c + 1:])]
#                                 if '' in list_c:
#                                     list_c = [lc for lc in list_c if lc != '']
#                                 if ','.join(list_c) not in combinaciones2:
#                                     combinaciones2.append(','.join(list_c))
#                         combinaciones2 = list(dict.fromkeys(combinaciones2))  # delete duplicates (when singualr and plural forms are the same)
#
#                         finalc1 = list(dict.fromkeys(combinaciones1 + combinaciones2[1:]))
#                         finalc2 = list(dict.fromkeys(combinaciones2 + combinaciones1[1:]))
#                         for c in range(max(len(finalc1), len(finalc2))):
#                             # combination between the grouping and the instruments
#                             if c < len(finalc1):
#                                 resolved_only_comb = combine_lists(resolved[i], finalc1[c], strings_combinations)
#                                 if resolved_only_comb[0] not in subgroup_possibilities:
#                                     subgroup_possibilities += resolved_only_comb
#                             # combination between the instruments and the combination
#                             if c < len(finalc2):
#                                 only_resolved_comb = combine_lists(only_instr[i], finalc2[c], strings_combinations)
#                                 if only_resolved_comb[0] not in subgroup_possibilities:
#                                     subgroup_possibilities += only_resolved_comb
#
#                     subgroup_possibilities.remove(resolved_comb[0])  # delete because it is subsequently introduced
#                     possibilities += subgroup_possibilities
#                     # combination between the grouping and strings
#                     if only_instr[i] != resolved[i]:  # only if singular and plural forms are different; if not, they would be duplicated
#                         possibilities += resolved_comb
#         return possibilities
#
#
#
# sorting = Sorting()
