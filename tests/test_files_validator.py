import pytest

from musif.config import Configuration

from musif import FilesValidator


class TestFilesValidator:

    def test_config_passed_as_path(self):
        # Given
        extractor = FilesValidator("data/static/config.yml")

        # When

        # Then
        assert False

    def test_config_more_than_one_argument(self):
        # Given

        # When / Then
        with pytest.raises(ValueError):
            FilesValidator("data/static/config.yml", "another argument")

    def test_config_passed_as_keywords(self):
        # Given
        config_dict = Configuration("data/static/config.yml").to_dict()
        extractor = FilesValidator(**config_dict)

        # When

        # Then
        assert False

    def test_config_passed_as_configuration_object(self):
        # Given
        config = Configuration("data/static/config.yml")
        extractor = FilesValidator(config)

        # When

        # Then
        assert False

    def test_config_passed_as_dict(self):
        # Given
        config_dict = Configuration("data/static/config.yml").to_dict()
        extractor = FilesValidator(config_dict)

        # When

        # Then
        assert False
