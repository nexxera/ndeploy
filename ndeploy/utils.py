import shutil
import tempfile


def create_temp_directory(prefix="ndeploy-", suffix="-ndeploy"):
    return tempfile.mkdtemp(prefix=prefix, suffix=suffix)


def rmtree(directory):
    shutil.rmtree(directory, ignore_errors=True)
