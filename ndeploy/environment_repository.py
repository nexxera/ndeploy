"""
Repositório para persistencia dos dados referentes ao Environment.
Há implementação apenas para inserir, apagar e listar.
Não há como atualizar os dados, se necessário usuário deve apagar e inserir um environment novo.
Posteriormente pode-se implementar a atualização, mas não é algo tão necessário.
"""
import json
import os
from ndeploy.model import Environment
from ndeploy.exception import EnvironmentAlreadyExistsError, \
    EnvironmentDoesNotExistError


class EnvironmentRepository:
    """
    Manages the environments inside ndeploy

    """
    def __init__(self, ndeploy_dir, shell_exec):
        self.ndeploy_dir = ndeploy_dir
        self.environments = self._load_environments_dict()
        self._configure_dirs()
        self.shell_exec = shell_exec

    def add_environment(self, environment):
        """
        Adds a new environment in the repository and persists to file

        Args:
            environment: Environment object to be saved

        """
        if self.has_environment(environment.name):
            raise EnvironmentAlreadyExistsError(environment.name)

        self._generate_rsa_for_env(environment.name)
        self.environments.append(environment)
        self._save_environments()

    def update_environment(self, env):
        """
        Updates an environment in the repository and persists to file.
        The env name will be preserved.

        Raises:
            EnvironmentDoesNotExistError: if the env.name passed as parameter
                does not exist in the repository

        Args:
            env (Environment): the env with updated data
        """
        if not self.has_environment(env.name):
            raise EnvironmentDoesNotExistError(env.name)

        to_update = self.load_environment(env.name)
        to_update.update(env)
        self._save_environments()

    def get_environment_key(self, name):
        """
        Returns the content of the public rsa key of the env

        Args:
            name (str): env name

        Returns:
            str containing the environment public rsa key
        """
        with open(self.get_env_public_key_path(name)) as file:
            return file.read()

        return None

    def get_env_public_key_path(self, env_name):
        """
        Returns the environment public key file path

        Args:
            env_name (str): the name of environment

        Returns:
            str containing the full path of public key file
        """
        return self.get_env_private_key_path(env_name) + ".pub"

    def get_env_private_key_path(self, env_name):
        """
        Returns the environment private key file path

        Args:
            env_name (str): the name of environment

        Returns:
            str containing the full path of private key file
        """
        return os.path.join(self.get_ndeploy_dir(), ".ssh", "id_rsa_" + env_name)

    def _generate_rsa_for_env(self, env_name):
        """
        Generates the public and private rsa pair for the environment.
        Will generate in the ndeploy keys folder with the openssh format.

        Args:
            env_name (str): the environment name

        """
        rsa_file_path = self.get_env_private_key_path(env_name)
        self.shell_exec.execute_program("ssh-keygen -f {path} -t rsa -N '' -q"
                                        .format(path=rsa_file_path), True)

    def remove_environment(self, env_name):
        """
        Removes the environment off the repository, persisting in
        the environments file.

        Args:
            env_name: Nome do Environment a ser removido.
        """
        for _environment in self.environments:
            if _environment.name == env_name:
                self.environments.remove(_environment)

        self._save_environments()

    def list_environments(self):
        """
        Returns the saved environments

        Returns:
            list of Environment objects
        """
        return self.environments

    def list_environments_as_str(self):
        environments = self.list_environments()
        if len(environments) == 0:
            return "There is no registered environment."

        result = "\n".join("name:%s, \ttype:%s, \tdeploy_host:%s"
                  % (env.name, env.type, env.deploy_host) for env in environments)

        return result

    def load_environment(self, env_name):
        """
        Gets an existing environment by name
            or None if it doesn't exist.

        Args:
            env_name (str): the environment name

        Returns:
            Environment object or None if it doesn't exist
        """
        for env in self.environments:
            if env.name == env_name:
                return env

        return None

    def has_environment(self, env_name):
        """
        Verifies if environment exists in the repository.

        Args:
            env_name (str): the environment name

        Returns:
            True if environment exists, False otherwise
        """
        return self.load_environment(env_name) is not None

    def _load_environments_dict(self):
        """
        Loads the environments persisted in the environments.json file

        Returns:
            list of dict containing the environments data
        """
        env_list = []
        if os.path.isfile(self.get_environments_file()):
            with open(self.get_environments_file()) as file:
                json_data = file.read()
                data = json.loads(json_data,
                                  object_hook=lambda j: Environment(**j))
                env_list = data
        return env_list

    def _save_environments(self):
        """
        Saves the environments in the json environments file

        """
        if not os.path.isdir(self.get_ndeploy_dir()):
            os.makedirs(self.get_ndeploy_dir())

        with open(self.get_environments_file(), 'w+') as fp:
            json_data = json.dumps(self.environments, default=lambda o: o.__dict__);
            fp.write(json_data)
            fp.close()

    def _configure_dirs(self):
        """
        Creates the folders needed by this class

        """
        os.makedirs(self.ndeploy_dir, exist_ok=True)
        ssh_path = os.path.join(self.ndeploy_dir, ".ssh")
        os.makedirs(ssh_path, exist_ok=True)

    def get_ndeploy_dir(self):
        """
        Returns the ndeploy home directory
        Returns:
            str containing ndeploy home dir
        """
        return self.ndeploy_dir

    def get_environments_file(self):
        """
        Returns the environments json file
        Returns:
            str containing full path of environments.json file
        """
        return os.path.join(self.get_ndeploy_dir(), "environments.json")

