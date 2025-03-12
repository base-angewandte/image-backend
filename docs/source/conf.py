# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'base Image Backend'
copyright = 'base Angewandte | University of Applied Arts Vienna, 2025'  # noqa: A001
author = 'base Dev Team'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'myst_parser',
    'sphinx_copybutton',
]

templates_path = ['_templates']
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'furo'
html_static_path = ['_static']

# -- Additional configuration

html_show_sourcelink = False

myst_heading_anchors = 4

primary_color = '#9c27b0'

html_theme_options = {
    'light_logo': 'image-backend-light.svg',
    'dark_logo': 'image-backend-dark.svg',
    'light_css_variables': {
        'color-brand-primary': primary_color,
        'color-brand-content': primary_color,
    },
    'dark_css_variables': {
        'color-brand-primary': primary_color,
        'color-brand-content': primary_color,
    },
    'sidebar_hide_name': True,
    'navigation_with_keys': True,
    # 'announcement': 'Important announcement!',
}

pygments_style = 'default'
pygments_dark_style = 'github-dark'
