from os import path
import pytest

from musif.extract.exceptions import ParseFileError
from musif.extract.extract import parse_musescore_file, _cache
from .constants import BASE_PATH, INCOMPLETE_FILE, MALFORMED_FILE

test_file = path.join(BASE_PATH, "static", "features", "Did03M-Son_regina-1730-Sarro[1.05][0006].mscx")
test_file_repeats = path.join(BASE_PATH, "arias_test", "Dem01M-O_piu-1735-Leo[1.01][0430].mscx")
test_file_repeats_same_file_different_dir = path.join(BASE_PATH, "arias_tests1", "Dem01M-O_piu-1735-Leo[1.01][0430].mscx")
MALFORMED_FILE = path.join(BASE_PATH, "arias_test", "malformed.mscx")


class TestParseMusescoreFile:

    def test_parse_musiscore_basic(self):
        # GIVEN
        _cache.clear()
        
        # WHEN
        score = parse_musescore_file(test_file)

        # THEN
        assert score is not None

    def test_parse_musescore_with_repeats(self):
        # GIVEN
        score_no_repeats = parse_musescore_file(test_file_repeats)
        _cache.clear()

        # WHEN
        score = parse_musescore_file(test_file_repeats, expand_repeats=True)

        # THEN
        assert len(score.index) > len(score_no_repeats.index)

    def test_parse_musescore_wrong_path(self):
        # GIVEN

        # WHEN/THEN
        with pytest.raises(ParseFileError):
            parse_musescore_file("wrong_path")

    def test_parse_musescore_wrong_path_not_saved_cache(self):
        # GIVEN
        _cache.clear()
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
            parse_musescore_file(MALFORMED_FILE)

    def test_parse_musescore_malformed_file_not_saved_cache(self):
        # GIVEN
        _cache.clear()
        try:
            parse_musescore_file(MALFORMED_FILE)
        except ParseFileError:
            pass

        # WHEN/THEN
        assert _cache.get(MALFORMED_FILE) is None

    def test_parse_musicxml_score_in_cache(self):
        # GIVEN
        _cache.clear()
        # WHEN
        parse_musescore_file(test_file)

        # THEN
        assert _cache.get(test_file) is not None

    def test_parse_musescore_in_cache_same_content(self):
        # GIVEN
        _cache.clear()
        # WHEN
        parse_musescore_file(test_file_repeats)
        parse_musescore_file(test_file_repeats_same_file_different_dir)

        # THEN
        assert _cache.get(test_file_repeats) is not None
        assert _cache.get(test_file_repeats_same_file_different_dir) is not None
