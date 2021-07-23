# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use Path(__file__).absolute().resolve().parent to make it absolute, like shown here.
#
# import os
# import sys
# sys.path.insert(0, Path('.').absolute())


# -- Project information -----------------------------------------------------

project = 'OpenNFT'
copyright = '2020, OpenNFT Team'
author = 'OpenNFT Team'

# The full version, including alpha/beta/rc tags
release = '1.0.0'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.todo',
]

todo_include_todos = True

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'alabaster'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

html_theme_options = {
    'logo': 'logo.png',
    'fixed_sidebar': 'true',
    'show_powered_by': 'false',

    'description': 'An open-source Python/Matlab framework for real-time fMRI neurofeedback training',

    'github_user': 'opennft',
    'github_repo': 'OpenNFT',
    'github_type': 'star',

    'extra_nav_links': {
        'GitHub repository': 'https://github.com/opennft/OpenNFT',
        # 'PyPI': 'https://pypi.org/project/pyOpenNFT',
    },
}
