import unittest

from unittest import mock

from ndeploy import core
from ndeploy.model import Environment


class EnvironmentTest(unittest.TestCase):
    """
    Test ndeploy functions.
    """

    def setUp(self):
        self.env_repo = mock.MagicMock()
        self.deployer = mock.MagicMock()
        self.core = core.NDeployCore(self.env_repo, self.deployer)

    def test_add_environments_should_call_environment_repository(self):
        self.core.add_environment("dokku", "dummy", "integrated-dev.nexxera.com",
                                  "git@gitlab.nexxera.com:/group/my-app.git")

        self.assertEqual(1, self.env_repo.add_environment.call_count)
        env_called = self.env_repo.add_environment.call_args[0][0]
        self.assertEqual(env_called.__dict__, Environment("dummy", "dokku", "integrated-dev.nexxera.com",
                                                          "git@gitlab.nexxera.com:/group/my-app.git").__dict__)

    def test_list_environments_should_call_environment_repository(self):
        self.core.list_environments_as_str()
        self.assertEqual(1, self.env_repo.list_environments_as_str.call_count)

    def test_remove_environments_should_call_environment_repository(self):
        self.core.remove_environment("dummy")
        self.env_repo.remove_environment.assert_called_once_with("dummy")

    def test_update_environment_should_call_environment_repository(self):
        self.core.update_environment("dummy", "dokku", "i.com", "git@git.com")
        self.assertEqual(1, self.env_repo.update_environment.call_count)
        env_called = self.env_repo.update_environment.call_args[0][0]
        self.assertEqual(env_called.__dict__,
                         Environment("dokku", "dummy", "i.com", "git@git.com").__dict__)

    def test_deploy_should_call_deployer(self):
        self.core.deploy("file", "name", "group", "environment")
        self.deployer.deploy.assert_called_once_with("file", "name", "group", "environment")



