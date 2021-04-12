from setuptools import find_packages, setup

from musif import VERSION

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="musif",
    version=VERSION,
    author="ICCMU Didone Project",
    author_email="didone@iccmu.es",
    description="Music feature extraction library",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="git@github.com:DIDONEproject/musiF.git",
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "beautifulsoup4==4.9.3",
        "bs4==0.0.1",
        "googletrans==3.1.0a0",
        "openpyxl==3.0.6",
        "matplotlib==3.3.4",
        "requests==2.25.1",
        "roman==3.3",
        "pandas==1.2.1",
        "numpy==1.20.0",
        "music21==6.7.1",
        "nltk==3.5",
        "tqdm==4.56.0",
        "xlrd==2.0.1",
        "roman==3.3",
        "scipy",
        "ms3",
        "pyyaml",
    ],
    entry_points={
        "console_scripts": [
            "melodic-analysis=musif.scripts.melodic_analysis:main",
        ],
    },
    python_requires=">=3.6",
)
