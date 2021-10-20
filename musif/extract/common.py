from typing import List, Optional

from musif.extract.constants import DATA_PART_ABBREVIATION


def filter_parts_data(parts_data: List[dict], parts_filter: Optional[List[str]]) -> List[dict]:
    if parts_filter is None:
        return parts_data
        
    if 'voice' in parts_filter:
        parts_filter[parts_filter.index('voice')]='ten'
        parts_filter.append('sop')
        parts_filter.append('bar')

    parts_filter_set = set(parts_filter)
    return [part_data for part_data in parts_data if part_data[DATA_PART_ABBREVIATION] in parts_filter_set]


def part_matches_filter(part_abbreviation: str, parts_filter: Optional[List[str]]) -> bool:
    if parts_filter is None:
        return True
    parts_filter_set = set(parts_filter)
    return part_abbreviation in parts_filter_set

