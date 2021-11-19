import math
from os import path

from musif import FeaturesExtractor
from musif.common.utils import read_dicts_from_csv

data_static_dir = path.join("data", "static")
config_path = path.join(data_static_dir, "config_harm.yml")
data_features_dir = path.join(data_static_dir, "features")
reference_file_path = path.join(data_features_dir, "Did03M-Son_regina-1730-Sarro[1.05][0006].xml")
expected_features_file_path = path.join(data_features_dir, "expected_features.csv")


class TestFeatures:

    def test_features(self):
        # Given
        extractor = FeaturesExtractor(config_path, data_dir=data_features_dir)
        expected_data = read_dicts_from_csv(expected_features_file_path)[0]
        errors = ""

        # When
        data_df = extractor.extract()
        for col in data_df.columns:
            data_type = str(data_df.dtypes[col])
            actual_value = self._format(data_df[col].values[0], data_type)
            expected_value = self._format(expected_data.get(col), data_type)
            if actual_value != expected_value:
                errors += f'  {col}\n    Expected: {expected_value}\n    Actual:   {actual_value}\n'
        if len(errors) > 0:
            errors = f"These features are wrong:\n\n{errors}"

        # Then
        assert len(errors) == 0, errors

    def _format(self, value, data_type: str):
        try:
            if data_type == 'object':
                return str(value)
            if data_type.startswith("float"):
                return round(float(value), 3)
            if data_type.startswith("int"):
                return math.floor(float(value))
        except:
            ...
        return None
