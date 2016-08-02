import json
import os
import unittest
import shutil

import ndeploy.environment_repository
from ndeploy import environment_repository
from ndeploy.environment_repository import EnvironmentRepository
from ndeploy.model import Environment


class EnvironmentTest(unittest.TestCase):
    """
    Test ndeploy functions.
    """

    def setUp(self):
        environment_repository.DIR_ENVS = os.environ['HOME'] + "/.ndeploy-tmp"
        environment_repository.FILE_ENVS = ndeploy.environment_repository.DIR_ENVS + "/environments.json"

        if os.path.isdir(environment_repository.DIR_ENVS):
            shutil.rmtree(environment_repository.DIR_ENVS)

        self.env_repo = EnvironmentRepository()

    def test_add_environments(self):

        self._add_environment()

        file = os.path.join(os.path.dirname(__file__), '../resources', 'model_environments.json')
        json_data_expected = open(file).read()
        data_expected = json.loads(json_data_expected)

        json_data = open(ndeploy.environment_repository.FILE_ENVS).read()
        data = json.loads(json_data)

        os.remove(ndeploy.environment_repository.FILE_ENVS)

        self.assertEqual(data, data_expected)

    def _add_environment(self):

        environment = Environment(
            type="dokku",
            name="integrated-dev",
            deploy_host="integrated-dev.nexxera.com",
            app_deployment_file_url="git@gitlab.nexxera.com:group/my-app.git")
        self.env_repo.add_environment(environment)

    def test_list_environments(self):

        environment_repository.DIR_ENVS = os.path.join(os.path.dirname(__file__), '../resources')
        environment_repository.FILE_ENVS = ndeploy.environment_repository.DIR_ENVS + "/environments.json"

        environments = EnvironmentRepository().list_environments()

        self.assertEqual(len(environments), 2)

    def test_remove_environments(self):
        self._add_environment()

        environment_qa = Environment(
            type="openshift",
            name="qa",
            deploy_host="qa.nexxera.com",
            app_deployment_file_url="git@gitlab.nexxera.com:group/my-app.git")
        self.env_repo.add_environment(environment_qa)

        self.env_repo.remove_environment("qa")

        environments = self.env_repo.list_environments()

        os.remove(ndeploy.environment_repository.FILE_ENVS)
        self.assertEqual(len(environments), 1)

    def test_load_enviroment(self):
        environment_repository.DIR_ENVS = os.path.join(os.path.dirname(__file__), '../resources')
        environment_repository.FILE_ENVS = ndeploy.environment_repository.DIR_ENVS + "/environments.json"

        environment = EnvironmentRepository().load_environment("dev")

        self.assertEqual(environment.type, "dokku")
        self.assertEqual(environment.deploy_host, "integrated-dev.nexxera.com")
