import pytest
from musif.config import Configuration
from musif.extract.extract import extract


class TestFilesExtractor:

    def test_extract(self):
        # Given
        files_dir = "../arias/Dem01M-O_piu-1735-Leo[1.01][0430].xml"
        expected_files = extract(files_dir)  # find_files_in_dir(files_dir)

        # When
        actual_files = extract(files_dir)

        # Then
        assert expected_files == actual_files
