import re
import pandas as pd
import numpy as np
from urllib.request import urlopen

REGEX = {}

def features2type(numeral, form=None, figbass=None):
	""" Turns a combination of the three chord features into a chord type.
    Returns
    -------
    'M':    Major triad
    'm':    Minor triad
    'o':    Diminished triad
    '+':    Augmented triad
    'mm7':  Minor seventh chord
    'Mm7':  Dominant seventh chord
    'MM7':  Major seventh chord
    'mM7':  Minor major seventh chord
    'o7':   Diminished seventh chord
    '%7':   Half-diminished seventh chord
    '+7':   Augmented (minor) seventh chord
    '+M7':  Augmented major seventh chord
    """
	if pd.isnull(numeral):
		return numeral
	form, figbass = tuple('' if pd.isnull(val) else val for val in (form, figbass))
	#triads
	if figbass in ['', '6', '64']:
		if form in ['o', '+']:
			return form
		if form in ['%', 'M']:
			if figbass == '':
				return f"{form}7"
			print(f"{form} is a seventh chord and cannot have figbass '{figbass}'")
			return None
		return 'm' if numeral.islower() else 'M'
	# seventh chords
	if form in ['o', '%', '+', '+M']:
		return f"{form}7"
	triad = 'm' if numeral.islower() else 'M'
	seventh = 'M' if form == 'M' else 'm'
	return f"{triad}{seventh}7"



def make_type_col(df, num_col='numeral', form_col='form', fig_col='figbass'):
	""" Create a new Series with the chord type for every row of `df`.
        Uses: features2type()
    """
	param_tuples = list(df[[num_col, form_col, fig_col]].itertuples(index=False, name=None))
	result_dict = {t: features2type(*t) for t in set(param_tuples)}
	return pd.Series([result_dict[t] for t in param_tuples], index=df.index, name='chordtype')



def sort_labels(labels, git_branch='master', drop_duplicates=True, verbose=True, **kwargs):
	""" Sort a list of DCML labels following custom criteria.
        Uses: split_labels()
    Parameters
    ----------
    labels : :obj:`collection` or :obj:`pandas.Series`
        The labels you want to sort.
    git_branch : :obj:`str`, optional
        The branch of the DCMLab/standards repo from which you want to use the regEx.
    drop_duplicates : :obj:`bool`, optional
        By default, the function returns an ordered list of unique labels. Set to
        False in order to keep duplicate labels. Note that where the ordered features
        are identical, labels appear in the order of their occurrence.
    verbose : .obj:`bool`, optional
        By default, values that are missing from custom orderings are printed out.
        Pass False to prevent that.
    kwargs : {'values', 'occurrences', 'rvalues', 'roccurrences'}, :obj:`dict`, :obj:`list` or callable
        Pass one argument for every feature that you want to sort in the order
        in which features should be used for sorting. The arguments will be mapped
        on the respective columns which should yield alpha-numeric values to be sorted.
        globalkey
        localkey
        pedal
        chord
        numeral
        form
        figbass
        changes
        relativeroot
        pedalend
        phraseend
        chordtype
    Examples
    --------
    .. highlight:: python
        # Sort numerals by occurrences (descending), the figbass by occurrences (ascending), and
        # the form column by the given order
        sort_labels(labels, numeral='occurrences', figbass='roccurrences', form=['', '+', 'o', '%', 'M'])
        # Sort numerals by custom ordering and each numeral by the (globally) most frequent chord types.
        sort_labels(labels, numeral=['I', 'V', 'IV'], chordtype='occurrences')
        # Sort relativeroots alphabetically and the numerals by a custom ordering which
        # is equivalent to ['V', 'vii', '#vii']
        sort_labels(labels, relativeroot='rvalues', numeral={'vii': 5, 'V': 0,  '#vii': 10})
        # Sort chord types by occurrences starting with the least frequent and sort their inversions
        # following the given custom order
        sort_labels(labels, chordtype='roccurrences', figbass=['2', '43', '65', '7'])
    """
	if len(kwargs) == 0:
		raise ValueError("Pass at least one keyword argument for sorting...")
	if not isinstance(labels, pd.core.series.Series):
		if isinstance(labels, pd.core.frame.DataFrame):
			raise TypeError("Pass only one column of your DataFrame.")
		labels = pd.Series(labels)
	if drop_duplicates:
		labels = labels.drop_duplicates()
	features = split_labels(labels, git_branch)

	def make_keys(col, order):

		def make_order_dict(it):
			missing = [v for v in col.unique() if v not in it]
			if len(missing) > 0 and verbose:
				print(f"The following values were missing in the custom ordering for column {col.name}:\n{missing}")
			return {v: i for i, v in enumerate(list(it) + missing)}

		if order in ['values', 'rvalues']:
			keys = sorted(set(col)) if order == 'values' else reversed(sorted(set(col)))
			order_dict = make_order_dict(keys)
		elif order in ['occurrences', 'roccurrences']:
			keys = col.value_counts(dropna=False).index if order == 'occurrences' else col.value_counts(dropna=False, ascending=True).index
			order_dict = make_order_dict(keys)
		elif order.__class__ is not dict:
			try:
				order_dict = make_order_dict(order)
			except:
				# order is expected to be a callable:
				return np.vectorize(order)(col)
		else:
			order_dict = order

		return np.vectorize(order_dict.get)(col)

	if 'chordtype' in kwargs:
		features['chordtype'] = make_type_col(features)
	key_cols = {col: make_keys(features[col], order) for col, order in kwargs.items() if col in features.columns}
	df = pd.DataFrame(key_cols, index=features.index)
	ordered_ix = df.sort_values(by=df.columns.to_list()).index
	return labels.loc[ordered_ix]



def split_labels(labels, git_branch='master', dropna=True):
	""" Split DCML harmony labels into their respective features using the regEx
        from the indicated branch of the DCMLab/standards repository.
    Parameters
    ----------
    labels : :obj:`pandas.Series`
        Harmony labels to be split.
    git_branch : :obj:`str`, optional
        The branch of the DCMLab/standards repo from which you want to use the regEx.
    dropna : :obj:`bool`, optional
        Drop rows where the regEx didn't match.
    """
	global REGEX
	if git_branch not in REGEX:
		url = f"https://raw.githubusercontent.com/DCMLab/standards/{git_branch}/harmony.py"
		glo, loc = {}, {}
		exec(urlopen(url).read(), glo, loc)
		REGEX[git_branch] = re.compile(loc['regex'], re.VERBOSE)
	regex = REGEX[git_branch]
	cols = ['globalkey', 'localkey', 'pedal', 'chord', 'numeral', 'form', 'figbass', 'changes', 'relativeroot', 'pedalend', 'phraseend']
	res = labels.str.extract(regex, expand=True)[cols]
	if dropna:
		return res.dropna(how='all').fillna('')
	return res.fillna('')

# labels = pd.read_csv('labels.csv').label
# sort_labels(labels, chordtype='roccurrences')