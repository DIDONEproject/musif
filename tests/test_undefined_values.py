"""A value that cannot be computed is NaN, never 0 (nor infinite): ratios
without a denominator in the density, texture and scale-degree features, and
the guard for harmonic annotations without a global key."""
import math

import numpy as np
import pandas as pd
from music21.key import Key
from music21.note import Note

from musif.config import ExtractConfiguration
from musif.extract.constants import DATA_PART_ABBREVIATION
from musif.extract.extract import _has_global_key
from musif.extract.features.core.constants import DATA_KEY
from musif.extract.features.core.handler import DATA_NOTES, DATA_SOUNDING_MEASURES
from musif.extract.features.density import handler as density
from musif.extract.features.scale import handler as scale
from musif.extract.features.tempo.constants import TIME_SIGNATURES
from musif.extract.features.texture import handler as texture

CONFIG = ExtractConfiguration(None)


def _part(abbreviation, notes, sounding_measures):
    return {
        DATA_PART_ABBREVIATION: abbreviation,
        DATA_NOTES: notes,
        DATA_SOUNDING_MEASURES: sounding_measures,
        TIME_SIGNATURES: ["4/4", "4/4"],
    }


class TestDensity:
    def test_part_that_never_sounds(self):
        features = {}
        density.update_part_objects({}, _part("va", [], []), CONFIG, features)
        # no notes over the eight beats of the score: a true 0
        assert features["Density"] == 0
        # no sounding beat to divide by: 0 would read as a part that sounds
        # and plays nothing
        assert math.isnan(features["SoundingDensity"])

    def test_part_that_sounds(self):
        features = {}
        notes = [Note("C4") for _ in range(4)]
        density.update_part_objects({}, _part("va", notes, [0]), CONFIG, features)
        assert features["Density"] == 4 / 8
        assert features["SoundingDensity"] == 4 / 4

    def test_density_per_quarter_note(self):
        # the same four notes in two measures of 2/2: four beats, but eight
        # quarter notes, as in 4/4
        features = {}
        notes = [Note("C4") for _ in range(4)]
        part = _part("va", notes, [0])
        part[TIME_SIGNATURES] = ["2/2", "2/2"]
        density.update_part_objects({}, part, CONFIG, features)
        assert features["Density"] == 4 / 4
        assert features["DensityQuarters"] == 4 / 8
        assert features["SoundingDensityQuarters"] == 4 / 4


class TestTexture:
    def test_no_ratio_against_a_part_without_notes(self):
        notes = [Note("C4") for _ in range(4)]
        parts = [_part("vnI", notes, [0]), _part("va", [], [])]
        features = {}
        texture.update_score_objects({}, parts, CONFIG, [{}, {}], features)
        # this used to be infinite
        assert math.isnan(features["PartVnI|PartVa_Texture"])


class TestScaleDegrees:
    def test_part_without_notes_has_counts_but_no_proportions(self):
        features = {}
        scale.update_part_objects({DATA_KEY: Key("C")}, {DATA_NOTES: []}, CONFIG, features)
        assert features["Degree1_Count"] == 0
        assert math.isnan(features["Degree1_Per"])

    def test_part_with_notes(self):
        features = {}
        notes = [Note("C4"), Note("C5"), Note("G4"), Note("B4")]
        scale.update_part_objects({DATA_KEY: Key("C")}, {DATA_NOTES: notes}, CONFIG, features)
        assert features["Degree1_Per"] == 0.5
        assert features["Degree2_Per"] == 0  # a measured zero


class TestGlobalKeyGuard:
    def test_annotations_with_a_global_key(self):
        assert _has_global_key(pd.DataFrame({"globalkey": ["C", "C"]}))

    def test_annotations_without_a_global_key(self):
        # what ms3 returns when the first label is invalid
        assert not _has_global_key(pd.DataFrame({"globalkey": [np.nan, np.nan]}))
        assert not _has_global_key(pd.DataFrame({"label": ["I", "V"]}))

    def test_no_annotations_at_all_is_left_to_the_feature_modules(self):
        assert _has_global_key(None)
        assert _has_global_key(pd.DataFrame())
