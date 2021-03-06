"""
/*
 * @Author: ThaumicMekanism [Stephan K.] 
 * @Date: 2020-01-23 21:03:57 
 * @Last Modified by: ThaumicMekanism [Stephan K.]
 * @Last Modified time: 2020-01-30 16:27:10
 */
"""
import os
from distutils.version import LooseVersion

VERSION = "1.0.1"

def get_welcome_message():
    return f"Thank you for using GradescopeBase v{VERSION} created by ThaumicMekanism [Stephan K.]!"

def is_local() -> bool:
    return os.environ.get("IS_LOCAL") == "true"

def root_dir() -> str:
    """
    This function assumes the root directory is the one right above the GradescopeBase folder.
    """
    dirname = os.path.dirname
    return dirname(dirname(os.path.realpath(__file__)))

def submission_dir() -> str:
    """
    This returns the dir which contains the submission.
    """
    if is_local():
        return "./submission"
    return "/autograder/submission"

def results_path() -> str:
    """
    This returns the path which the results json should be exported to.
    """
    if is_local():
        return "./results/results.json"
    return "/autograder/results/results.json"

class NoneLooseVersion(LooseVersion):
    def __init__ (self, vstring=None):
        if vstring:
            self.parse(vstring)
        else:
            self.version = None

    def _cmp (self, other):
        if isinstance(other, str):
            other = NoneLooseVersion(other)
        if self.version == other.version:
            return 0
        if self.version is not None:
            return -1
        if other.version is not None:
            return 1
        if self.version < other.version:
            return -1
        if self.version > other.version:
            return 1

def merge(a, b, path=None):
    "merges b into a"
    if path is None: path = []
    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                merge(a[key], b[key], path + [str(key)])
            elif a[key] == b[key]:
                pass # same leaf value
            else:
                raise Exception('Conflict at %s' % '.'.join(path + [str(key)]))
        else:
            a[key] = b[key]
    return a