import json
import os.path
import tempfile

import yaml
from ndeploy.git_exec import GitExec, GitExecError
from yaml.parser import ParserError

from ndeploy.model import App, Environment
from ndeploy.exception import InvalidArgumentError, \
    AppConfigFileCloneError, InvalidEnvironmentFileError


class Deployer:
    """
    Class responsible for resolving the deploy configurations and
    delegating to a provider to do deploy.
    """
    NDEPLOY_TEMPLATE_FILE = 'ndeploy'
    CONFIG_FILE_FORMAT_SUPPORTED = ['json', 'yaml']

    def __init__(self, provider_repository, env_repository):
        """
        Constructor.
        Args:
            provider_repository (provider.ProviderRepository):
            env_repository (environment_repository.EnvironmentRepository):
        """
        self.provider_repository = provider_repository
        self.env_repository = env_repository
        self._app_data_template = None

    def deploy(self, file=None, group=None, name=None, environment=None):
        """
        Resolves the user parameters and deploys apps in an environment.

        The apps configuration will be resolved locally if `file` parameter
        was passed or in a remote git repository with the url configured
        in the environment (@see ndeploy.model.Environment.app_deployment_file_url)

        If remotely the url will be formatted with `group` and `name` args.

        Args:
            file (str): path to the local json configuration file
            group (str): app group
            name (str): app name
            environment (str): environment name where the apps will be deployed
        """
        if not file and (not group or not name):
            raise InvalidArgumentError("Could not resolve the app json file. Either pass "
                                       "the local file path with --file arg or remotely"
                                       "using --group and --name args")

        self._load_template_ndeploy_file()

        self._exec_deploy_or_undeploy(self._deploy, file, group, name, environment)

    def undeploy(self, file=None, name=None, group=None, environment=None):
        """
        Undeploys the app with `name` and `group` from `environment`

        Args:
            file (str): path to the local json configuration file
            name (str): the app name
            group (str): the app group name
            environment (str): the environment name

        """
        if not file and (not group or not name):
            raise InvalidArgumentError("Could not resolve the app json file. Either pass "
                                       "the local file path with --file arg or remotely"
                                       "using --group and --name args")

        self._exec_deploy_or_undeploy(self._undeploy, file, group, name, environment)

    def _exec_deploy_or_undeploy(self, undeploy_deploy_callback, file, group, name, environment):
        """
        Execute the flow needed to undeploy or deploy the applications
        The actual undeploy or deploy must be done by the 'undeploy_deploy_callback'

        Args:
            undeploy_deploy_callback (fn): function that makes the undeploy or deploy
            file (str): path to the local json configuration file
            group (str): the app group name
            name (str): the app name
            environment (str): the environment name
        """
        env, data_in_json = self._resolve_apps_data_and_env(file, group, name, environment)

        if data_in_json and 'apps' in data_in_json:
            for index, item_data in enumerate(data_in_json['apps'], start=1):
                print("...Application {}/{}...".format(index, len(data_in_json['apps'])))
                undeploy_deploy_callback(env, item_data, group, name)
        else:
            undeploy_deploy_callback(env, data_in_json, group, name)

    def _deploy(self, env, item_data, group, app_name):
        """
        Deploy an application session

        Args:
            env (class): Environment for deploy
            item_data (dict): dict containing app data from existing file
            group (str): app group name
            app_name (str): app name
        """
        app, provider = self._resolve_app_and_provider(env, group, app_name, item_data)
        provider.deploy(app, env)

    def _undeploy(self, env, item_data, group, name):
        """
        Undeploy an application session

        Args:
            env (class): Environment for deploy
            item_data (dict): dict containing app data from existing file
            group (str): app group name
            name (str): app name
        """
        app, provider = self._resolve_app_and_provider(env, group, name, item_data)
        provider.undeploy(app, env)

    def _resolve_apps_data_and_env(self, file, group, app_name, env_name):
        """
        Resolves the app, env and provider object for this deploy/undeploy session

        Args:
            file: app configuration file
            group (str): app group name
            app_name (str): app name
            env_name (str): environment name

        Returns:
           Tuple containing (Environment, App)

        """
        apps_data = None
        if file:
            apps_data = self._resolve_environment_file(file)

        env = self._resolve_environment(apps_data, env_name)
        assert env is not None

        if not apps_data:
            apps_data = self._resolve_remote_app_file(group, app_name, env)
        assert apps_data is not None

        return env, apps_data

    def _resolve_app_and_provider(self, env, group, app_name, app_data):
        """
        Resolves the app, env and provider object for this deploy/undeploy session

        Args:
            env (class): Environment for deploy
            group (str): app group name
            app_name (str): app name
            app_data (dict): dict containing app data from existing file (optional)

        Returns:
            Tuple containing (Environment, App, AbstractProvider)
        """
        app = self._resolve_app(app_data, group, app_name, env)
        assert app is not None

        provider = self._resolve_provider(env)
        assert provider is not None

        return app, provider

    @staticmethod
    def _exec_git_clone_archive(rsa_path, repo_url, branch, local_folder, file_relative_path):
        """
        Download the remote configuration file in a git repository

        Args:
            rsa_path (str): path to the repo rsa private key
            repo_url (str): the remote repo url
            branch (str): git branch name
            local_folder (str): the path of the temporary dir to the ndeploy
            file_relative_path (str): the path of the file relative to the repo root

        Returns:
            full path for the downloaded file
        """
        try:
            return GitExec.archive_clone(rsa_path, repo_url, branch, local_folder, file_relative_path)
        except GitExecError as e:
            print(e)
            raise AppConfigFileCloneError(repo_url, "{}/{}".format(local_folder, file_relative_path))

    def _get_remote_and_resolve_conf_file(self, repo_url, branch, file_relative_path, rsa_path):
        """
        Gets the remote app configuration file in a git repository

        Args:
            repo_url (str): the remote repo url
            branch (str): git branch name
            file_relative_path (str): the path of the file relative to the repo root
            rsa_path (str): path to the repo rsa private key

        Returns:
            dict containing the contents of the remote config file
        """
        local_folder = os.path.join(self.env_repository.get_ndeploy_dir(), "tmp")
        if not os.path.isdir(local_folder):
            os.makedirs(local_folder)

        print("...Getting remote app config file from " + repo_url)

        with tempfile.TemporaryDirectory(dir=local_folder) as temporary_dir:
            try:
                cloned_file = self._exec_git_clone_archive(rsa_path, repo_url, branch,
                                                           temporary_dir, file_relative_path)
            except AppConfigFileCloneError:
                file_name, file_extension = file_relative_path.split('.')
                new_file_extension = 'yaml' if file_extension == 'json' else 'json'
                file_relative_path = '{}.{}'.format(file_name, new_file_extension)
                cloned_file = self._exec_git_clone_archive(rsa_path, repo_url, branch,
                                                           temporary_dir, file_relative_path)

            print("...Successfully downloaded remote app config file")
            return self._resolve_environment_file(cloned_file)

    def _resolve_remote_app_file(self, group, name, env):
        """
        Resolves the remote app configuration file.
        Will download from a git repository configured in the environment.
        (@see ndeploy.model.Environment.app_deployment_file_url)

        Args:
            group (str): the app group
            name (str): the app name
            env (class): Environment for deploy

        Returns:
            dict containing the contents of remote configuration json

        """
        assert env
        assert group

        rsa_key = self.env_repository.get_env_private_key_path(env.name)
        repo_url, branch, file_relative_path = env.format_remote_deployment_file_url(group, name)
        return self._get_remote_and_resolve_conf_file(repo_url, branch, file_relative_path, rsa_key)

    def _resolve_app(self, app_data, group, name, env):
        """
        Resolves the app deploy configuration locally or remotely.
        Will try to resolve remotely (in a git repo) only if `app_data` is None

        Args:
            app_data (dict): the app data (if None will try to get remotely)
            group (str): the app group name (will be used only if `app_data` is None)
            name (str): the app name (will be used only if `app_data` is None)
            env (class): Environment for deploy

        Returns:
            ndeploy.model.App object

        """
        if not app_data:
            app_data = self._resolve_remote_app_file(group, name, env)

        assert app_data

        if "environment" in app_data:
            app_data.pop("environment")

        return App(**app_data)

    def _resolve_provider(self, env):
        """
        Resolves the provider deploy configuration and returns an instance

        Args:
            env (class): Environment for deploy

        Returns:
            implementation ndeploy.provider.AbstractProvider object

        """
        return self.provider_repository.get_provider_for(env.type)

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

    @staticmethod
    def _load_file_to_dict(file):
        """
        Load config file and return a dict with items

        Args:
            file: configuration file json, yaml
        Returns:
            dict with file items
        """
        try:
            with open(file) as content_data:
                if content_data.name.endswith(".json"):
                    config_data = json.load(content_data)
                elif content_data.name.endswith(".yaml"):
                    config_data = yaml.load(content_data)
                else:
                    raise ValueError("Invalid config file format")

                return config_data
        except (ValueError, ParserError) as e:
            raise InvalidEnvironmentFileError(file, e)

    def _load_template_ndeploy_file(self):
        """
        Load local template file ndeploy.json

        """
        cwd = os.getcwd() + os.sep
        full_path_template = "{0}{1}".format(cwd, self.NDEPLOY_TEMPLATE_FILE)
        if os.path.exists('{}.json'.format(full_path_template)):
            self._app_data_template = self._load_file_to_dict('{}.json'.format(full_path_template))
        elif os.path.exists('{}.yaml'.format(full_path_template)):
            self._app_data_template = self._load_file_to_dict('{}.yaml'.format(full_path_template))

    def _resolve_environment_file(self, file):
        """
        Resolves environment config file, template local ndeploy.json and parameter file,
        and return a dict with file items

        Args:
            file: configuration file

        Returns:
            dict with file items
        """
        app_data_load = self._load_file_to_dict(file)

        if self._app_data_template:
            print("...Merge local settings with remote...")
            return self._deep_merge_two_dict(self._app_data_template, app_data_load)

        return app_data_load

    def _deep_merge_two_dict(self, dict1, dict2, in_conflict=lambda v1, v2: v2):
        """
        Merge dict2 into dict1, using in_conflict function to resolve the leaf conflicts

        Args:
            dict1: dictionary initial
            dict2: dictionary to merge

        Returns:
            new merged dict
        """

        for k in dict2:
            if k in dict1:
                if isinstance(dict1[k], dict) and isinstance(dict2[k], dict):
                    self._deep_merge_two_dict(dict1[k], dict2[k], in_conflict)
                elif dict1[k] != dict2[k]:
                    dict1[k] = in_conflict(dict1[k], dict2[k])
            else:
                dict1[k] = dict2[k]
        return dict1
