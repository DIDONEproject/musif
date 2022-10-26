from os import path

import pytest

from musif.common.utils import read_object_from_yaml_file
from musif.config import Configuration
from musif.extract.extract import FilesValidator

from .constants import BASE_PATH, MALFORMED_FILE, INCOMPLETE_FILE

config_file = path.join(BASE_PATH, "config_test", "config.yml")
config_file_parallel = path.join(BASE_PATH, "config_test", "config_parallel.yml")
test_file = path.join(BASE_PATH, "static", "Did03M-Son_regina-1730-Sarro[1.05][0006].xml")

class TestFilesValidator:
    # configurations tests
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

    def test_config_passed_with_override(self):
        # Given
        expected = read_object_from_yaml_file(config_file_parallel)

        # When
        extractor = FilesValidator(config_file, parallel=True)

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
        with pytest.raises(FileNotFoundError):
            FilesValidator()

    # MALFORMED FILES TESTS

    def test_validate_file(self, capsys):
        # Given
        validator = FilesValidator(config_file)

        # When
        validator.validate(test_file)
        out, err = capsys.readouterr()
        # Then
        assert err.count('\nERROR:\tThat seems to be an invalid path!') == 0

    def test_validate_malformed_file(self, capsys):
        # Given
        validator = FilesValidator(config_file)

        # When
        validator.validate(MALFORMED_FILE)
        out, err = capsys.readouterr()
        # Then
        assert err.count('\nERROR:\tThat seems to be an invalid path!') == 1

    def test_validate_malformed_file_with_correct_file(self, capsys):
        # Given
        validator = FilesValidator(config_file)

        # When
        validator.validate([MALFORMED_FILE, test_file])
        out, err = capsys.readouterr()

        # Then
        assert err.count('\nERROR:\tThat seems to be an invalid path!') == 1

    def test_validate_two_malformed_files(self, capsys):
        # Given
        validator = FilesValidator(config_file)

        # When
        validator.validate([MALFORMED_FILE, MALFORMED_FILE])
        out, err = capsys.readouterr()
        # Then
        assert err.count('\nERROR:\tThat seems to be an invalid path!') == 2

    # INCOMPLETE FILES TESTS

    def test_validate_incompleted_file(self, capsys):
        # Given
        validator = FilesValidator(config_file)

        # When
        validator.validate(INCOMPLETE_FILE)
        out, err = capsys.readouterr()
        # Then
        assert err.count('\nERROR:\tThat seems to be an invalid path!') == 1

    def test_validate_incompleted_file_with_correct_file(self, capsys):
        # Given
        validator = FilesValidator(config_file)

        # When
        validator.validate([INCOMPLETE_FILE, test_file])
        out, err = capsys.readouterr()
        # Then
        assert err.count('\nERROR:\tThat seems to be an invalid path!') == 1

    def test_validate_two_incompleted_files(self, capsys):
        # Given
        validator = FilesValidator(config_file)

        # When
        validator.validate([INCOMPLETE_FILE, INCOMPLETE_FILE])
        out, err = capsys.readouterr()
        # Then
        assert err.count('\nERROR:\tThat seems to be an invalid path!') == 2

    # PARALLEL MALFORMED TEST

    # @pytest.mark.parallel_malformed
    # def test_validate_parallel_file(self, capsys):
    #     # Given
    #     config = Configuration(config_file)
    #     config.parallel = True
    #     validator = FilesValidator(config)
    #     musicxml = extract_files(test_file)
    #
    #     # When
    #     validator.validate(musicxml)
    #     out, err = capsys.readouterr()
    #
    #     # Then
    #     assert err.count('\nERROR:\tThat seems to be an invalid path!') == 0
    #
    # @pytest.mark.parallel_malformed
    # def test_validate_parallel_malformed_file(self, capsys):
    #     # Given
    #     config = Configuration(config_file)
    #     config.parallel = True
    #     validator = FilesValidator(config)
    #
    #     # When
    #     validator.validate(malformed_file)
    #     out, err = capsys.readouterr()
    #     # Then
    #     assert err == '\nERROR:\tThat seems to be an invalid path!'  # out.count('\nERROR:\tThat seems to be an
    #     # invalid path!') == 1
    #
    # @pytest.mark.parallel_malformed
    # def test_validate_parallel_malformed_file_with_correct_file(self, capsys):
    #     # Given
    #     config = Configuration(config_file)
    #     config.parallel = True
    #     validator = FilesValidator(config)
    #
    #     # When
    #     validator.validate([malformed_file, test_file])
    #     out, err = capsys.readouterr()
    #     # Then
    #     assert err.count('\nERROR:\tThat seems to be an invalid path!') == 1
    #
    # @pytest.mark.parallel_malformed
    # def test_validate_parallel_two_malformed_files(self, capsys):
    #     # Given
    #     config = Configuration(config_file)
    #     config.parallel = True
    #     validator = FilesValidator(config)
    #
    #     # When
    #     validator.validate([malformed_file, malformed_file])
    #     out, err = capsys.readouterr()
    #     # Then
    #     assert err.count('\nERROR:\tThat seems to be an invalid path!') == 2
