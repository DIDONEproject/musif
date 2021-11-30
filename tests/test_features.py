import math
from os import path

from musif.extract.features.prefix import get_part_prefix

from musif import FeaturesExtractor
from musif.common.utils import read_dicts_from_csv

data_static_dir = path.join("data", "static")
config_path = path.join(data_static_dir, "config.yml")
data_features_dir = path.join(data_static_dir, "features")
reference_file_path = path.join(data_features_dir, "Did03M-Son_regina-1730-Sarro[1.05][0006].xml")
expected_features_file_path = path.join(data_features_dir, "expected_features.csv")


class TestFeatures:

    def test_features(self):
        # Given
        parts_filter = ["vnI", "vnII", "va", "bs", "sop", "ten", "alt", "bar", "bass", "bbar"]
        extractor = FeaturesExtractor(config_path, data_dir=data_features_dir, parts_filter=parts_filter)
        expected_data = read_dicts_from_csv(expected_features_file_path)[0]
        errors = ""

        # When
        data_df = extractor.extract()
        cols_to_remove = []
        for col in data_df.columns:
            if not col.startswith(get_part_prefix("")):
                continue
            if not col.startswith(get_part_prefix("vnI")) and not col.startswith(get_part_prefix("sop")):
                cols_to_remove.append(col)
        data_df.drop(cols_to_remove, axis=1, inplace=True)
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
                return str(value) if value is not None else ""
            if data_type.startswith("float"):
                return round(float(value), 3) if value is not None else 0.0
            if data_type.startswith("int"):
                return math.floor(float(value)) if value is not None else 0
        except:
            ...
        return None
