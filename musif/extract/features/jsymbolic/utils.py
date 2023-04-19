import os
import shutil
import sys
import subprocess
import platform
import urllib.request
from tqdm import tqdm

JSYMBOLIC_URL = "https://master.dl.sourceforge.net/project/jmir/jSymbolic/jSymbolic%202.2/jSymbolic_2_2_user.zip"


class JavaNotFoundError(RuntimeError):
    pass


def get_java_path():
    java = __get_java_path_env()
    if java is not None:
        return java
    java = __get_java_path_subprocess()
    if java is not None:
        return java
    java = __get_java_path_env()
    if java is not None:
        return java
    raise JavaNotFoundError(
        "Could not find Java! Plese, set JAVA_HOME environment variable or make it available in the PATH."
    )


def __get_java_path_env():
    if sys.platform == "win32":
        java = os.path.join(os.environ["JAVA_HOME"], "bin", "java.exe")
    else:
        java = os.path.join(os.environ["JAVA_HOME"], "bin", "java")
    if os.path.exists(java):
        return java
    else:
        return None


def __get_java_path_shutil():
    path = shutil.which("java")
    return path


def __get_java_path_subprocess():
    try:
        return subprocess.check_output(["which", "java"]).decode("utf-8").strip()
    except subprocess.CalledProcessError:
        return None


def _jsymbolic_path():
    if platform.system() == "Windows":
        cache_dir = os.path.join(os.getenv("APPDATA"), "jSymbolic")
    elif platform.system() == "Linux":
        cache_dir = os.path.expanduser("~/.cache/jsymbolic")
    elif platform.system() == "Darwin":
        cache_dir = os.path.expanduser("~/Library/Caches/jSymbolic")
    else:
        raise Exception("Unsupported operating system: " + platform.system())
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    filename = os.path.join(cache_dir, "jsymbolic.jar")
    return filename


def download_jsymbolic():
    # Download jSymbolic, if not already downloaded
    # and save it to the OS cache directory
    filename = _jsymbolic_path()

    if not os.path.exists(filename):
        print("Downloading jSymbolic...")
        with tqdm(unit="B", unit_scale=True, unit_divisor=1024, miniters=1) as t:
            urllib.request.urlretrieve(JSYMBOLIC_URL, filename, reporthook=t.update_to)
        print("Download complete.")
    else:
        print("jSymbolic already downloaded.")
