from .utils import get_java_path, download_jsymbolic(), JavaNotFoundError

download_jsymbolic()
try:
    get_java_path()
except JavaNotFoundError:
    print("Java not found!")
    print("Value of JAVA_HOME:", os.environ["JAVA_HOME"])
    print("Value of PATH:", os.environ["PATH"])
