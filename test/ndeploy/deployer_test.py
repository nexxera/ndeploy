import unittest
import os
import json
from unittest import mock

from ndeploy.exception import InvalidArgumentError, BadFormedRemoteAppFileUrlError
from ndeploy.deployer import Deployer
from ndeploy.model import Environment


class DeployerTest(unittest.TestCase):

    def setUp(self):
        self.provider_repo = mock.MagicMock()
        self.env_repo = mock.MagicMock()
        self.deployer = Deployer(self.provider_repo, self.env_repo)

        self.mocked_provider = mock.MagicMock()
        self.provider_repo.get_provider_for.return_value = self.mocked_provider

    def test_deploy_should_fail_if_no_environment_is_passed(self):
        with self.assertRaises(expected_exception=InvalidArgumentError):
            self.deployer.deploy(os.path.join(os.path.dirname(__file__), '../resources', 'app.json'))

    def test_deploy_should_fail_if_invalid_environment_is_passed(self):

        with self.assertRaises(expected_exception=InvalidArgumentError):
            self.env_repo.has_environment.side_effect = lambda e: e != "invalid"
            self.deployer.deploy(file=os.path.join(os.path.dirname(__file__), '../resources', 'app.json'),
                                 environment="invalid")

    def test_deploy_should_accept_local_config_file_with_env(self):
        local_file = os.path.join(os.path.dirname(__file__), '../resources', 'app_with_env.json')

        self.deployer.deploy(file=local_file)
        self._assert_deploy_call("my-app", "super-app", "dev", "dev.nexxera.com", "dokku")

    def _configure_env(self, name, host, _type, url):
        self.env_repo.has_environment.side_effect = lambda e: e == _type
        self.env_repo.load_environment.side_effect = lambda e: Environment(_type, name, host, url) if e == _type else None

    def test_deploy_with_file_and_registered_env(self):
        local_file = os.path.join(os.path.dirname(__file__), '../resources', 'app.json')
        self._configure_env("qa", "qa.nexxera.com", "openshift", "url")

        self.deployer.deploy(file=local_file, environment="openshift")

        self._assert_deploy_call("my-app", "super-app", "qa", "qa.nexxera.com", "openshift")

    def test_deploy_with_group_name_without_env_should_fail(self):
        with self.assertRaises(expected_exception=InvalidArgumentError):
            self.deployer.deploy(group="group", name="app")

    @mock.patch("ndeploy.deployer.Deployer._get_remote_conf")
    def test_deploy_with_group_name_and_registered_env(self, _get_remote_conf):
        _get_remote_conf.return_value = {"name": "app", "deploy_name": "financial"}
        self._configure_env("qa", "qa.nexxera.com", "openshift",
                            "git@git.nexxera.com:environment-conf-qa/{group}.git master {name}.json")
        self.deployer.deploy(group="financial-platform", name="financial-platform-core",
                             environment="openshift")

        self._assert_deploy_call("app", "financial", "qa", "qa.nexxera.com", "openshift")

    @mock.patch("ndeploy.deployer.Deployer._get_remote_conf")
    def test_should_raise_exception_if_remote_app_url_is_bad_formed(self, _get_remote_conf):
        _get_remote_conf.return_value = {"name": "app", "deploy_name": "financial"}
        with self.assertRaises(BadFormedRemoteAppFileUrlError):
            self._configure_env("qa", "qa.nexxera.com", "openshift",
                                "git@git.nexxera.com:environment-conf-qa/{group}.git")
            self.deployer.deploy(group="financial-platform", name="financial-platform-core",
                                 environment="openshift")

    def _assert_deploy_call(self, expected_app_name, expected_app_deploy_name,
                            expected_env_name, expected_env_deploy_host, expected_env_type):
        self.provider_repo.get_provider_for.assert_called_with(expected_env_type)
        self.assertEqual(1, self.mocked_provider.deploy.call_count)

        app_called = self.mocked_provider.deploy.call_args[0][0]
        env_called = self.mocked_provider.deploy.call_args[0][1]
        self._assertApp(expected_app_name, expected_app_deploy_name, app_called)
        self._assertEnv(expected_env_name, expected_env_deploy_host, expected_env_type, env_called)

    def _assertApp(self, expected_name, expected_deploy_name, app):
        self.assertEqual(expected_name, app.name)
        self.assertEqual(expected_deploy_name, app.deploy_name)

    def _assertEnv(self, expected_name, expected_deploy_host, expected_type, env):
        self.assertEqual(expected_name, env.name)
        self.assertEqual(expected_deploy_host, env.deploy_host)
        self.assertEqual(expected_type, env.type)

    def _assert_json(self, _dict, json_file):
        with open(json_file) as json_data:
            loaded_dict = json.load(json_data)
            self.assertEqual(loaded_dict, _dict)
