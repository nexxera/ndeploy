

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


class BadFormedRemoteConfigUrlError(NDeployError):
    """
    Thrown when an app deployment file url was passed in wrong format
    """
    def __init__(self, env, url):
        """
        Args:
            env (str): env name
            url (str): bad formed url
        """
        self.env = env
        self.url = url

    def __str__(self):
        return "Could not parse the app deployment file url for environment {env}. " \
               "\nCurrent url: {url}" \
               "\nUrl should be GIT_REPO GIT_BRANCH RELATIVE_JSON_PATH" \
               "\nExample: git@git.nexxera.com/conf-qa/{{group}}.git develop {{name}}.json".format(env=self.env, url=self.url)


class EnvironmentAlreadyExistsError(NDeployError):
    """
    Excpetion thrown when user tries to add two environment with same name
    """
    def __init__(self, env_name):
        self.env_name = env_name

    def __str__(self):
        return "Environment with name {} already exists"\
            .format(self.env_name)


class EnvironmentDoesNotExistError(NDeployError):
    """
    Exception thrown when user tries to get an inexistent environment
    """
    def __init__(self, env_name):
        self.env_name = env_name

    def __str__(self):
        return "Environment with name {} does not exist" \
            .format(self.env_name)


class InvalidVarTypeError(NDeployError):
    """
    Thrown when an invalid var type is passed in env_vars app field
    """
    def __init__(self, var_name):
        self.var_name = var_name

    def __str__(self):
        return "Could not parse var type with name {}" \
            .format(self.var_name)


