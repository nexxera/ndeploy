import json
import shutil
import os.path
from ndeploy.model import App, Environment
from ndeploy.exception import InvalidArgumentError, \
    AppConfigFileCloneError, BadFormedRemoteConfigUrlError


class Deployer:
    """
    Class responsible for resolving the deploy configurations and
    delegating to a provider to do deploy.
    """

    def __init__(self, provider_repository, env_repository):
        """
        Constructor.
        Args:
            provider_repository (provider.ProviderRepository):
            env_repository (environment_repository.EnvironmentRepository):
        """
        self.provider_repository = provider_repository
        self.env_repository = env_repository

    def deploy(self, file=None, group=None, name=None, environment=None):
        """
        Resolves the user parameters and deploys an app in an environment.

        The app configuration will be resolved locally if `file` parameter
        was passed or in a remote git repository with the url configured
        in the environment (@see ndeploy.model.Environment.app_deployment_file_url)

        If remotely the url will be formatted with the `group` and `name`
        passed.

        Args:
            file (str): path to the local json configuration file
            group (str): app group
            name (str): app name
            environment (str): environment name where the app will be deployed
        """
        app_data = None

        if file:
            with open(file) as json_data:
                app_data = json.load(json_data)

        env = self._resolve_environment(app_data, environment)
        assert env is not None

        app = self._resolve_app(app_data, group, name, env)
        assert app is not None

        self.provider_repository.get_provider_for(env.type).deploy(app, env)

    def _get_remote_conf(self, repo_url, branch, file_relative_path, rsa_path):
        """
        Gets the remote app configuration file in a git repository

        Args:
            repo_url (str): the remote repo url
            branch (str): git branch name
            file_relative_path (str): the path of the file relative to the repo root
            rsa_path (str): path to the repo rsa private key

        Returns:
            dict containing the contents of the remote json file

        """
        local_folder = os.path.join(
            self.env_repository.get_ndeploy_dir(), "tmp")

        if os.path.isdir(local_folder):
            shutil.rmtree(local_folder)

        os.makedirs(local_folder)

        print("getting config file from " + repo_url)

        os.system("ssh-agent bash -c 'ssh-add {rsa_path}; git archive --remote={repo_url} "
                  "{branch} {file_relative_path} | tar -x -C {local_folder}'"
                  .format(rsa_path=rsa_path, repo_url=repo_url,
                          branch=branch, local_folder=local_folder,
                          file_relative_path=file_relative_path))

        cloned_file = os.path.join(local_folder, file_relative_path)
        if not os.path.isfile(cloned_file):
            raise AppConfigFileCloneError(repo_url, cloned_file)

        with open(cloned_file) as json_data:
            app_data = json.load(json_data)

        return app_data

    def _format_remote_app_file_url(self, group, name, environment):
        """
        Formats the environenmt.app_deployment_file_url with group and
        name info and return a tuple containing the url info
        Args:
            group (str):
            name (str):
            environment (str):

        Returns:
            Tuple containing (repo_url, branch, file_relative_path)

        """
        repo_info = environment.app_deployment_file_url.split()
        if len(repo_info) != 3:
            raise BadFormedRemoteConfigUrlError(name, environment.name,
                                                environment.app_deployment_file_url)

        return repo_info[0].format(group=group), repo_info[1], \
            repo_info[2].format(name=name)

    def _resolve_remote_app_file(self, group, name, environment):
        """
        Resolves the remote app configuration file.
        Will download from a git repository configured in the environment.
        (@see ndeploy.model.Environment.app_deployment_file_url)

        Args:
            group (str): the app group
            name (str): the app name
            environment (str): the environment name

        Returns:
            dict containing the contents of remote configuration json

        """
        assert environment
        assert group

        rsa_key = self.env_repository.get_env_private_key_path(environment.name)
        repo_url, branch, file_relative_path = self._format_remote_app_file_url(group, name, environment)
        app_data = self._get_remote_conf(repo_url, branch, file_relative_path, rsa_key)

        return app_data

    def _resolve_app(self, app_data, group, name, environment):
        """
        Resolves the app deploy configuration locally or remotely.
        Will try to resolve remotely (in a git repo) only if `app_data` is None

        Args:
            app_data (dict): the app data (if None will try to get remotely)
            group (str): the app group name (will be used only if `app_data` is None)
            name (str): the app name (will be used only if `app_data` is None)
            environment (str): environment name (will be used only if `app_data` is None)

        Returns:
            ndeploy.model.App object

        """
        if not app_data:
            app_data = self._resolve_remote_app_file(group, name, environment)

        assert app_data

        if "environment" in app_data:
            app_data.pop("environment")

        return App(**app_data)

    def _resolve_environment(self, app_data, environment):
        """
        Resolves the environment deploy configuration and returns
        an instance of Environment class.

        Args:
            app_data (dict): the app data
            environment (str): environment name

        Returns:
            ndeploy.model.Environment object

        """
        if environment and self.env_repository.has_environment(environment):
            return self.env_repository.load_environment(environment)

        if app_data and "environment" in app_data:
            env = app_data["environment"]
            return Environment(env["type"], env["name"],
                               env["deploy_host"])

        raise InvalidArgumentError("cant resolve any environment. "
                                   "Either pass an environment in app "
                                   "config file or explicitly in 'ndeploy deploy' command")