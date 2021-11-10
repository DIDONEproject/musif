from os import path

import pytest
from musif.extract.extract import parse_musicxml_file

test_file = path.join("data", "static", "Did03M-Son_regina-1730-Sarro[1.05][0006].xml")
config_file = path.join("data", "static", "config.yml")


class TestParseMusicXMLFile:

    def test(self):
        # GIVEN
        split_keywords= ["woodwind
  - brass
  - wind

        # WHEN
        parse_musicxml_file()

        # THEN
        assert True

    # TODO comprobar cache

    # TODO split keywords