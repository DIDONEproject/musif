from musif import FeaturesExtractor
from musif.common.utils import read_dicts_from_csv


class TestFeatures:

    def test_features(self):
        # Given
        extractor = FeaturesExtractor("data/static/config.yml")
        file_to_process = "data/static/Did03M-Son_regina-1730-Sarro[1.05][0006].xml"
        expected_data = read_dicts_from_csv("data/static/expected_features.csv")[0]
        errors = ""

        # When
        data_df = extractor.extract(file_to_process)
        for col in data_df.columns:
            actual_value = data_df[col].values[0]
            expected_value = expected_data.get(col)
            if actual_value != expected_value:
                errors += f'  {col}\n    Expected: {expected_value}\n    Actual:   {actual_value}\n'
        if len(errors) > 0:
            errors = f"These features are wrong:\n\n{errors}"

        # Then
        assert len(errors) == 0, errors
