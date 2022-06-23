from os import path

import pytest

from musif.common._utils import read_object_from_yaml_file
from musif.config import Configuration
from musif.extract.exceptions import ParseFileError
from musif.extract.extract import PartsExtractor, _cache

from .constants import BASE_PATH, CONFIG_FILE, INCOMPLETE_FILE, MALFORMED_FILE

empty_dir = path.join(BASE_PATH, "config_test")

directory_tests = path.join(BASE_PATH, "arias_tests1")
first_file_dir = path.join(BASE_PATH, "arias_test", "Dem01M-O_piu-1735-Leo[1.01][0430].xml")
first_file_same_file_different_dir = path.join(BASE_PATH, "arias_tests1", "Dem01M-O_piu-1735-Leo[1.01][0430].xml")
second_file_dir = path.join(BASE_PATH, "arias_test", "Dem02M-In_te-1733-Caldara[1.02][0417].xml")

first_content = ['obI', 'obII', 'hnI', 'hnII', 'ten', 'vnI', 'vnII', 'va', 'bs']
first_content_no_split = ['ob', 'hn', 'ten', 'vnI', 'vnII', 'va', 'bs']
union_content = ['obI', 'obII', 'hnI', 'hnII', 'sop', 'ten', 'vnI', 'vnII', 'va', 'bs']


class TestPartsExtractor:

    # -----------------CONFIGURATION-----------------

    def test_config_passed_as_path(self):
        # GIVEN
        expected = read_object_from_yaml_file(CONFIG_FILE)

        # WHEN
        extractor = PartsExtractor(CONFIG_FILE)

        # THEN
        assert expected == extractor._cfg.to_dict()

    def test_config_passed_as_keywords(self):
        # GIVEN
        config_dict = Configuration(CONFIG_FILE).to_dict()
        expected = read_object_from_yaml_file(CONFIG_FILE)

        # WHEN
        extractor = PartsExtractor(**config_dict)

        # THEN
        assert extractor._cfg.to_dict() == expected

    def test_config_passed_as_configuration_object(self):
        # GIVEN
        config = Configuration(CONFIG_FILE)
        expected = read_object_from_yaml_file(CONFIG_FILE)

        # WHEN
        extractor = PartsExtractor(config)

        # THEN
        assert extractor._cfg.to_dict() == expected

    def test_config_passed_as_dict(self):
        # GIVEN
        config_dict = Configuration(CONFIG_FILE).to_dict()
        expected = read_object_from_yaml_file(CONFIG_FILE)

        # WHEN
        extractor = PartsExtractor(config_dict)

        # THEN
        assert extractor._cfg.to_dict() == expected

    def test_config_wrong_path(self):
        # GIVEN

        # WHEN/THEN
        with pytest.raises(FileNotFoundError):
            PartsExtractor("wrong_path")

    def test_config_more_than_one_argument(self):
        # GIVEN

        # WHEN / THEN
        with pytest.raises(ValueError):
            PartsExtractor(CONFIG_FILE, "another argument")

    def test_config_wrong_type_argument(self):
        # GIVEN

        # WHEN / THEN
        with pytest.raises(TypeError):
            PartsExtractor(0)

    def test_config_no_argument(self):
        # GIVEN
        expected = Configuration()

        # WHEN
        extractor = PartsExtractor()

        # THEN
        assert expected.to_dict() == extractor._cfg.to_dict()

    # ----------------EXTRACTING FILES----------------

    def test_basic_parts_extractor(self):
        # GIVEN
        _cache.clear()
        extractor = PartsExtractor(CONFIG_FILE)

        # WHEN
        parts = extractor.extract(first_file_dir)

        # THEN
        assert parts == first_content

    def test_basic_parts_extractor_without_split(self):
        # GIVEN
        _cache.clear()
        extractor = PartsExtractor(CONFIG_FILE, split_keywords=[])

        # WHEN
        parts = extractor.extract(first_file_dir)

        # THEN
        assert parts == first_content_no_split

    def test_extract_directory(self):
        # GIVEN
        _cache.clear()
        extractor = PartsExtractor(CONFIG_FILE)

        # WHEN
        parts = extractor.extract(directory_tests)

        # THEN
        assert parts == union_content

    def test_extract_files_same_parts(self):
        # GIVEN
        _cache.clear()
        extractor = PartsExtractor(CONFIG_FILE)
        files = [first_file_dir, first_file_same_file_different_dir]
        # If it's given the same path it will just load from cache the first one

        # WHEN
        parts = extractor.extract(files)

        # THEN
        assert parts == first_content

    def test_extract_different_parts(self):
        # GIVEN
        _cache.clear()
        extractor = PartsExtractor(CONFIG_FILE)
        files = [first_file_dir, second_file_dir]

        # WHEN
        parts = extractor.extract(files)

        # THEN
        assert parts == union_content

    def test_extract_empty_directory(self):
        # GIVEN
        _cache.clear()
        extractor = PartsExtractor(CONFIG_FILE)

        # WHEN
        parts = extractor.extract(empty_dir)

        # THEN
        assert parts == []

    def test_extract_malformed_file(self):
        # GIVEN
        _cache.clear()
        extractor = PartsExtractor(CONFIG_FILE)

        # WHEN/THEN
        with pytest.raises(ParseFileError):
            extractor.extract(MALFORMED_FILE)

    def test_extract_incomplete_file(self):
        # GIVEN
        _cache.clear()
        extractor = PartsExtractor(CONFIG_FILE)

        # WHEN/THEN
        with pytest.raises(ParseFileError):
            extractor.extract(INCOMPLETE_FILE)

    # ---------------PATHS VALUES---------------

    def test_extract_wrong_type(self):
        # GIVEN
        extractor = PartsExtractor(CONFIG_FILE)
        files = 0

        # WHEN/THEN
        with pytest.raises(TypeError):
            extractor.extract(files)

    def test_extract_wrong_type_empty(self):
        # GIVEN
        extractor = PartsExtractor(CONFIG_FILE)

        # WHEN/THEN
        with pytest.raises(TypeError):
            extractor.extract()

    def test_extract_wrong_file(self):
        # GIVEN
        extractor = PartsExtractor(CONFIG_FILE)
        files = "wrong_file"

        # WHEN/THEN
        with pytest.raises(ValueError):
            extractor.extract(files)
