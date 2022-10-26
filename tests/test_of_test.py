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
features_definition = pd.read_excel('tests/FeaturesDefinition.xlsx')
rules = features_definition.iloc[:, 5:]
rules.set_index(features_definition['Name'], inplace=True)
data = pd.read_csv('martiser/extraction_total'+'_alldata.csv', header=0, index_col=False)


def checktype(x, check_type):
    """
    check that any columns in `df` is not of type `t`

    returns True if any is not of type 't' or False otherwise
    """
    if check_type == 'str':
        return not all(is_string_dtype(x[col]) for col in x.columns)
    elif check_type == 'float':
        return not all(is_float_dtype(x[col]) for col in x.columns)
    elif check_type == 'int':
        x.dropna(inplace=True)
        x_ = x.astype(int)
        return not all(x_ == x) # in case there is any float value. Meant for int columns that might contain nans
    elif check_type == 'bool':
        return not all(is_bool_dtype(x[col]) for col in x.columns)


check_functions = {
        'any_na': lambda x, y: np.asarray(list(x.index))[x.isna().to_numpy()[:, 0]],
        'all_na': lambda x, y: x.isna().all()[0],
        'any_0': lambda x, y:  np.asarray(list(x.index))[(x==0).to_numpy()[:, 0]],
        'all_0': lambda x, y: (x == 0).all()[0],
        'minval': lambda x, y:  np.asarray(list(x.index))[(x.select_dtypes([int, float]) < float(y)).to_numpy()[:, 0]],
        'maxval': lambda x, y:  np.asarray(list(x.index))[(x.select_dtypes([int, float]) > float(y)).to_numpy()[:, 0]],
        'data_type': checktype
        }


def check_rules_column(regex, rules, data, check_functions):
    # getting the portion of data that must be checked
    matched_data = data.filter(regex='\\b' + regex + '\\b')
    
    if matched_data.empty:
        if rules.loc[regex, 'removed_postpro'] == 1:
            return
        musif.logs.perr(f'{regex} could not be found!')
        return

    # for check in rules.index:
    for check in rules.columns[:-1]:
        action = rules.loc[regex, check]
        try:
            check_res = check_functions[check](matched_data, action)
            if (type(check_res) is np.ndarray and check_res.size > 0) or (check_res is True):
                if action == 'na':
                    continue
                if type(action) is not str:
                    action='err'
                action_fn = getattr(musif.logs, 'p' + action, musif.logs.perr)
                action_fn(f"{check} found to be True for columns matched by the following regex:\n\t{regex}. Columns: {matched_data.columns}")
                if type(check_res) is np.ndarray and action == 'err':
                    print(f'Indexes are: {check_res} for columns {list(matched_data.columns)}')
                    
                    
        except ValueError:
            # 1. possible errors connected with casting to float
            # 2. todo
            continue

# for regex in rules.columns:
for regex in features_definition['Name']:
    check_rules_column(regex, rules, data, check_functions)

# Parallel(n_jobs=1)(delayed(check_rules_column)(regex, rules, data, check_functions) for regex in rules.columns)
