"""
from root of the git repo, run with: python -m tests.test_of_test 

POSSIBLE VALUES 

`info`, `warn`, `err`, `crit`, `na`

Only for `minval` and `maxval`: numbers (anything if not appliable)

"""
import pandas as pd
from pandas.api.types import is_integer_dtype, is_float_dtype, is_string_dtype, is_bool_dtype
import numpy as np
import musif.logs
from joblib import Parallel, delayed

musif.logs.logger().setLevel(musif.logs.LEVEL_INFO)
rules = pd.read_csv('tests/test_unit_rules.csv', header=0, index_col=0)
data = pd.read_csv('martiser/extraction_01_08_22_total_alldata.csv', header=0, index_col=False)

def checktype(df, t):
    """
    check that all columns in `df` are of type `t`

    returns True or False
    """
    if t == 'str':
        return all(is_string_dtype(x[col]) for col in x.columns)
    elif t == 'float':
        return all(is_float_dtype(x[col]) for col in x.columns)
    elif t == 'int':
        return all(is_integer_dtype(x[col]) for col in x.columns)
    elif t == 'bool':
        return all(is_bool_dtype(x[col]) for col in x.columns)


check_functions = {
        'any_na': lambda x, y: x.isna().any()[0],
        'all_na': lambda x, y: x.isna().all()[0],
        'any_0': lambda x, y: (x == 0).any()[0],
        'all_0': lambda x, y: (x == 0).all()[0],
        'minval': lambda x, y: (x.select_dtypes([int, float]) < float(y)).any()[0],
        'maxval': lambda x, y: (x.select_dtypes([int, float]) > float(y)).any()[0],
        'data_type': checktype
        }

def check_rules_column(regex, rules, data, check_functions):
    # getting the portion of data that must be checked
    matched_data = data.filter(regex=regex)

    for check in rules.index:
        action = rules.loc[check, regex]
        try:
            if check_functions[check](matched_data, action):
                if action == 'na':
                    continue
                action_fn = getattr(musif.logs, 'p' + action, musif.logs.perr)
                action_fn(f"{check} found to be True for columns matched by the following regex:\n\t{regex}")
        except ValueError:
            # 1. possible errors connected with casting to float
            # 2. todo
            continue

for regex in rules.columns:
    check_rules_column(regex, rules, data, check_functions)

# Parallel(n_jobs=1)(delayed(check_rules_column)(regex, rules, data, check_functions) for regex in rules.columns)
