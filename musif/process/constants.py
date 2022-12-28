from musif.extract.features.prefix import get_part_prefix

PRESENCE = "Presence_of"
"""Constant to create columns regarding presenc of an instrument or not."""

voices_list = ["sop", "ten", "alt", "bar", "bbar", "bass"]
"""List of prefixes for singers used to find voices columns"""

voices_list_prefixes = [get_part_prefix(i) for i in voices_list]
"""List of prefixes `Part_` + each element of voices_list"""
