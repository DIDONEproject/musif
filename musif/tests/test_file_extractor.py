import pytest
from musif.extract.extract import extract_files


class TestFilesextract_filesor:

    # ONE FILE/DIRECTORY

    def test_extract_files_one_file(self):
        # Given
        files_dir = "/data/arias_test/Dem01M-O_piu-1735-Leo[1.01][0430].xml"
        expected_files = ["/data/arias_test/Dem01M-O_piu-1735-Leo[1.01][0430].xml"]  # find_files_in_dir(files_dir)

        # When
        actual_files = extract_files(files_dir)

        # Then
        assert expected_files == actual_files

    def test_extract_files_one_directory(self):
        # Given
        files_dir = "data/arias_test"
        expected_files = ["data/arias_test"]  # find_files_in_dir(files_dir)

        # When
        actual_files = extract_files(files_dir)

        # Then
        assert expected_files == actual_files

    # SEVERAL FILES/DIRECTORIES

    def test_extract_files_several_files(self):
        # Given
        files_dir = ["/data/arias_test/Dem01M-O_piu-1735-Leo[1.01][0430].xml",
                     "/data/arias_test/Dem02M-In_te-1733-Caldara[1.02][0417].xml"]
        expected_files = files_dir

        # When
        actual_files = extract_files(files_dir)

        # Then
        assert expected_files == actual_files

    def test_extract_files_several_directories(self):  # this maybe shouldn't be possible
        # Given
        files_dir = ["/data/arias_test", "/data/arias_test1"]
        expected_files = files_dir
        # When
        actual_files = extract_files(files_dir)

        # Then
        assert expected_files == actual_files

    # INVALID PATH VALUES

    def test_extract_files_incorrect_type(self):
        # Given
        with pytest.raises(ValueError):
            extract_files(0)
