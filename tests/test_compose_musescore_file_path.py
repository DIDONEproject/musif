from os import path

import pytest

from musif.extract.extract import compose_musescore_file_path

test_file = path.join("directory", "file.xml")
expected_test_file = "file.mscx"
test_different_directory = "musescore_direcory"
long_directory_path = path.join("first", "second", "directory")
different_path_lines_directory = "first/second\directory"


class TestComposeMusescoreFilePath:

    def test_basic_compose_musescore_file_path(self):
        # GIVEN
        expected = path.join("directory", expected_test_file)

        # WHEN
        path_name = compose_musescore_file_path(test_file, None)

        # THEN
        assert path_name == expected

    def test_another_directory(self):
        # GIVEN
        expected = path.join(test_different_directory, expected_test_file)

        # WHEN
        path_name = compose_musescore_file_path(test_file, test_different_directory)

        # THEN
        assert path_name == expected

    def test_another_directory_long_path(self):
        # GIVEN
        expected = path.join(long_directory_path, expected_test_file)

        # WHEN
        path_name = compose_musescore_file_path(test_file, long_directory_path)

        # THEN
        assert path_name == expected

    def test_another_directory_diff_lines_path(self):
        # GIVEN
        expected = path.join(different_path_lines_directory, expected_test_file)

        # WHEN
        path_name = compose_musescore_file_path(test_file, different_path_lines_directory)

        # THEN
        assert path_name == expected

    def test_file_wrong_extention(self):
        # WHEN/THEN
        with pytest.raises(ValueError):
            compose_musescore_file_path("file.txt", None)

    def test_file_without_extention(self):
        # WHEN/THEN
        with pytest.raises(ValueError):
            compose_musescore_file_path("file", None)

    def test_bad_extention(self):
        with pytest.raises(ValueError):
            compose_musescore_file_path("file.xml.txt", None)

    def test_weird_characters(self):
        # GIVEN
        expected = "píùñ.mscx"

        # WHEN
        path_name = compose_musescore_file_path("píùñ.xml", None)

        # THEN
        assert path_name == expected
