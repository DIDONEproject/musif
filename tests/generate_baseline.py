"""Regenerate the pinned regression baselines in tests/data/static/.

Run from the repository root AFTER verifying that current extraction values
are correct:

    python tests/generate_baseline.py

The committed baselines are the reference the regression tests compare
against; regenerating them silently accepts whatever the code currently
produces, so review the diff.
"""
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.conftest import (  # noqa: E402
    DIDONE_DIR,
    DIDONE_SAMPLE,
    REGRESSION_FEATURES,
    SCORES_DIR,
    STATIC_DIR,
    extraction_config,
)


def main():
    import tempfile

    from musif.extract.extract import FeaturesExtractor

    with tempfile.TemporaryDirectory() as tmp_dir:
        config = extraction_config(SCORES_DIR, tmp_dir)
        df = FeaturesExtractor(config).extract()
    destination = STATIC_DIR / "expected_features.csv"
    df.to_csv(destination, index=False)
    print(f"written {destination} ({df.shape[0]} rows x {df.shape[1]} columns)")

    xml = DIDONE_DIR / "xml" / f"{DIDONE_SAMPLE}.xml"
    mscx = DIDONE_DIR / "musescore" / f"{DIDONE_SAMPLE}.mscx"
    if xml.exists() and mscx.exists():
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            (tmp / "xml").mkdir()
            (tmp / "musescore").mkdir()
            (tmp / "xml" / xml.name).write_bytes(xml.read_bytes())
            (tmp / "musescore" / mscx.name).write_bytes(mscx.read_bytes())
            config = extraction_config(
                tmp / "xml",
                tmp,
                musescore_dir=str(tmp / "musescore"),
                features=REGRESSION_FEATURES + ["harmony", "scale_relative"],
            )
            df = FeaturesExtractor(config).extract()
        destination = STATIC_DIR / "expected_didone_features.csv"
        df.to_csv(destination, index=False)
        print(f"written {destination} ({df.shape[0]} rows x {df.shape[1]} columns)")
    else:
        print(f"DIDONE corpus not found at {DIDONE_DIR}; skipped its baseline")


if __name__ == "__main__":
    main()
