# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import sphinx_py3doc_enhanced_theme

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.coverage',
    'sphinx.ext.doctest',
    'sphinx.ext.extlinks',
    'sphinx.ext.ifconfig',
    'sphinx.ext.napoleon',
    'sphinx.ext.todo',
    'sphinx.ext.viewcode',
    "sphinxcontrib.apidoc",
]
source_suffix = '.rst'
master_doc = 'index'
project = 'map_parallel'
year = '2020'
author = 'Kolen Cheung'
copyright = '{0}, {1}'.format(year, author)
version = release = '0.2.0'

pygments_style = 'trac'
templates_path = ['.']
extlinks = {
    'issue': ('https://github.com/ickc/python-map_parallel/issues/%s', '#'),
    'pr': ('https://github.com/ickc/python-map_parallel/pull/%s', 'PR #'),
}
html_theme = "sphinx_py3doc_enhanced_theme"
html_theme_path = [sphinx_py3doc_enhanced_theme.get_html_theme_path()]
html_theme_options = {
    'githuburl': 'https://github.com/ickc/python-map_parallel/'
}

html_use_smartypants = True
html_last_updated_fmt = '%b %d, %Y'
html_split_index = False
html_sidebars = {
   '**': ['searchbox.html', 'globaltoc.html', 'sourcelink.html'],
}
html_short_title = '%s-%s' % (project, version)

napoleon_use_ivar = True
napoleon_use_rtype = False
napoleon_use_param = False

# https://github.com/sphinx-contrib/apidoc
apidoc_module_dir = "../src/map_parallel"
apidoc_separate_modules = True
apidoc_module_first = True
