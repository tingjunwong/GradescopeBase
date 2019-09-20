import os

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
        return "/autograder/submission"