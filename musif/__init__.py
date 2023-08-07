from musif.common._constants import ENCODING
from musif.extract import FeaturesExtractor
from musif.process.processor import DataProcessor
import importlib.metadata
import os 

os.environ['GIT_PYTHON_REFRESH'] = 'quiet'
try:
    __version__ = importlib.metadata.version(__package__ or __name__)
except:
    pass
