

class NDeployError(Exception):
    """
    Base class for exceptions in ndeploy
    """
    pass


class InvalidArgumentError(NDeployError):
    """
    Exception thrown when invalid arguments are passed to ndeploy
    """
    def __init__(self, message):
        self.message = message


class AppConfigFileCloneError(NDeployError):
    """
    Throws when ndeploy could not get remote config file for a deploy
    """
    def __init__(self, repo, local_file):
        self.repo = repo
        self.local_file = local_file

    def __str__(self):
        return "Could not get app config file from {}. Tried to save in {}"\
            .format(self.repo, self.local_file)


class EnvironmentAlreadyExistsError(NDeployError):
    """
    Excpetion thrown when user tries to add two environment with same name
    """
    def __init__(self, env_name):
        self.env_name = env_name

    def __str__(self):
        return "Environment with name {} already exists"\
            .format(self.env_name)

