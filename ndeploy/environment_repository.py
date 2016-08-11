"""
Repositório para persistencia dos dados referentes ao Environment.
Há implementação apenas para inserir, apagar e listar.
Não há como atualizar os dados, se necessário usuário deve apagar e inserir um environment novo.
Posteriormente pode-se implementar a atualização, mas não é algo tão necessário.
"""
import json
import os
import sys
from ndeploy.model import Environment
from ndeploy.shell_exec import ShellExec


class EnvironmentRepository:
    """
    Classe responsável por gerenciar environments dentro do ndeploy
    """

    def __init__(self, ndeploy_dir):
        self.ndeploy_dir = ndeploy_dir
        self.environments = self._load_environments_dict()
        self._configure_dir()

    def _configure_dir(self):
        os.makedirs(self.ndeploy_dir, exist_ok=True)
        ssh_path = os.path.join(self.ndeploy_dir, ".ssh")
        os.makedirs(ssh_path, exist_ok=True)

    def get_ndeploy_dir(self):
        """
        Retorna o path do diretório de configurações do ndeploy
        Returns:
            Caminho para o diretório de configurações do ndeploy
        """
        return self.ndeploy_dir

    def get_environments_file(self):
        """
        Retorna o caminho do arquivo json de environments do ndeploy
        Returns:
            Caminho para o 'environments.json', onde ficam persistidos os environments
        """
        return os.path.join(self.get_ndeploy_dir(), "environments.json")

    def add_environment(self, environment):
        """
        Adiciona um novo Environment e salva o arquivo de environments
        Args:
            environment: Environment a ser salvo

        Returns:

        """
        # self.enviroments = _load_environments_dict()

        for _environment in self.environments:
            if _environment.name == environment.name:
                sys.exit('Environment already exists!')

        self._generate_rsa_for_env(environment.name)
        self.environments.append(environment)
        self._save_environments()

    def get_environment_key(self, name):
        with open(self.get_env_public_key_path(name)) as file:
            return file.read()

        return None

    def get_env_public_key_path(self, env_name):
        return self.get_env_private_key_path(env_name) + ".pub"

    def get_env_private_key_path(self, env_name):
        return os.path.join(self.get_ndeploy_dir(), ".ssh", "id_rsa_" + env_name)

    def _generate_rsa_for_env(self, env):
        rsa_file_path = self.get_env_private_key_path(env)
        ShellExec.execute_program("ssh-keygen -f {path} -t rsa -N '' -q"
                                  .format(path=rsa_file_path), True)

    def remove_environment(self, name):
        """
        Remove o Environment informado e salva o arquivo de environments
        Args:
            name: Nome do Environment a ser removido.

        Returns:

        """
        for _environment in self.environments:
            if _environment.name == name:
                self.environments.remove(_environment)

        self._save_environments()

    def list_environments(self):
        """
        Carrega os Environments salvos.
        Returns: Lista de objetos do tipo Environment

        """
        return self.environments

    def load_environment(self, name):
        """
        Carrega um Environment específico que esteja salvo.
        Args:
            name: Nome do Environment a ser carregado.

        Returns: Objeto Environment com os dados salvos.

        """
        for env in self.environments:
            if env.name == name:
                return env

        return None

    def has_environment(self, name):
        return self.load_environment(name) is not None

    def _load_environments_dict(self):
        """
        Carrega os Environments salvos.
        Returns: Lista de dicionários com dados salvos.

        """
        env_list = []
        if os.path.isfile(self.get_environments_file()):
            json_data = open(self.get_environments_file()).read()
            data = json.loads(json_data, object_hook=lambda j: Environment(**j))
            env_list = data
        return env_list

    def _save_environments(self):
        """
        Salva os Environments no arquivo local de persistência no formato Json.

        Returns:

        """
        if not os.path.isdir(self.get_ndeploy_dir()):
            os.makedirs(self.get_ndeploy_dir())

        with open(self.get_environments_file(), 'w+') as fp:
            json_data = json.dumps(self.environments, default=lambda o: o.__dict__);
            fp.write(json_data)
            fp.close()
