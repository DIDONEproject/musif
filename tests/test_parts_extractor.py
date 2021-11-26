from os import path

import pytest

from musif.common.utils import read_object_from_yaml_file
from musif.config import Configuration
from musif.extract.exceptions import ParseFileError
from musif.extract.extract import PartsExtractor

config_file = path.join("data", "static", "config.yml")
config_default = path.join("data", "config_test", "config_default.yml")
empty_dir = path.join("data", "config_test")

directory_tests = path.join("data", "arias_tests1")
first_file_dir = path.join("data", "arias_test", "Dem01M-O_piu-1735-Leo[1.01][0430].xml")
first_file_dir_twin = path.join("data", "arias_tests1", "Dem01M-O_piu-1735-Leo[1.01][0430].xml")
second_file_dir = path.join("data", "arias_test", "Dem02M-In_te-1733-Caldara[1.02][0417].xml")

incomplete_file = path.join("data", "arias_test", "incomplete.xml")
malformed_file = path.join("data", "arias_test", "malformed.xml")

first_content = ['obI', 'obII', 'hnI', 'hnII', 'ten', 'vnI', 'vnII', 'va', 'bs']
first_content_no_split = ['ob', 'hn', 'ten', 'vnI', 'vnII', 'va', 'bs']
union_content = ['obI', 'obII', 'hnI', 'hnII', 'sop', 'ten', 'vnI', 'vnII', 'va', 'bs']


class TestPartsExtractor:

    # -----------------CONFIGURATION-----------------

    def test_config_passed_as_path(self):
        # GIVEN
        expected = read_object_from_yaml_file(config_file)

        # WHEN
        extractor = PartsExtractor(config_file)

        # THEN
        assert expected == extractor._cfg.to_dict()

    def test_config_passed_as_keywords(self):
        # GIVEN
        config_dict = Configuration(config_file).to_dict()
        expected = read_object_from_yaml_file(config_file)

        # WHEN
        extractor = PartsExtractor(**config_dict)

        # THEN
        assert extractor._cfg.to_dict() == expected

    def test_config_passed_as_configuration_object(self):
        # GIVEN
        config = Configuration(config_file)
        expected = read_object_from_yaml_file(config_file)

        # WHEN
        extractor = PartsExtractor(config)

        # THEN
        assert extractor._cfg.to_dict() == expected

    def test_config_passed_as_dict(self):
        # GIVEN
        config_dict = Configuration(config_file).to_dict()
        expected = read_object_from_yaml_file(config_file)

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
            PartsExtractor(config_file, "another argument")

    def test_config_wrong_type_argument(self):
        # GIVEN

        # WHEN / THEN
        with pytest.raises(TypeError):
            PartsExtractor(0)

    def test_config_no_argument(self):
        # GIVEN
        expected = Configuration(config_default)

        # WHEN
        extractor = PartsExtractor()

        # THEN
        assert expected.to_dict() == extractor._cfg.to_dict()

    # ----------------EXTRACTING FILES----------------

    def test_basic_parts_extractor(self):
        # GIVEN
        extractor = PartsExtractor(config_file)

        # WHEN
        parts = extractor.extract(first_file_dir)

        # THEN
        assert parts == first_content

    def test_basic_parts_extractor_without_split(self):
        # GIVEN
        extractor = PartsExtractor(config_file, split_keywords=[])

        # WHEN
        parts = extractor.extract(first_file_dir)

        # THEN
        assert parts == first_content_no_split

    def test_extract_directory(self):
        # GIVEN
        extractor = PartsExtractor(config_file)

        # WHEN
        parts = extractor.extract(directory_tests)

        # THEN
        assert parts == union_content

    def test_extract_files_same_parts(self):
        # GIVEN
        extractor = PartsExtractor(config_file)
        files = [first_file_dir, first_file_dir_twin]
        # If it's given the same path it will just load from cache the first one

        # WHEN
        parts = extractor.extract(files)

        # THEN
        assert parts == first_content

    def test_extract_different_parts(self):
        # GIVEN
        extractor = PartsExtractor(config_file)
        files = [first_file_dir, second_file_dir]

        # WHEN
        parts = extractor.extract(files)

        # THEN
        assert parts == union_content

    def test_extract_empty_directory(self):
        # GIVEN
        extractor = PartsExtractor(config_file)

        # WHEN
        parts = extractor.extract(empty_dir)

        # THEN
        assert parts == []

    def test_extract_malformed_file(self):
        # GIVEN
        extractor = PartsExtractor(config_file)

        # WHEN/THEN
        with pytest.raises(ParseFileError):
            extractor.extract(malformed_file)

    def test_extract_incomplete_file(self):
        # GIVEN
        extractor = PartsExtractor(config_file)

        # WHEN/THEN
        with pytest.raises(ParseFileError):
            extractor.extract(incomplete_file)

    # ---------------PATHS VALUES---------------

    def test_extract_wrong_type(self):
        # GIVEN
        extractor = PartsExtractor(config_file)
        files = 0

        # WHEN/THEN
        with pytest.raises(TypeError):
            extractor.extract(files)

    def test_extract_wrong_type_empty(self):
        # GIVEN
        extractor = PartsExtractor(config_file)

        # WHEN/THEN
        with pytest.raises(TypeError):
            extractor.extract()

    def test_extract_wrong_file(self):
        # GIVEN
        extractor = PartsExtractor(config_file)
        files = "wrong_file"

        # WHEN/THEN
        with pytest.raises(ValueError):
            extractor.extract(files)
