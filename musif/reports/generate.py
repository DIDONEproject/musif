########################################################################
# GENERATION MODULE
########################################################################
# This script is ment to read the intermediate DataFrame computed by the
# FeaturesExtractor and perform several computations while grouping the data
# based on several characteristics.
# Writes the final report files as well as generates the visualisations
########################################################################
import copy
from genericpath import exists
import glob
import json
import math
import os
import shutil
import sys
import threading  # for the lock used for visualising, as matplotlib is not thread safe
from copy import deepcopy
from os import path
from typing import List, Tuple, Optional

import numpy as np
import openpyxl
import pandas as pd
from music21 import interval, note, pitch
from musif.common.utils import read_object_from_yaml_file
from musif.config import Configuration
from pandas import DataFrame
from tqdm import tqdm

from .constants import not_used_cols, rows_groups, metadata_columns, forbiden_groups
from .tasks import group_execution, factor_execution

import musif.extract.features.ambitus as ambitus
import musif.extract.features.interval as interval
import musif.extract.features.lyrics as lyrics


class FeaturesGenerator:

    def __init__(self, *args, **kwargs):
        config_data = kwargs
        self._cfg = Configuration(**config_data)
        

    def generate_reports(self, df: Tuple[DataFrame, DataFrame], num_factors: int = 0, main_results_path: str = '', parts_list: Optional[List[str]] = None) -> DataFrame:
        self.parts_list = [] if parts_list is None else parts_list
        self.global_features = df
        self.num_factors_max = num_factors
        self.main_results_path = main_results_path
        self.sorting_lists = self._read_sorting_lists()
        self._write(self.global_features)

    def _read_sorting_lists(self):
        return self._cfg.sorting_lists


    def _write(self, all_info: List[DataFrame]):
        # 2. Start the factor generation
        for factor in range(0, self.num_factors_max + 1):
            factor_execution(
                all_info, factor, self.parts_list, self.main_results_path, self.sorting_lists)