import os

from musif import FeaturesExtractor
from musif.reports.generate import FeaturesGenerator

if __name__ == "__main__":
    parts = ["vnI","obI"]
    # parts = None

    arias_path="./arias/"
    arias_path="../Corpus/corpus_filtrado"
    # arias_path="../Corpus/corpus_filtrado/fallos"
    # arias_path="../Corpus/corpus_filtrado/fallos/wrong_chords"
    # arias_path="../Corpus/corpus_filtrado/fallos/check"
