"""
Models used in deploy process
"""
from ndeploy.exception import BadFormedRemoteConfigUrlError


class Environment:
    """
    Data model for a target environment in ndeploy
    """

    def __init__(self, type, name, deploy_host, app_deployment_file_url=None):
        """
        Constructor.
        Args:
            type (str): environment type.
                Ex: 'openshift', 'dokku', 'heroku', etc.
            name (str): environment name.
                Ex: 'dev', 'qa', 'stage', 'production', etc.
            deploy_host (str): host where the target apps will be deployed
            app_deployment_file_url (str): template url from where the
                remote apps configuration will be downloaded.
                Should have three tokens separated by spaces
                [[REPO_GIT_URL]] [[BRANCH]] [[RELATIVE_APP_JSON]]
                The REPO_GIT_URL should have a {group} placeholder
                The RELATIVE_APP_JSON should have a {{app}} placeholder
                Ex: git@git.nexxera.com/conf-qa/{group}.git develop {app}.json
        """
        self.type = type
        self.name = name
        self.deploy_host = deploy_host
        self.app_deployment_file_url = app_deployment_file_url

        self.check_is_valid()

    def update(self, env):
        """
        Updates an instance of Environment.
        The environment name will keep the same.

        Args:
            env (Environment): the env with updated data
        """
        assert env.name == self.name
        self.type = env.type
        self.deploy_host = env.deploy_host
        self.app_deployment_file_url = env.app_deployment_file_url

        self.check_is_valid()

    def check_is_valid(self):
        """
        Verifies if the Environment data is valid.

        Raises:
            BadFormedRemoteConfigUrlError if `app_deployment_file_url`
                is invalid

        """
        if not self.app_deployment_file_url_is_valid():
            raise BadFormedRemoteConfigUrlError(self.name,
                                                self.app_deployment_file_url)

    def app_deployment_file_url_is_valid(self):
        """
        Tells if current environment data is in a valid format

        Returns:
            True if is valid format, False otherwise

        """
        if self.app_deployment_file_url is None:
            return True

        repo_info = self.app_deployment_file_url.split()
        return len(repo_info) == 3 and "{group}" in repo_info[0] and "{name}" in repo_info[2]

    def format_remote_deployment_file_url(self, group, name):
        """
        Parses and formats the app_deployment_file_url with group and
        name and return a tuple containing the repo info
        Args:
            group (str):
            name (str):

        Returns:
            Tuple containing (repo_url, branch, file_relative_path)

        """
        assert self.app_deployment_file_url is not None, \
            "trying to format a None app_deployment_file_url"
        self.check_is_valid()
        repo_info = self.app_deployment_file_url.split()
        return repo_info[0].format(group=group), repo_info[1], repo_info[2].format(name=name)


class App:
    """
    Data model for an application in ndeploy.
    """

    def __init__(self, name, group, **args):
        """
        Constructor.

        Args:
            name (str): application name
            group (str): application group
            deploy_name (str): application name in the deploy env.
                If not informed will use the app name.
            repository (str): application git source repository.
            image (str): application docker image url.
                if passed in it will have priority over source repository.
            env_vars (dict): environment variables that will be injected in
                the target deploy image.
                Each variable/value should be passed as the dict key/value
                OS environment variables, services and app urls could be used
                as described in `ndeploy.env_var_resolver.EnvVarResolver`
            scripts (dict): dict containing scripts that will be executed
                in deploy lifecycle (ex: predeploy or postdeploy)
        """
        self.name = name
        self.group = group
        self.deploy_name = args["deploy_name"] if "deploy_name" in args else self.name
        self.repository = args["repository"] if "repository" in args else ""
        self.image = args["image"] if "image" in args else ""
        self.env_vars = args["env_vars"] if "env_vars" in args else {}
        self.scripts = args["scripts"] if "scripts" in args else {}
