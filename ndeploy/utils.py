import glob
import shutil
import tempfile


def create_temp_directory(prefix="ndeploy-", suffix="-ndeploy"):
    return tempfile.mkdtemp(prefix=prefix, suffix=suffix)


def rmtree(directory):
    shutil.rmtree(directory, ignore_errors=True)


def get_temp_dir_app_if_exists(app_name, suffix="-ndeploy"):
    temp_dir = glob.glob('{0}/{1}*{2}'.format(tempfile.gettempdir(), app_name, suffix))
    if temp_dir:
        return temp_dir[0]

    return None
