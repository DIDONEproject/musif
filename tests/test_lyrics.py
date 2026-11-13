"""Unit tests for the sung-text features."""
from music21.key import Key
from music21.note import Lyric, Note

from musif.extract.features.lyrics.handler import get_voice_reg
from musif.musicxml.common import _get_lyrics_in_notes


class TestSyllables:
    def test_melisma_marker_is_not_a_syllable(self):
        # MuseScore closes every melisma line with a lyric that has no text
        sung = Note("C5")
        sung.addLyric("la")
        end_of_melisma = Note("D5")
        end_of_melisma.lyrics.append(Lyric(text=""))
        plain = Note("E5")
        assert _get_lyrics_in_notes([sung, end_of_melisma, plain]) == ["la"]


class TestVoiceRegister:
    NOTES = ["C5", "E5", "G5"]  # mean pitch: 3.67 semitones above C5

    def _register(self, pitches, key):
        return get_voice_reg([Note(p) for p in pitches], Key(key))

    def test_distance_to_the_nearest_tonic(self):
        assert abs(self._register(self.NOTES, "C") - 11 / 3) < 1e-9
        # in G the nearest tonic is the G above the centre of the part
        assert abs(self._register(self.NOTES, "G") + 10 / 3) < 1e-9

    def test_last_note_does_not_matter(self):
        # the reference used to be the part's own last note
        assert self._register(["G5", "E5", "C5"], "C") == self._register(self.NOTES, "C")

    def test_no_notes_or_no_key(self):
        value = get_voice_reg([], Key("C"))
        assert value != value
        value = get_voice_reg([Note("C5")], None)
        assert value != value
