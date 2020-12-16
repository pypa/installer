# -- Project information -----------------------------------------------------
project = "installer"

copyright = "2020, Pradyun Gedam"
author = "Pradyun Gedam"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.todo",
    "myst_parser",
]

# -- Options for Autodoc -----------------------------------------------------

# Automatically extract typehints when not specified and add them to
# descriptions of the relevant function/methods.
autodoc_typehints = "description"

# -- Options for HTML output -------------------------------------------------
html_theme = "furo"
html_title = "installer"
