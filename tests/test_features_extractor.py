from os import path

import pytest

from musif.config import Configuration
from musif.extract.exceptions import ParseFileError
from musif.extract.extract import FeaturesExtractor

from musif.common.utils import read_object_from_yaml_file

config_file = path.join("data", "static", "config.yml")
config_default = path.join("data", "config_test", "config_default.yml")
test_file = path.join("data", "static", "features", "Did03M-Son_regina-1730-Sarro[1.05][0006].xml")
data_dir = path.join("data", "static", "features")

test_several_files = path.join("data", "arias_tests1")
test_several_files_different = path.join(test_several_files, "Dem01M-O_piu-1735-Leo[1.01][0430].xml")

test_malformed = path.join("data", "arias_test", "malformed.xml")
test_incomplete = path.join("data", "arias_test", "incomplete.xml")


class TestFeaturesExtractor:

    # -----------------CONFIGURATION-----------------

    def test_config_passed_as_path(self):
        # GIVEN
        expected = read_object_from_yaml_file(config_file)

        # WHEN
        extractor = FeaturesExtractor(config_file)

        # THEN
        assert expected == extractor._cfg.to_dict()

    def test_config_passed_as_keywords(self):
        # GIVEN
        config_dict = Configuration(config_file).to_dict()
        expected = read_object_from_yaml_file(config_file)

        # WHEN
        extractor = FeaturesExtractor(**config_dict)

        # THEN
        assert extractor._cfg.to_dict() == expected

    def test_config_passed_as_configuration_object(self):
        # GIVEN
        config = Configuration(config_file)
        expected = read_object_from_yaml_file(config_file)

        # WHEN
        extractor = FeaturesExtractor(config)

        # THEN
        assert extractor._cfg.to_dict() == expected

    def test_config_passed_as_dict(self):
        # GIVEN
        config_dict = Configuration(config_file).to_dict()
        expected = read_object_from_yaml_file(config_file)

        # WHEN
        extractor = FeaturesExtractor(config_dict)

        # THEN
        assert extractor._cfg.to_dict() == expected

    def test_config_wrong_path(self):
        # GIVEN

        # WHEN/THEN
        with pytest.raises(FileNotFoundError):
            FeaturesExtractor("wrong_path")

    def test_config_more_than_one_argument(self):
        # GIVEN

        # WHEN / THEN
        with pytest.raises(ValueError):
            FeaturesExtractor(config_file, "another argument")

    def test_config_wrong_type_argument(self):
        # GIVEN

        # WHEN / THEN
        with pytest.raises(TypeError):
            FeaturesExtractor(0)

    def test_config_no_argument(self):
        # GIVEN
        expected = Configuration()  # config_default

        # WHEN
        extractor = FeaturesExtractor()

        # THEN
        assert expected.to_dict() == extractor._cfg.to_dict()

    # ---------------EXTRACTOR---------------

    def test_basic_extract(self):
        # GIVEN
        extractor = FeaturesExtractor(config_file, data_dir=data_dir)

        # WHEN
        resul = extractor.extract()

        # THEN
        assert resul is not None
    
    def test_num_features(self):
        # GIVEN
        featu = ["file_name"]
        extractor = FeaturesExtractor(config_file, features=featu, data_dir=data_dir)

        # WHEN
        resul = extractor.extract()

        # THEN
        assert len(resul.columns) == 9

    def test_missing_module(self):
        # GIVEN
        featu = ["interval"]
        extractor = FeaturesExtractor(config_file, features=featu, data_dir=data_dir)

        # WHEN/THEN
        with pytest.raises(KeyError):
            extractor.extract()

    def test_missing_module_order(self):
        # GIVEN
        featu = ["interval", "core"]
        extractor = FeaturesExtractor(config_file, features=featu, data_dir=data_dir)

        # WHEN/THEN
        with pytest.raises(KeyError):
            extractor.extract()

    # ------------------------FILES PATHS------------------------

    def test_several_files_directory(self):
        # GIVEN
        extractor = FeaturesExtractor(config_file, data_dir=test_several_files)

        # WHEN
        resul = extractor.extract()

        # THEN
        assert resul is not None

    def test_no_file(self):
        # GIVEN
        extractor = FeaturesExtractor(config_file, data_dir=[])

        # WHEN
        resul = extractor.extract()

        # THEN
        assert len(resul.columns) == 0

    def test_several_files_paths(self):
        # GIVEN
        extractor = FeaturesExtractor(config_file, data_dir=[test_file, test_several_files_different])

        # WHEN
        resul = extractor.extract()

        # THEN
        assert resul is not None

    def test_malformed(self):
        # WHEN/THEN
        with pytest.raises(ParseFileError):
            FeaturesExtractor(config_file, data_dir=test_malformed).extract()

    def test_incomplete(self):
        # WHEN/THEN
        with pytest.raises(ParseFileError):
            FeaturesExtractor(config_file, data_dir=test_incomplete).extract()
