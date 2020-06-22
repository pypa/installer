# -- Path setup --------------------------------------------------------------

# None.

# -- Project information -----------------------------------------------------

project = "installer"
copyright = "2020, Pradyun Gedam"
author = "Pradyun Gedam"


# -- General configuration ---------------------------------------------------

extensions = ["sphinx.ext.autodoc"]
templates_path = ["_templates"]
exclude_patterns = []

# -- Autodoc configuration ---------------------------------------------------

# Automatically extract typehints when not specified and add them to
# descriptions of the relevant function/methods.
autodoc_typehints = "description"

# -- Options for HTML output -------------------------------------------------

html_theme = "alabaster"
html_static_path = ["_static"]
pygments_style = "lovelace"
