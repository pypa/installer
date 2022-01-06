"""A sphinx documentation configuration file.
"""

import os
import pathlib
import sys

# -- Project information ---------------------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
project = "installer"

copyright = "2020, Pradyun Gedam"
author = "Pradyun Gedam"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.doctest",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "myst_parser",
]

# -- Options for HTML output -----------------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_title = project

# -- Options for Autodoc --------------------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html#configuration

autodoc_member_order = "bysource"
autodoc_preserve_defaults = True

# Automatically extract typehints when not specified and add them to
# descriptions of the relevant function/methods.
autodoc_typehints = "description"
autodoc_typehints_description_target = "documented"

if "READTHEDOCS" in os.environ:
    src_folder = pathlib.Path(__file__).resolve().parent.parent / "src"
    sys.path.append(str(src_folder))

    print("Detected running on ReadTheDocs")
    print(f"Added {src_folder} to sys.path")
    __import__("installer")

# -- Options for intersphinx ----------------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/intersphinx.html#configuration

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "pypug": ("https://packaging.python.org", None),
}

# -- Options for Markdown files --------------------------------------------------------
# https://myst-parser.readthedocs.io/en/latest/sphinx/reference.html

myst_enable_extensions = [
    "colon_fence",
    "deflist",
]
myst_heading_anchors = 3
