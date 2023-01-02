# Hooks

Hooks were originally introduced to mitigate the limits of the [caching
system](./Caching.html), that forbid the modification of `music21` objects from inside
the features.

However, they turn to be useful to expand the compatibility of musiF to file formats and
datasets that present differences and that generates error with the musiF code. For an
example, see the [advanced tutorial]().

A hook is any object, module, or package with a function `execute` which
accepts two objects: a [`Configuration`](./Configuration.html) object and the data parsed from
the score. The latter is a dictionary which contains the `music21.stream.Score` object
resulting from the MusicXML file, its parts data, the harmonic annotations contained in
a MuseScore file (if available), etc.

An example of a hook may be the following:
```python

import pandas as pd
import musif.extract.constants as C

class MyHook:
  def execute(cfg, data):
      score: Score = data[C.DATA_SCORE]
      ms3_df: pd.DatFrame = data[C.DATA_MUSESCORE_SCORE]
      for p in score.parts:
        score.remove(p)

      ms3_df[:] = 0

      return data
```

You can put the function `execute` in any object. In this case, we used a class, but you
could even use a module or a package.

Then you only need to tell to the `FeatureExtractor` object that it should use the hook:
```python
from musif.extract.extract import FeaturesExtractor

df = FeaturesExtractor("config.yml", precache_hooks=[MyHook])
```
Of course, you can use the option `precache_hooks` in the `config.yml` file as well, in
which case you should pass a string that can be imported with `import ...` or loaded
with `getattr`.

Hooks is run just before of creating the `SmartModuleCache` object, thus they are only
run when parsing the score, not when loading the cache from file.
