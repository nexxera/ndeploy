import json
import shutil
import git
from subprocess import call
import os.path
from ndeploy.model import App, Environment
from ndeploy.exception import InvalidArgumentError, AppConfigFileCloneError


class Deployer:
    """
    Classe responsável por resolver os parâmetros do deploy e chamar o paas para fazer o deploy
    """

    def __init__(self, paas_repository, env_repository):
        self.paas_repository = paas_repository
        self.env_repository = env_repository

    def deploy(self, file=None, group=None, name=None, environment=None):
        """
        Método responsável por tratar os parâmetros passados pelo usuário e tentar fazer o deploy da aplicação.

        :param file:
        :param group:
        :param name:
        :param environment:
        :return:
        """
        app_data = None

        if file:
            with open(file) as json_data:
                app_data = json.load(json_data)

        env = self._resolve_environment(app_data, environment)
        assert env is not None

        app = self._resolve_app(app_data, group, name, env)
        assert app is not None

        self.paas_repository.get_paas_for(env.type).deploy(app, env)

    def _get_remote_conf(self, repo_url, relative_path, rsa_path):

        local_folder = "tmp"

        if os.path.isdir(local_folder):
            shutil.rmtree(local_folder)

        print("getting config file from " + repo_url)
        # git.Repo.clone_from(repo_url, "tmp")
        call(["ssh-agent", "bash", "-c", "'ssh-add {rsa_path}; git clone {repo_url} {local_folder}'"
             .format({"rsa_path": rsa_path, "repo_url": repo_url, "local_folder": local_folder})])

        cloned_file = os.path.join("tmp", relative_path)
        if not os.path.isfile(cloned_file):
            raise AppConfigFileCloneError(repo_url, cloned_file)

        with open(cloned_file) as json_data:
            app_data = json.load(json_data)

        return app_data

    def _resolve_remote_app_file(self, group, name, environment):
        assert environment
        assert group

        rsa_key = self.env_repository.get_env_private_key_path(environment.name)
        repo_url = environment.app_deployment_file_url.format(group)
        app_data = self._get_remote_conf(repo_url, os.path.join(name, "app.json"), rsa_key)

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
                               env["deploy-host"])

        raise InvalidArgumentError("cant resolve any environment. "
                                   "Either pass an environment in app "
                                   "config file or explicitly in 'ndeploy deploy' command")