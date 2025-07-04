import glob
from os.path import basename, dirname, isfile


def __list_all_EModules():
    mod_paths = glob.glob(dirname(__file__) + "/*.py")

    all_EModules = [
        basename(f)[:-3]
        for f in mod_paths
        if isfile(f) and f.endswith(".py") and not f.endswith("__init__.py")
    ]

    return all_EModules


ALL_EModules = sorted(__list_all_EModules())
__all__ = ALL_EModules + ["ALL_EModules"]




