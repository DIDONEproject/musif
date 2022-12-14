# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import os
import sys

sys.path.insert(0, os.path.abspath("../../"))

# The full version, including alpha/beta/rc tags
release = "0.1"

project = "musiF"
copyright = "2022, Didone Project"
author = "Didone Project"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "myst_parser",
    "sphinx.ext.napoleon",
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.autosummary",
]
autosummary_generate = True
autosummary_imported_members = True
myst_all_links_external = True

# templates_path = ["_templates"]
autodoc_mock_imports = [
    "music21",
    "pandas",
    "scipy",
    "joblib",
    "matplotlib",
    "numpy",
    "openpyxl",
    "deepdiff",
    "pyyaml",
    "ms3",
    "tqdm",
    "roman",
]
exclude_patterns = []

autodoc_default_options = {
    "members": True,
    "show_inheritance": True,
}


def autodoc_skip_member_handler(app, what, name, obj, skip, options):
    # Basic approach; you might want a regex instead
    if not hasattr(obj, "__doc__"):
        return True
    elif not obj.__doc__:
        return True
    elif name == "__init__":
        return False
    elif name.startswith("_"):
        return True
    return skip


def setup(app):
    app.connect("autodoc-skip-member", autodoc_skip_member_handler)


html_theme = "alabaster"
html_static_path = ["_static"]
html_css_files = ["css/custom.css"]
