# Configuration file for the Sphinx documentation builder.

from datetime import date
import importlib
import inspect
from pathlib import Path
import sys

sys.path.insert(0, str(Path("../..").absolute()))
sys.path.insert(0, str(Path("../../").absolute()))

from __about__ import __version__

try:
    import git  # pyright: ignore[reportMissingImports]

    git_repo = git.Repo(".", search_parent_directories=True)
    git_commit = git_repo.head.commit
except ImportError:
    git_commit = "main"
    git_repo = None

# -- Project information
project = "QuickUp!"
copyright = f"{date.today().year}, Matias Agustin Mendez"
author = "Matias Agustin Mendez"

version = __version__
release = __version__

# -- General configuration
extensions = [
    "sphinx_rtd_theme",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.linkcode",
    "sphinx_copybutton",
]

templates_path = ["_templates"]
exclude_patterns = []
smartquotes = False

# Napoleon settings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = False
napoleon_type_aliases = None
napoleon_attr_annotations = True

# Autodoc
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "undoc-members": True,
    "exclude-members": "__weakref__",
}
autoclass_content = "init"

# LinkCode — links API docs to GitHub source
code_url = f"https://github.com/matagus/quickup/blob/{git_commit}"


def linkcode_resolve(domain, info):
    """Link code references to GitHub."""
    if domain == "js":
        return
    if domain != "py":
        raise ValueError("expected only Python objects")
    if not info.get("module"):
        return

    mod = importlib.import_module(info["module"])
    if "." in info["fullname"]:
        objname, attrname = info["fullname"].split(".")
        obj = getattr(mod, objname)
        try:
            obj = getattr(obj, attrname)
        except AttributeError:
            return None
    else:
        obj = getattr(mod, info["fullname"])

    try:
        file = inspect.getsourcefile(obj)
        lines = inspect.getsourcelines(obj)
    except TypeError:
        return None
    if file is None or git_repo is None:
        return None
    file = Path(file).resolve().relative_to(git_repo.working_dir)
    if file.parts[0] != "quickup":
        return None
    start, end = lines[1], lines[1] + len(lines[0]) - 1
    return f"{code_url}/{file}#L{start}-L{end}"


# -- HTML output
html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_title = project
html_logo = None
html_favicon = None

html_theme_options = {
    "logo_only": False,
    "prev_next_buttons_location": "bottom",
    "style_external_links": False,
    "vcs_pageview_mode": "",
    "style_nav_header_background": "white",
    "collapse_navigation": True,
    "sticky_navigation": True,
    "navigation_depth": 4,
    "includehidden": True,
    "titles_only": False,
}

html_context = {
    "display_github": True,
    "github_user": "matagus",
    "github_repo": "quickup",
    "github_version": "main",
    "conf_py_path": "/docs/source/",
}

html_css_files = [
    "custom.css",
]
