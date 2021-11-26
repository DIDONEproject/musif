from os import path
import pytest

from musif.extract.exceptions import ParseFileError
from musif.extract.extract import parse_musescore_file, _cache

test_file = path.join("data", "static", "features", "Did03M-Son_regina-1730-Sarro[1.05][0006].mscx")
test_file_repeats = path.join("data", "arias_test", "Dem01M-O_piu-1735-Leo[1.01][0430].mscx")
test_file_repeats_same_file_different_dir = path.join("data", "arias_tests1", "Dem01M-O_piu-1735-Leo[1.01][0430].mscx")
malformed_file = path.join("data", "arias_test", "malformed.mscx")


class TestParseMusicXMLFile:

    def test_parse_musiscore_basic(self):
        # GIVEN

        # WHEN
        score = parse_musescore_file(test_file)

        # THEN
        assert score is not None

    def test_parse_musescore_with_repeats(self):
        # GIVEN
        score_no_repeats = parse_musescore_file(test_file_repeats)

        # WHEN
        score = parse_musescore_file(test_file_repeats_same_file_different_dir, expand_repeats=True)
        # different path to not use cache

        # THEN
        assert len(score.index) > len(score_no_repeats.index)

    def test_parse_musescore_wrong_path(self):
        # GIVEN

        # WHEN/THEN
        with pytest.raises(ParseFileError):
            parse_musescore_file("wrong_path")

    def test_parse_musescore_wrong_path_not_saved_cache(self):
        # GIVEN
        try:
            parse_musescore_file("wrong_path")
        except ParseFileError:
            pass

        # WHEN/THEN
        assert _cache.get("wrong_path") is None

    def test_parse_musescore_malformed_file(self):
        # GIVEN

        # WHEN/THEN
        with pytest.raises(ParseFileError):
            parse_musescore_file(malformed_file)

    def test_parse_musescore_malformed_file_not_saved_cache(self):
        # GIVEN
        try:
            parse_musescore_file(malformed_file)
        except ParseFileError:
            pass

        # WHEN/THEN
        assert _cache.get(malformed_file) is None

    def test_parse_musicxml_score_in_cache(self):
        # GIVEN

        # WHEN
        parse_musescore_file(test_file)

        # THEN
        assert _cache.get(test_file) is not None

    def test_parse_musescore_in_cache_same_content(self):
        # GIVEN

        # WHEN
        parse_musescore_file(test_file_repeats)
        parse_musescore_file(test_file_repeats_same_file_different_dir)

        # THEN
        assert _cache.get(test_file_repeats) is not None and _cache.get(test_file_repeats_same_file_different_dir) is not None
