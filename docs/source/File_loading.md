# File loading

`musif` is mainly built on top of MusicXML files. Specifically, it uses [`music21`](https://web.mit.edu/`music21`/) to
parse them and a [caching system](./Caching.html) to cache the parsed objects and speed
up successive parsing.

While MusicXML offers a rather complete representation of Western music notation, it
does not offer a standard way of encoding complex harmonic annotations. For this reason,
we adopted MuseScore files as well (another option could be the MEI or the IEEE
1599 formats).

Finally, we offer the option to load any file format supported by MuseScore or
`music21`.

All these file formats are managed by 3 directories:
1. `data_dir`: directory for MusicXML files or files loaded by `music21`
2. `musescore_dir`: directory for MuseScore files or files loaded by MuseScore
3. `cache_dir`: directory for cached files

To these, we should also add the `dfs_dir`, which is an experimental feature to export
the music data parsed using `MuseScore` and `music21` to pandas DataFrames that are
easily usable for datascience purposes. For now, this format is not usable for
extracting features and can be accessed using the
[`load_score_df`](./API/musif.cache.html#musif.cache.utils.load_score_df) function.
More details are available in the [API
docs](./API/musif.cache.html#musif.cache.utils.store_score_df).

## File precedence

The file loading system works as follows.

First, a list of files is obtained in this way:

1. The `data_dir` directory is recuresively searched for a [specific
   extension](./API/musif.musicxml.html#musif.musicxml.constants.MUSICXML_FILE_EXTENSION)
   (`.xml` by default).
2. The `musescore_dir` directory is recursively searched for a
   [specific
   extension](./API/musif.musescore.html#musif.musescore.constants.MUSESCORE_FILE_EXTENSION)
   (`.mscx` by default).
3. Choose the main directory for file discovery:
    1. Try using `data_dir` and the discovered files in it.
    2. Ff no file in `data_dir` is found or if `data_dir` is not specified, try using the
     `musescore_dir` and the files found in it .
    3. If no file is found in the `musescore_dir` or in the `data_dir`, the `cache_dir` is
     recursively searched.

Once the list of files has been obtained, we proceed to the parsing of each
`filename`:
1. If a corresponding file is found in `cache_dir`, unpickle it and skip the parsing.
2. If `filename` has the [extension specified for
   MuseScore](./API/musif.musescore.html#musif.musescore.constants.MUSESCORE_FILE_EXTENSION),
   convert it to the [extension specified for
   `music21`](./API/musif.musicxml.html#musif.musicxml.constants.MUSICXML_FILE_EXTENSION)
   format using MuseScore; by default, `ms3` is used to discover a path to the MuseScore
   executable, but you can specify it using the `mscore_exec` option (you will need this
   option to run MuseScore without graphical environment, e.g., using `xvfb-run`); by
   default, files are converted to MusicXML.
3. If `filename` has the [extension specified for
   `music21`](./API/musif.musicxml.html#musif.musicxml.constants.MUSICXML_FILE_EXTENSION),
   parse it using `music21`.
4. If `filename` also exists in `musescore_dir` (with the extension specified for
   MuseScore) and harmonic features are requested, load it using `ms3` in search of
   harmonic annotations. Harmonic features are listed (and editable) in [a constant
   variable](./API/musif.extract.html#musif.extract.constants.REQUIRE_MSCORE) and by
   default they are `'harmony'` and `'scale_relative'` only.

In general, the recommended file format is MusicXML, as created by [MakeMusic Finale®
27](https://web.archive.org/web/https://www.finalemusic.com/blog/finale-v27-is-here/).
However, you can tune `musif.musicxml.constants.MUSICXML_FILE_EXTENSION` to load any
other file supported by `music21`, or `musif.musescore.constants.MUSESCORE_FILE_EXTENSION`
to load any file supported by MuseScore. In general, the two latter methods will lead to
loss of information in the feature extraction process and will likely generate errors.
Thus, you will need to tune the extraction process using [hooks](./Hooks.html) and
[custom features](./Custom_features.html). For instance, you could load a dataset of
MIDI files by using MuseScore or Humdrum/ABC/MEI files by using `music21`. Where possible,
we suggest the use of MuseScore. See the [advanced tutorial]() for an example.

It is not possible to mix `data_dir` and `musescore_dir`, except when [harmonic
annotations](./API/musif.extract.html#musif.extract.constants.REQUIRE_MSCORE) are
needed. Indeed, if a file is found in `data_dir`, then
`musescore_dir` is expected to contain files with harmonic features, i.e., MuseScore
files loadable by `ms3`. On the contrary, if `data_dir` is empty, MusicXML files will
be created using MuseScore; thus, if you need harmonic annotations, you could
theoretically provide only MuseScore files with harmonic annotations. However, we
experienced errors due to the parsing of MusicXML by `music21` and to the  slight
differences in the MusicXML files produced by different notation software, such as
MuseScore, Finale, Sibelius, Dorico, etc.

## Annotating

`musif` was created in the context of the ERC [Didone](https://didone.eu) project and thus
it works better when using the same work pipeline and annotations.

In the `Didone` project, we adopted the following approach:
1. An engraver transcribed the original manuscript source using Finale® 27 and
   exported it to a MusicXML file with `.xml` extension.
2. Further checks and error fixing was performed by a group of musicologists and orchestra conductors.
3. A music theorist annotated the harmonic analysis using MuseScore and saved it to a
   `.mscx` file; harmonic anotations were created following the guidelines presented in [1] and extended in [2].

As consequence, we suggest the use of MuseScore files for harmonic annotations and
Finale® for engraving the music. Note that the harmonic features of `musif` only
work with the annotation format presented in [1].

## References

[1] Neuwirth, M., Harasim, D., Moss, F. C., & Rohrmeier, M. (2018). The Annotated Beethoven Corpus (ABC): A Dataset of Harmonic Analyses of All Beethoven String Quartets. Frontiers in Digital Humanities, 5. https://doi.org/10.3389/fdigh.2018.00016

[2] Hentschel, J., Neuwirth, M., & Rohrmeier, M. (2021). The Annotated Mozart Sonatas: Score, Harmony, and Cadence. Transactions of the International Society for Music Information Retrieval, 4(1), 67–80. https://doi.org/10.5334/tismir.63
