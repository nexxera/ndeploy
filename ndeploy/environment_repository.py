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


DIR_ENVS = os.environ['HOME']+"/.ndeploy"
FILE_ENVS = DIR_ENVS + "/environments.json"


class EnvironmentRepository:
    """
    Classe responsável por gerenciar environments dentro do ndeploy
    """

    def __init__(self):
        self.environments = self._load_environments_dict()

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

        self.environments.append(environment)
        self._save_environments()

    def remove_environment(self, name):
        """
        Remove o Environment informado e salva o arquivo de environments
        Args:
            name: Nome do Environment a ser removido.

        Returns:

        """
        # enviroments = _load_environments_dict()

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
        # _enviroments = _load_environments_dict()
        # environments = []
        #
        # for _environment in self.environments:
        #     environment = Environment(**_environment)
        #     environments.append(environment)
        #
        # return environments

    def load_environment(self, name):
        """
        Carrega um Environment específico que esteja salvo.
        Args:
            name: Nome do Environment a ser carregado.

        Returns: Objeto Environment com os dados salvos.

        """
        # enviroments = _load_environments_dict()

        for env in self.environments:
            if env.name == name:
                return env

        return None

    def has_environment(self, name):
        return self.load_environment(name) is not None

    @staticmethod
    def _load_environments_dict():
        """
        Carrega os Environments salvos.
        Returns: Lista de dicionários com dados salvos.

        """
        env_list = []
        if os.path.isfile(FILE_ENVS):
            json_data = open(FILE_ENVS).read()
            data = json.loads(json_data, object_hook=lambda j: Environment(**j))
            env_list = data
        return env_list

    def _save_environments(self):
        """
        Salva os Environments no arquivo local de persistência no formato Json.

        Returns:

        """
        if not os.path.isdir(DIR_ENVS):
            os.makedirs(DIR_ENVS)

        with open(FILE_ENVS, 'w+') as fp:
            json_data = json.dumps(self.environments, default=lambda o: o.__dict__);
            fp.write(json_data)
            fp.close()
