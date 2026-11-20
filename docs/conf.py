# https://www.sphinx-doc.org/en/master/usage/configuration.html
from importlib.metadata import version as get_version

project = "map_parallel"
author = "Kolen Cheung"
copyright = f"2020, {author}"
version = release = get_version("map-parallel")

extensions = [
    "myst_parser",
    "sphinx.ext.apidoc",
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
]
source_suffix = {".md": "markdown", ".rst": "restructuredtext"}
exclude_patterns = ["_build"]

html_theme = "furo"
html_title = f"{project} {version}"

autodoc_member_order = "bysource"
apidoc_modules = [
    {
        "path": "../src/map_parallel",
        "destination": "api",
        "separate_modules": True,
        "module_first": True,
    },
]
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "distributed": ("https://distributed.dask.org/en/stable", None),
    "mpi4py": ("https://mpi4py.readthedocs.io/en/stable", None),
}

myst_heading_anchors = 3
