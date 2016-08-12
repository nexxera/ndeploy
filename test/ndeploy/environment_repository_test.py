import json
import os
import unittest
import shutil

from ndeploy.environment_repository import EnvironmentRepository
from ndeploy.model import Environment
from ndeploy.exception import EnvironmentAlreadyExistsError
from unittest.mock import MagicMock


class EnvironmentTest(unittest.TestCase):
    """
    Test ndeploy functions.
    """

    def setUp(self):
        self.ndeploy_dir = os.environ['HOME'] + "/.ndeploy-tmp"

        if os.path.isdir(self.ndeploy_dir):
            shutil.rmtree(self.ndeploy_dir)

        self.shell_exec = MagicMock()
        self.env_repo = EnvironmentRepository(self.ndeploy_dir, self.shell_exec)

    def test_add_environments(self):

        self._add_integrated_dev_environment()

        file = os.path.join(os.path.dirname(__file__), '../resources', 'model_environments.json')
        json_data_expected = open(file).read()
        data_expected = json.loads(json_data_expected)

        json_data = open(self.env_repo.get_environments_file()).read()
        data = json.loads(json_data)

        os.remove(self.env_repo.get_environments_file())

        self.assertEqual(data, data_expected)

    def test_add_environment_should_create_rsa_key_with_same_name_of_env(self):
        self._add_integrated_dev_environment()

        self.shell_exec.execute_program("ssh-keygen -f {} -t rsa -N '' -q"
                                        .format(os.path.join(
                                            self.env_repo.get_ndeploy_dir(),
                                            ".ssh",
                                            "id_rsa_integrated-dev")))

    def test_list_environments(self):
        test_ndeploy_dir = os.path.join(os.path.dirname(__file__), '../resources')
        environments = EnvironmentRepository(test_ndeploy_dir, self.shell_exec)\
            .list_environments()

        self.assertEqual(len(environments), 2)

    def test_remove_environments(self):
        self._add_integrated_dev_environment()
        self._add_qa_environment()

        self.env_repo.remove_environment("qa")

        environments = self.env_repo.list_environments()

        os.remove(self.env_repo.get_environments_file())
        self.assertEqual(len(environments), 1)

    def test_load_enviroment(self):
        test_ndeploy_dir = os.path.join(os.path.dirname(__file__), '../resources')
        environment = EnvironmentRepository(test_ndeploy_dir, self.shell_exec)\
            .load_environment("dev")

        self.assertEqual(environment.type, "dokku")
        self.assertEqual(environment.deploy_host, "integrated-dev.nexxera.com")

    def test_cannot_add_two_environments_with_same_name(self):
        self._add_integrated_dev_environment()
        with self.assertRaises(EnvironmentAlreadyExistsError):
            self._add_integrated_dev_environment()

    # helpers

    def _add_integrated_dev_environment(self):
        self._add_environment(Environment(
            type="dokku",
            name="integrated-dev",
            deploy_host="integrated-dev.nexxera.com",
            app_deployment_file_url="git@gitlab.nexxera.com:group/my-app.git"))

    def _add_qa_environment(self):
        self._add_environment(Environment(
            type="openshift",
            name="qa",
            deploy_host="qa.nexxera.com",
            app_deployment_file_url="git@gitlab.nexxera.com:group/my-app.git"))

    def _add_environment(self, env):
        self.env_repo.add_environment(env)
