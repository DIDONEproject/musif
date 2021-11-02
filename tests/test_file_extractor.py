from os import path

import pytest
from musif.extract.extract import extract_files

files_dir_test = path.join("data", "arias_test")
files_dir_test1 = path.join("data", "arias_tests1")
file_dem1 = "Dem01M-O_piu-1735-Leo[1.01][0430].xml"
file_dem2 = "Dem02M-In_te-1733-Caldara[1.02][0417].xml"


class TestFilesExtractFiles:

    # ONE FILE/DIRECTORY

    def test_extract_files_one_file(self):
        # Given
        files_dir = path.join(files_dir_test, file_dem1)
        expected_files = [files_dir]

        # When
        actual_files = extract_files(files_dir)

        # Then
        assert expected_files == actual_files

    def test_extract_files_one_directory(self):
        # Given
        files_dir = files_dir_test
        expected_files = [path.join(files_dir, file_dem1), path.join(files_dir, file_dem2)]

        # When
        actual_files = extract_files(files_dir)

        # Then
        assert expected_files == actual_files

    def test_extract_files_recursive_directory(self):  # maybe too much
        # Given
        files_dir = path.join("data")
        expected_files = [path.join(files_dir_test, file_dem1), path.join(files_dir_test, file_dem2),
                          path.join(files_dir_test1, file_dem1), path.join(files_dir_test1, file_dem2),
                          path.join("data", "static", "config.yml"),
                          path.join("data", "static", "Did03M-Son_regina-1730-Sarro[1.05][0006].xml"),
                          path.join("data", "static", "expected_features.csv")]
        # When
        actual_files = extract_files(files_dir)

        # Then
        assert expected_files == actual_files

    # SEVERAL FILES/DIRECTORIES

    def test_extract_files_several_files(self):
        # Given
        files_dir = [path.join(files_dir_test, file_dem1), path.join(files_dir_test, file_dem2)]
        expected_files = files_dir

        # When
        actual_files = extract_files(files_dir)

        # Then
        assert expected_files == actual_files

    def test_extract_files_several_directories(self):
        # Given
        files_dir = [files_dir_test, files_dir_test1]
        expected_files = [path.join(files_dir_test, file_dem1), path.join(files_dir_test, file_dem2),
                          path.join(files_dir_test1, file_dem1), path.join(files_dir_test1, file_dem2)]
        # When
        actual_files = extract_files(files_dir)
        assert expected_files == actual_files

    # INVALID PATH VALUES

    def test_extract_files_incorrect_type(self):
        # Given
        with pytest.raises(ValueError):
            extract_files(0)

    def test_non_existing_file(self):  # Should fail but doesn't
        # Given
        files_dir = "doesntExists"
        # Then
        with pytest.raises(ValueError):
            extract_files(files_dir)
