from typing import List, Optional


def filter_parts_data(parts_data: List[dict], parts_filter: Optional[List[str]]) -> List[dict]:
    if parts_filter is None:
        return parts_data
    parts_filter_set = set(parts_filter)
    return [part_data for part_data in parts_data if part_data["abbreviation"] in parts_filter_set]
