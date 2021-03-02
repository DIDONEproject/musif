import glob
import math
from concurrent.futures import as_completed
from concurrent.futures.process import ProcessPoolExecutor
from copy import deepcopy
from os import path
from typing import Dict, List, Optional

from tqdm import tqdm

from musif import musicxml
from musif.config import cpu_workers, default_sequential, read_logger


class ScoreInfo:
    def __init__(
        self,
        id: str,
        file_name: str,
        opera: str,
        label: str,
        aria: str,
        composer: str,
        year: str,
        decade: str,
        act: str,
        scene: str,
        act_and_scene: str,
        city: str,
        country: str,
        form: str,
        role: str,
        role_type: str,
        gender: str,
        old_clef: str,
        Scoring: str,
        SoundScoring: str,
        Instrumentation: str,
        Voices: str,
        FamilyScoring: str,
        FamilyInstrumentation: str,
        key: str,
        mode: str,
        key_signature: str,
        tempo: str,
        time_signature: str,
        to_musicxml_part: Dict[str, str],
    ):
        self._id = id
        self._file_name = file_name
        self._opera = opera
        self._label = label
        self._aria = aria
        self._composer = composer
        self._year = year
        self._decade = decade
        self._act = act
        self._scene = scene
        self._act_and_scene = act_and_scene
        self._city = city
        self._country = country
        self._form = form
        self._role = role
        self._role_type = role_type
        self._gender = gender
        self._old_clef = old_clef
        self._scoring = Scoring
        self._sound_scoring = SoundScoring
        self._instrumentation = Instrumentation
        self._voices = Voices
        self._family_scoring = FamilyScoring
        self._family_instrumentation = FamilyInstrumentation
        self._key = key
        self._mode = mode
        self._key_signature = key_signature
        self._tempo = tempo
        self._time_signature = time_signature
        self._to_musicxml_part = deepcopy(to_musicxml_part)
        self._to_musif_part = {value: key for key, value in self._to_musicxml_part.items()}

    @property
    def id(self) -> str:
        return self._id

    @property
    def file_name(self) -> str:
        return self._file_name

    @property
    def opera(self) -> str:
        return self._opera

    @property
    def label(self) -> str:
        return self._label

    @property
    def aria(self) -> str:
        return self._aria

    @property
    def composer(self) -> str:
        return self._composer

    @property
    def year(self) -> str:
        return self._year

    @property
    def decade(self) -> str:
        return self._decade

    @property
    def act(self) -> str:
        return self._act

    @property
    def scene(self) -> str:
        return self._scene

    @property
    def act_and_scene(self) -> str:
        return self._act_and_scene

    @property
    def city(self) -> str:
        return self._city

    @property
    def country(self) -> str:
        return self._country

    @property
    def form(self) -> str:
        return self._form

    @property
    def role(self) -> str:
        return self._role

    @property
    def role_type(self) -> str:
        return self._role_type

    @property
    def gender(self) -> str:
        return self._gender

    @property
    def old_clef(self) -> str:
        return self._old_clef

    @property
    def scoring(self) -> str:
        return self._scoring

    @property
    def sound_scoring(self) -> str:
        return self._sound_scoring

    @property
    def instrumentation(self) -> str:
        return self._instrumentation

    @property
    def voices(self) -> str:
        return self._voices

    @property
    def family_scoring(self) -> str:
        return self._family_scoring

    @property
    def family_instrumentation(self) -> str:
        return self._family_instrumentation

    @property
    def key(self) -> str:
        return self._key

    @property
    def mode(self) -> str:
        return self._mode

    @property
    def key_signature(self) -> str:
        return self._key_signature

    @property
    def tempo(self) -> str:
        return self._tempo

    @property
    def time_signature(self) -> str:
        return self._time_signature

    def to_musicxml_part(self, musif_part: str) -> Optional[str]:
        return self._to_musicxml_part.get(musif_part)

    def to_musiF_part(self, musicxml_part: str) -> Optional[str]:
        return self._to_musif_part[musicxml_part]


class ScoreInfoExtractor:
    def __init__(self, sequential: bool = None):
        self._sequential = sequential or default_sequential

    def from_dir(self, musicxml_scores_dir: str) -> List[ScoreInfo]:
        read_logger.info(f"Extracting basic info from directory '{musicxml_scores_dir}'")
        musicxml_files = glob.glob(path.join(musicxml_scores_dir, f"*.{musicxml.FILE_EXTENSION}"))
        read_logger.info(f"{len(musicxml_files)} musicxml scores found")
        tqdm_options = {'total': len(musicxml_files), 'unit': 'it', 'unit_scale': True, 'leave': True}
        if self._sequential:
            normalized_scores = [self.from_file(musicxml_file) for musicxml_file in tqdm(musicxml_files, **tqdm_options)]
        else:
            executor = ProcessPoolExecutor(max_workers=cpu_workers)
            futures = [executor.submit(self.from_file, musicxml_file) for musicxml_file in musicxml_files]
            normalized_scores = [task.result() for task in tqdm(as_completed(futures), **tqdm_options)]
        read_logger.info(f"Finished extraction of basic info from directory '{musicxml_scores_dir}'")
        return normalized_scores

    def from_file(self, musicxml_file: str) -> ScoreInfo:
        read_logger.debug(f"Normalizing file {musicxml_file}")
        musicxml_score = musicxml.parse(musicxml_file)
        return self.from_score(musicxml_score, musicxml_file)

    def from_score(self, musicxml_score: musicxml.Score, musicxml_file: str) -> ScoreInfo:
        data = {}
        file_name = path.basename(musicxml_file)[: -len(musicxml.FILE_EXTENSION) - 1]
        # data["file_name"] = file_name
        # data.update(self._extract_variables_from_file_name(file_name))
        # musicxml.split_wind_layers(musicxml_score)
        # data.update(get_general_features(data["id"]))
        # scoring_variables, abbreviation_to_musicxml_part = get_scoring_features(musicxml_score)
        # data.update(scoring_variables)
        # data["musicxml_mapping"] = abbreviation_to_musicxml_part
        # musicxml_parts = [abbreviation_to_musicxml_part[abbreviation] for abbreviation in data["Scoring"]]
        # general_variables, _ = musicxml.get_general_xml_variables(musicxml_score, musicxml_parts)
        # data.update(general_variables)
        #
        # musicxml.split_wind_layers(musicxml_score)
        # file_name = path.basename(musicxml_file)[: -len(musicxml.FILE_EXTENSION) - 1]
        # data["file_name"] = file_name
        # data["modulations"] = []  # [('I', 0), ('V', 30), ...]
        # scoring_variables, abbreviation_to_musicxml_part = get_scoring(musicxml_score)
        # data.update(scoring_variables)
        # data["musicxml_mapping"] = abbreviation_to_musicxml_part
        # musicxml_parts = [abbreviation_to_musicxml_part[abbreviation] for abbreviation in data["part_scoring"]]
        # general_variables, _ = musicxml.get_general_xml_variables(musicxml_score, musicxml_parts)
        # data.update(general_variables)

        return ScoreInfo(**data)

    @staticmethod
    def _extract_variables_from_file_name(file_name):
        """
        get variables from file_name
        returns a dictionary so it can be easily input in a df
        """

        opera_title = file_name[0:3]
        label = file_name.split("-", 2)[0]
        aria_id = file_name.split("[")[-1].split("]")[0]
        aria_title = file_name.split("-", 2)[1]
        composer = file_name.split("-", -1)[-1].split("[", 2)[0]
        year = file_name.split("-", -2)[-2]
        decade = str(int(year) // 100) + str(math.floor(int(year) % 100 / 10) * 10) + "s"
        act = file_name.split("[", 1)[-1].split(".", 1)[0]
        scene = file_name.split(".", 1)[-1].split("]", 1)[0]

        return {
            "opera": opera_title,
            "label": label,
            "id": aria_id,
            "aria": aria_title,
            "composer": composer,
            "year": year,
            "decade": decade,
            "act": act,
            "scene": scene,
            "act_and_scene": act + scene,
        }
