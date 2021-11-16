from os import path
import pytest

from musif.extract.exceptions import ParseFileError
from musif.extract.extract import parse_musicxml_file

test_file = path.join("data", "static", "Did03M-Son_regina-1730-Sarro[1.05][0006].xml")
incompleted_file = path.join("data", "arias_test", "incompleted.xml")
malformed_file = path.join("data", "arias_test", "malformed.xml")


class TestParseMusicXMLFile:

    def test_parse_musicxml_basic(self):
        # GIVEN
        split_keywords = []

        # WHEN
        score = parse_musicxml_file(test_file, split_keywords)

        # THEN
        assert score is not None

    def test_parse_musicxml_with_keywords(self):
        # GIVEN
        split_keywords = ["woodwind", "brass", "wind"]

        # WHEN
        score = parse_musicxml_file(test_file, split_keywords)

        # THEN
        assert score is not None

    def test_parse_musicxml_incomplete_file(self):
        # GIVEN
        split_keywords = ["woodwind", "brass", "wind"]

        # WHEN/THEN
        with pytest.raises(ParseFileError):
            parse_musicxml_file(incompleted_file, split_keywords)

    def test_parse_musicxml_incomplete_file_not_saved_cache(self):
        # GIVEN
        split_keywords = ["woodwind", "brass", "wind"]
        try:
            parse_musicxml_file(incompleted_file, split_keywords)
        except ParseFileError:
            pass

        # WHEN/THEN
        with pytest.raises(ParseFileError):
            parse_musicxml_file(incompleted_file, split_keywords)

    def test_parse_musicxml_wrong_path(self):
        # GIVEN
        split_keywords = ["woodwind", "brass", "wind"]

        # WHEN/THEN
        with pytest.raises(ParseFileError):
            parse_musicxml_file("wrong_path", split_keywords)

    def test_parse_musicxml_wrong_path_not_saved_cache(self):
        # GIVEN
        split_keywords = ["woodwind", "brass", "wind"]
        try:
            parse_musicxml_file("wrong_path", split_keywords)
        except ParseFileError:
            pass

        # WHEN/THEN
        with pytest.raises(ParseFileError):
            parse_musicxml_file("wrong_path", split_keywords)

    def test_parse_musicxml_malformed_file(self):
        # GIVEN
        split_keywords = ["woodwind", "brass", "wind"]

        # WHEN/THEN
        with pytest.raises(ParseFileError):
            parse_musicxml_file(malformed_file, split_keywords)

    def test_parse_musicxml_malformed_file_not_saved_cache(self):
        # GIVEN
        split_keywords = ["woodwind", "brass", "wind"]
        try:
            parse_musicxml_file(malformed_file, split_keywords)
        except ParseFileError:
            pass

        # WHEN/THEN
        with pytest.raises(ParseFileError):
            parse_musicxml_file(malformed_file, split_keywords)

    def test_parse_musicxml_score_in_cache(self):
        # GIVEN
        split_keywords = []
        expected = parse_musicxml_file(test_file, split_keywords)

        # WHEN
        score = parse_musicxml_file(test_file, split_keywords)

        # THEN
        assert expected == score  # It will be the same object, so they will have the same id.
