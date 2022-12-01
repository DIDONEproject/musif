"""
This package implements utilities to cache and speed-up the extraction of features.
"""
from .cache import SmartModuleCache, CACHE_FILE_EXTENSION
from .utils import isinstance, iscache, hasattr, store_score_df, FileCacheIntoRAM
