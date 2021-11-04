from os import path

import pytest

from musif.common.utils import read_object_from_yaml_file
from musif.config import Configuration

from musif import FilesValidator

config_file = path.join("data", "static", "config.yml")
test_file = path.join("data", "static", "Did03M-Son_regina-1730-Sarro[1.05][0006].xml")


class TestFilesValidator:

    # configurations tests

    def test_config_passed_as_path(self):
        # Given
        expected = read_object_from_yaml_file(config_file)

        # When
        extractor = FilesValidator(config_file)

        # Then
        assert expected == extractor._cfg.to_dict()

    def test_config_passed_as_keywords(self):
        # Given
        config_dict = Configuration(config_file).to_dict()
        expected = read_object_from_yaml_file(config_file)

        # When
        extractor = FilesValidator(**config_dict)

        # Then
        assert extractor._cfg.to_dict() == expected

    def test_config_passed_as_configuration_object(self):
        # Given
        config = Configuration(config_file)
        expected = read_object_from_yaml_file(config_file)

        # When
        extractor = FilesValidator(config)

        # Then
        assert extractor._cfg.to_dict() == expected

    def test_config_passed_as_dict(self):
        # Given
        config_dict = Configuration(config_file).to_dict()
        expected = read_object_from_yaml_file(config_file)

        # When
        extractor = FilesValidator(config_dict)

        # Then
        assert extractor._cfg.to_dict() == expected

    def test_config_more_than_one_argument(self):
        # Given

        # When / Then
        with pytest.raises(ValueError):
            FilesValidator(config_file, "another argument")

    def test_config_wrong_type_argument(self):
        # Given

        # When / Then
        with pytest.raises(TypeError):
            FilesValidator(0)

    def test_config_no_argument(self):
        # Given

        # When / Then
        with pytest.raises(ValueError):
            FilesValidator()

    # VALIDATE TESTS

    def test_validate_file(self):
        # Given
        validator = FilesValidator(config_file)

        # When
        validator.validate(test_file)
        out, err = capfd.readouterr()
        # Then
        assert out != '\nERROR:\tThat seems to be an invalid path!'

