"""Unit tests for configuration handling and pipeline plumbing."""
import pandas as pd
import pytest
from music21.meter import TimeSignature
from music21.note import Note
from music21.stream import Measure

from musif.config import ExtractConfiguration, PostProcessConfiguration
from musif.extract.basic_modules.file_name_generic.handler import (
    update_score_objects as file_name_handler,
)
from musif.extract.common import _filter_parts_data
from musif.extract.constants import DATA_FILE
from musif.extract.features.tempo.handler import extract_time_signatures
from musif.extract.utils import cast_mixed_dtypes


class TestConfigAliases:
    def test_legacy_keys_reach_the_real_options(self):
        config = PostProcessConfiguration(
            {"grouped": True, "delete_files": True,
             "separate_intrumentation_column": True}
        )
        assert config.grouped_analysis is True
        assert config.delete_failed_files is True
        assert config.separate_instrumentation_column is True

    def test_log_key_aliases(self):
        config = PostProcessConfiguration(
            {"log": {"file_path": "/tmp/x.log", "console_level": "ERROR",
                     "file_level": "ERROR"}}
        )
        assert config.log_file == "/tmp/x.log"


class TestVoiceFilter:
    def test_expanded_once_at_configuration_time(self):
        config = ExtractConfiguration(None, parts_filter=["voice", "vnI"])
        assert "voice" not in config.parts_filter
        assert "sop" in config.parts_filter
        assert "vnI" in config.parts_filter

    def test_filtering_does_not_mutate_the_input(self):
        parts_filter = ["voice"]
        _filter_parts_data([], parts_filter)
        assert parts_filter == ["voice"]


class TestFileNameGeneric:
    def _parse(self, file_name):
        score_features = {}
        file_name_handler({DATA_FILE: file_name}, [], None, [], score_features)
        return score_features["Artist"], score_features["Title"]

    def test_underscore_splits_artist_and_title(self):
        assert self._parse("/x/Corelli_op1n1.xml") == ("Corelli", "op1n1")

    def test_no_underscore(self):
        # this shape used to raise IndexError for every such file
        assert self._parse("/x/example.xml") == ("", "example")

    def test_multiple_dots(self):
        assert self._parse("/x/a.b.xml") == ("", "a.b")


class TestDtypeCasting:
    def test_stray_string_becomes_nan_not_crash(self):
        column = pd.Series([1.5, 2.5, "Allegro"])
        result = cast_mixed_dtypes(column)
        assert pd.isna(result.iloc[2])
        assert result.iloc[0] == 1.5

    def test_fraction_strings_are_evaluated(self):
        column = pd.Series([1.5, 2.5, "1/4"])
        result = cast_mixed_dtypes(column)
        assert abs(float(result.iloc[2]) - 0.25) < 1e-12


class TestTimeSignatureList:
    def test_own_time_signature_wins_on_repeated_measure_numbers(self):
        measures = []
        for number, timesig in [(1, "4/4"), (2, None), (2, "1/4")]:
            measure = Measure(number=number)
            if timesig:
                measure.append(TimeSignature(timesig))
            measure.append(Note("C4"))
            measures.append(measure)
        _, _, time_signatures, _, _ = extract_time_signatures(measures, {})
        # the repeated measure number used to silently reuse '4/4'
        assert time_signatures == ["4/4", "4/4", "1/4"]


class TestWindowValidation:
    def test_overlap_must_be_smaller_than_window(self, tmp_path):
        from musif.extract.extract import FeaturesExtractor

        extractor = FeaturesExtractor(
            {"data_dir": "tests/data/scores", "window_size": 2, "overlap": 2,
             "parallel": 1, "output_dir": str(tmp_path),
             "log": {"log_file": str(tmp_path / "musif.log"),
                     "file_log_level": "ERROR", "console_log_level": "ERROR"}}
        )
        with pytest.raises(ValueError, match="overlap"):
            extractor.extract()
