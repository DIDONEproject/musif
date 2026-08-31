from typing import List


from music21.note import Note

from numpy import mean


from musif.common._constants import VOICE_FAMILY

from musif.config import ExtractConfiguration

from musif.extract.common import _filter_parts_data

from musif.extract.constants import DATA_FAMILY, DATA_PART_ABBREVIATION

from musif.extract.features.core.handler import DATA_LYRICS, DATA_NOTES

from musif.extract.features.prefix import get_part_feature, get_score_feature

from .constants import *

from musif.extract.features.core.constants import (
    DATA_MEASURES,
    DATA_SOUNDING_MEASURES,
)


def update_part_objects(
    score_data: dict, part_data: dict, cfg: ExtractConfiguration, part_features: dict
):

    notes = part_data[DATA_NOTES]

    lyrics = part_data[DATA_LYRICS]

    if part_data[DATA_FAMILY] == VOICE_FAMILY:

        syllabic_ratio = get_syllabic_ratio(notes, lyrics)

        voice_presence = len(part_data[DATA_SOUNDING_MEASURES]) / len(
            part_data[DATA_MEASURES]
        ) if part_data[DATA_MEASURES] else 0

        part_features.update(
            {
                SYLLABLES: len(lyrics),
                SYLLABIC_RATIO: syllabic_ratio,
                VOICE_PRESENCE: voice_presence,
            }
        )


def update_score_objects(
    score_data: dict,
    parts_data: List[dict],
    cfg: ExtractConfiguration,
    parts_features: List[dict],
    score_features: dict,
):

    parts_data = _filter_parts_data(parts_data, cfg.parts_filter)

    if len(parts_data) == 0:
        return

    voice_parts_data = [
        part_data for part_data in parts_data if part_data[DATA_FAMILY] == VOICE_FAMILY
    ]

    features = {}

    if voice_parts_data:

        for part_data in voice_parts_data:

            part = part_data[DATA_PART_ABBREVIATION]

            features[get_part_feature(part, SYLLABIC_RATIO)] = get_syllabic_ratio(
                part_data[DATA_NOTES], part_data[DATA_LYRICS]
            )

            features[get_part_feature(part, SYLLABLES)] = len(part_data[DATA_LYRICS])

            features[get_part_feature(part, VOICE_PRESENCE)] = len(
                part_data[DATA_SOUNDING_MEASURES]
            ) / len(part_data[DATA_MEASURES]) if part_data[DATA_MEASURES] else 0

        notes = [
            note for part_data in voice_parts_data for note in part_data[DATA_NOTES]
        ]

        lyrics = [
            lyrics
            for part_data in voice_parts_data
            for lyrics in part_data[DATA_LYRICS]
        ]

        features[get_score_feature(SYLLABLES)] = len(lyrics)

        # ratio of sums: a note-weighted aggregate over the voice parts
        features[get_score_feature(SYLLABIC_RATIO)] = get_syllabic_ratio(notes, lyrics)

        # each voice part is measured against its OWN last note, then averaged
        voice_regs = [
            get_voice_reg(part_data[DATA_NOTES]) for part_data in voice_parts_data
        ]
        voice_regs = [v for v in voice_regs if v == v]
        features[get_score_feature(VOICE_REG)] = (
            mean(voice_regs) if voice_regs else float("nan")
        )

    return score_features.update(features)


def get_syllabic_ratio(notes: List[Note], lyrics: List[str]) -> float:

    if lyrics is None or len(lyrics) == 0:
        # undefined without lyrics; a genuine ratio is never 0
        return float("nan")

    return len(notes) / len(lyrics)


def get_voice_reg(notes: List[Note]) -> float:
    # DATA_NOTES never contains chords (they are excluded from note-based
    # features), so a plain pitch access is safe here
    if notes:
        last_note = notes[-1].pitch.midi
        distances = [note.pitch.midi - last_note for note in notes]
        return mean(distances)

    return float("nan")
