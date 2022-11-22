import warnings
from logging import getLogger
from typing import List, Dict

from musif.config import LOGGER_NAME
from pandas import DataFrame


def sort_list(list_to_sort: List[str], reference_list: List[str]) -> List[str]:
    """
    Sorts first list based on the second one. Those elements that are not present
    in the reference list will be placed at the end. Returns the same list re-ordered.

    Parameters
    ----------
    list_to_sort : list
        List that needs to be sorted according to some criteria
    reference_list : str
        List used as reference to sort the first one.
    """
    sort_dictionary = {elem: i for i, elem in enumerate(reference_list)}
    found = [elem for elem in list_to_sort if elem in sort_dictionary]
    orphans = [elem for elem in list_to_sort if elem not in sort_dictionary]
    return sorted(found, key=lambda x: sort_dictionary[x]) + orphans


def sort_dict(dict_to_sort: dict, reference_list: list) -> dict:
    """
    Sorts dictionary keys according to a reference li()

    Parameters
    ----------
    dict_to_sort : dict
        Dictionary that needs to be sorted according to some criteria
    main_list : list
        List used as reference to sort the first one.
    """

    indexes = []
    oprhans = []
    for i in dict_to_sort:
        if i in reference_list:
            indexes.append(reference_list.index(i))
        else:
            oprhans.append({i: dict_to_sort[i]})
            getLogger(LOGGER_NAME).warning(
                "We do not have the appropiate sorting for {}".format(i)
            )
    indexes = sorted(indexes)
    list_sorted = [
        {reference_list[i]: dict_to_sort[reference_list[i]]} for i in indexes
    ]
    list_sorted = list_sorted + oprhans
    dict_sorted = dict((key, d[key]) for d in list_sorted for key in d)
    return dict_sorted


def sort_columns(data: DataFrame, sorting_list: list) -> DataFrame:
    """
    Reorders columns of a Dataframe according to a reference list. Uses sort_list.

    Parameters
    ----------
    data : DataFrame
        DataFrame whose columns needs to be re-ordered according to some criteria
    sorting_list : list
        List used as reference to sort columns.
    """

    cols = sort_list(data.columns.tolist(), [i for i in sorting_list])
    data = data[cols]
    return data


def sort_dataframe(
    data: DataFrame, column: str, sorting_lists: Dict[list, str], key_to_sort: str
) -> DataFrame:
    """
    Sorts Dataframe's rows by a column using a list as a reference.
    Parameters
    ----------
    data: DataFrame
        DataFrame to be re-ordered according to some criteria.
    column: str
        Column of the Dataframe used as key.
    sorting_lists: Dict[list]
        Dictionary containing lists used as reference to sort values.
    key_to_sort: str
        Key from sorting_lists that contains the desired list to be used as reference.
    """
    if key_to_sort == "Alphabetic":
        dataSorted = data.sort_values(by=[column])
    else:
        form_list = sorting_lists[key_to_sort]  # es global
        indexes = []
        for i in data[column]:
            if str(i).lower().strip() not in ["nan", "nd"]:
                value = (
                    i.strip()
                    if key_to_sort not in ["FormSorting", "CharacterSorting"]
                    else i.strip().lower()
                )
                try:
                    # index = form_list.index(value)
                    index = form_list.index(value) if value in form_list else 999
                except ValueError:
                    index = 999
                    warnings.warn(
                        "We do not have the value {} in the sorting list {}".format(
                            value, key_to_sort
                        )
                    )
                indexes.append(index)
            else:
                indexes.append(999)  # at the end of the list

        data.loc[:, "Ranks"] = indexes
        dataSorted = data.sort_values(by=["Ranks"])
        dataSorted.drop("Ranks", 1, inplace=True)
    return dataSorted
