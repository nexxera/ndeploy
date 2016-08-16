import json
import shutil
from subprocess import call
import os.path
from ndeploy.model import App, Environment
from ndeploy.exception import InvalidArgumentError, AppConfigFileCloneError


class Deployer:
    """
    Classe responsável por resolver os parâmetros do deploy e chamar o provider para fazer o deploy
    """

    def __init__(self, provider_repository, env_repository):
        self.provider_repository = provider_repository
        self.env_repository = env_repository

    def deploy(self, file=None, group=None, name=None, environment=None):
        """
        Método responsável por tratar os parâmetros passados pelo
        usuário e tentar fazer o deploy da aplicação.

        Args:
            file (str): path do arquivo json de configuração da app (optional)
            group (str): grupo da aplicação (optional, caso não seja passado o file)
            name (str): nome da aplicação (optional, caso não seja passado o file)
            environment (str): nome do environment onde será feito o deploy (optional)
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

    def _get_remote_conf(self, repo_url, relative_path, rsa_path):

        local_folder = os.path.join(
            self.env_repository.get_ndeploy_dir(), "tmp")

        if os.path.isdir(local_folder):
            shutil.rmtree(local_folder)

        os.makedirs(local_folder)

        print("getting config file from " + repo_url)

        os.system("ssh-agent bash -c 'ssh-add {rsa_path}; git clone {repo_url} {local_folder}'"
             .format(rsa_path=rsa_path, repo_url=repo_url, local_folder=local_folder))

        cloned_file = os.path.join(local_folder, relative_path)
        if not os.path.isfile(cloned_file):
            raise AppConfigFileCloneError(repo_url, cloned_file)

        with open(cloned_file) as json_data:
            app_data = json.load(json_data)

        return app_data

    def _resolve_remote_app_file(self, group, name, environment):
        assert environment
        assert group

        rsa_key = self.env_repository.get_env_private_key_path(environment.name)
        repo_url = environment.app_deployment_file_url.format(group=group)
        app_data = self._get_remote_conf(repo_url, name + ".json", rsa_key)

        return app_data

    def _resolve_app(self, app_data, group, name, environment):

        if not app_data:
            app_data = self._resolve_remote_app_file(group, name, environment)

        assert app_data

        if "environment" in app_data:
            app_data.pop("environment")

        return App(**app_data)

    def _resolve_environment(self, app_data, environment):

        if environment and self.env_repository.has_environment(environment):
            return self.env_repository.load_environment(environment)

        if app_data and "environment" in app_data:
            env = app_data["environment"]
            return Environment(env["type"], env["name"],
                               env["deploy_host"])

        raise InvalidArgumentError("cant resolve any environment. "
                                   "Either pass an environment in app "
                                   "config file or explicitly in 'ndeploy deploy' command")