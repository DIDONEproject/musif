from os import path

import pytest
from musif.extract.extract import extract_files
from .constants import BASE_PATH

files_dir_test = path.join(BASE_PATH, "arias_test")
files_dir_test1 = path.join(BASE_PATH, "arias_tests1")
files_dir_test_type = path.join(BASE_PATH, "static")

file_dem1_test = path.join(files_dir_test, "Dem01M-O_piu-1735-Leo[1.01][0430].xml")
file_dem2_test = path.join(files_dir_test, "Dem02M-In_te-1733-Caldara[1.02][0417].xml")

file_dem1_test1 = path.join(files_dir_test1, "Dem01M-O_piu-1735-Leo[1.01][0430].xml")
file_dem2_test1 = path.join(files_dir_test1, "Dem02M-In_te-1733-Caldara[1.02][0417].xml")

file_dem3 = path.join(files_dir_test_type, "Did03M-Son_regina-1730-Sarro[1.05][0006].xml")


class TestExtractFiles:

    # ONE FILE/DIRECTORY

    def test_extract_files_one_file(self):
        # Given
        files_dir = file_dem1_test
        expected_files = [files_dir]

        # When
        actual_files = extract_files(files_dir)

        # Then
        assert expected_files == actual_files

    def test_extract_files_one_directory(self):
        # Given
        files_dir = files_dir_test
        expected_files = [file_dem1_test, file_dem2_test]

        # When
        actual_files = extract_files(files_dir)

        # Then
        assert expected_files == actual_files

    def test_extract_files_recursive_directory(self):
        # Given
        files_dir = BASE_PATH
        expected_files = []  # It search for .xml files, It's not recursive

        # When
        actual_files = extract_files(files_dir)

        # Then
        assert expected_files == actual_files

    # SEVERAL FILES/DIRECTORIES

    def test_extract_files_several_files(self):
        # Given
        files_dir = [file_dem1_test, file_dem2_test]
        expected_files = files_dir

        # When
        actual_files = extract_files(files_dir)

        # Then
        assert expected_files == actual_files

    def test_extract_files_several_directories(self):
        # Given
        files_dir = [files_dir_test, files_dir_test1]
        expected_files = [file_dem1_test, file_dem2_test, file_dem1_test1, file_dem2_test1]

        # When
        actual_files = extract_files(files_dir)

        # then
        assert expected_files == actual_files

    # INVALID PATH VALUES

    def test_extract_files_incorrect_type(self):
        # Given
        with pytest.raises(TypeError):
            extract_files(0)

    def test_extract_non_existing_file(self):
        # Given
        files_dir = "doesntExists"

        # Then
        with pytest.raises(ValueError):
            extract_files(files_dir)

    # TYPE OF FILE

    def test_extract_only_good_files_directory(self):
        # Given
        files_dir = files_dir_test_type
        expected_files = [file_dem3]
        # When
        actual_files = extract_files(files_dir)
        # Then
        assert expected_files == actual_files

    def test_extract_not_bad_file(self):
        # Given
        files_dir = path.join(files_dir_test_type, "config.yml")
        expected_files = []
        # When
        actual_files = extract_files(files_dir)
        # Then
        assert expected_files == actual_files

    def test_extract_only_good_files_list(self):
        # Given
        files_dir = [path.join(files_dir_test_type, "config.yml"), file_dem3]
        expected_files = [file_dem3]
        # When
        actual_files = extract_files(files_dir)
        # Then
        assert expected_files == actual_files
