import os
import warnings
from pathlib import Path

import pandas as pd
import pytest

warnings.filterwarnings("ignore")

TESTS_DIR = Path(__file__).parent
SCORES_DIR = TESTS_DIR / "data" / "scores"
STATIC_DIR = TESTS_DIR / "data" / "static"

# Feature modules that need neither MuseScore analyses nor music21's native
# feature set (whose values drift across music21 versions).
REGRESSION_FEATURES = [
    "core",
    "ambitus",
    "melody",
    "tempo",
    "density",
    "texture",
    "lyrics",
    "scale",
    "key",
    "dynamics",
    "rhythm",
]

# Optional real-corpus regression: point MUSIF_DIDONE_DIR at a directory with
# xml/ and musescore/ subfolders (defaults to the DIDONE corpus layout).
DIDONE_DIR = Path(os.environ.get("MUSIF_DIDONE_DIR", "~/Documents/Corpus_DIDONE")).expanduser()
DIDONE_SAMPLE = "Adr01M-Dal_labro-1734-Pergolesi[1.01][2604]"


def extraction_config(data_dir, tmp_dir, **overrides):
    config = {
        "data_dir": str(data_dir),
        "parallel": 1,
        "basic_modules": ["scoring", "file_name_generic"],
        "features": list(REGRESSION_FEATURES),
        "output_dir": str(tmp_dir),
        "log": {
            "log_file": str(Path(tmp_dir) / "musif.log"),
            "file_log_level": "ERROR",
            "console_log_level": "ERROR",
        },
    }
    config.update(overrides)
    return config


@pytest.fixture(scope="session")
def extracted_features(tmp_path_factory) -> pd.DataFrame:
    """One extraction of the committed test scores, shared by the suite."""
    from musif.extract.extract import FeaturesExtractor

    tmp_dir = tmp_path_factory.mktemp("extraction")
    config = extraction_config(SCORES_DIR, tmp_dir)
    return FeaturesExtractor(config).extract()


@pytest.fixture(scope="session")
def expected_features() -> pd.DataFrame:
    """The pinned baseline (regenerate with tests/generate_baseline.py)."""
    return pd.read_csv(STATIC_DIR / "expected_features.csv", low_memory=False)


@pytest.fixture(scope="session")
def didone_features(tmp_path_factory) -> pd.DataFrame:
    """Extraction of one real DIDONE aria, harmony included. Skipped when the
    corpus is not available locally."""
    xml = DIDONE_DIR / "xml" / f"{DIDONE_SAMPLE}.xml"
    mscx = DIDONE_DIR / "musescore" / f"{DIDONE_SAMPLE}.mscx"
    if not (xml.exists() and mscx.exists()):
        pytest.skip(f"DIDONE corpus not available at {DIDONE_DIR}")
    from musif.extract.extract import FeaturesExtractor

    tmp_dir = tmp_path_factory.mktemp("didone")
    data_dir = tmp_dir / "xml"
    mscore_dir = tmp_dir / "musescore"
    data_dir.mkdir()
    mscore_dir.mkdir()
    (data_dir / xml.name).write_bytes(xml.read_bytes())
    (mscore_dir / mscx.name).write_bytes(mscx.read_bytes())
    config = extraction_config(
        data_dir,
        tmp_dir,
        musescore_dir=str(mscore_dir),
        features=REGRESSION_FEATURES + ["harmony", "scale_relative"],
    )
    return FeaturesExtractor(config).extract()
