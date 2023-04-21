import io
import os
import shutil
import sys
import subprocess
import platform
import zipfile
import requests
from pathlib import Path

from musif.logs import linfo
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
        "Could not find Java Runtime Environment (JRE)! Please, set JAVA_HOME environment variable or make it available in the PATH."
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
        cache_dir = Path(os.getenv("APPDATA"), "jSymbolic")
    elif platform.system() == "Linux":
        cache_dir = Path.home() / ".cache" / "jSymbolic"
    elif platform.system() == "Darwin":
        cache_dir = Path.home() / "Library" / "Caches" / "jSymbolic"
    else:
        raise Exception("Unsupported operating system: " + platform.system())
    if not cache_dir.exists():
        cache_dir.mkdir(parents=True)
    filename = cache_dir / "jSymbolic.jar"
    return filename


def download(url):
    resp = requests.get(url, stream=True)
    total = int(resp.headers.get('content-length', 0))
    data = b''
    with tqdm(
        desc=url,
        total=total,
        unit='iB',
        unit_scale=True,
        unit_divisor=1024,
    ) as bar:
        for chunk in resp.iter_content(chunk_size=1024):
            data += chunk
            bar.update(len(chunk))
    return data


def download_jsymbolic():
    # Download jSymbolic, if not already downloaded
    # and save it to the OS cache directory
    filename = _jsymbolic_path()
    libdir = filename.parent / 'lib'

    if not filename.exists() or not libdir.exists():
        # Download the zip file
        data = download(JSYMBOLIC_URL)

        # Extract the jar file from the zip file
        with zipfile.ZipFile(io.BytesIO(data)) as zf:

            # Extract the lib directory recursively
            libdir.mkdir()
            for f in zf.filelist:
                if f.filename.startswith('jSymbolic_2_2_user/lib'):
                    with zf.open(f.filename) as fin:
                        with open(libdir.as_posix() + f.filename[len('jSymbolic_2_2_user/lib'):], 'wb') as fout:
                            fout.write(fin.read())

            # Extract the jar file
            with zf.open('jSymbolic_2_2_user/jSymbolic2.jar') as f:
                with open(filename.as_posix(), 'wb') as fout:
                    fout.write(f.read())
        linfo("jSymbolic downloaded into {filname}")
