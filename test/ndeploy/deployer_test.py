import unittest
import os
import json
from unittest import mock

from ndeploy.exception import InvalidArgumentError, BadFormedRemoteConfigUrlError, InvalidEnvironmentFileError
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
        for file in ['app.json', 'app.yaml']:
            with self.assertRaises(expected_exception=InvalidArgumentError):
                self.deployer.deploy(os.path.join(os.path.dirname(__file__), '../resources', file))

    def test_deploy_should_fail_if_invalid_environment_is_passed(self):
        for file in ['app.json', 'app.yaml']:
            with self.assertRaises(expected_exception=InvalidArgumentError):
                self.env_repo.has_environment.side_effect = lambda e: e != "invalid"
                self.deployer.deploy(file=os.path.join(os.path.dirname(__file__), '../resources', file),
                                     environment="invalid")

    def test_deploy_should_fail_if_file_group_and_name_is_not_passed(self):
        with self.assertRaises(expected_exception=InvalidArgumentError):
            self.deployer.deploy(environment="dev")

    def test_deploy_should_fail_if_group_or_name_is_not_passed(self):
        with self.assertRaises(expected_exception=InvalidArgumentError):
            self.deployer.deploy(group="mygroup", environment="dev")

        with self.assertRaises(expected_exception=InvalidArgumentError):
            self.deployer.deploy(name="myapp", environment="dev")

    def test_deploy_should_accept_local_config_file_with_env(self):
        local_file = os.path.join(os.path.dirname(__file__), '../resources', 'app_with_env.json')

        self.deployer.deploy(file=local_file)
        self._assert_deploy_call("my-app", "super-app", "dev", "dev.nexxera.com", "dokku")

    def test_deploy_with_file_and_registered_env(self):
        local_file = os.path.join(os.path.dirname(__file__), '../resources', 'app.json')
        self._configure_env("qa", "qa.nexxera.com", "openshift", None)

        self.deployer.deploy(file=local_file, environment="qa")

        self._assert_deploy_call("my-app", "super-app", "qa", "qa.nexxera.com", "openshift")

    def test_deploy_with_group_name_without_env_should_fail(self):
        with self.assertRaises(expected_exception=InvalidArgumentError):
            self.deployer.deploy(group="group", name="app")

    @mock.patch("ndeploy.deployer.Deployer._get_remote_conf")
    def test_deploy_with_group_name_and_registered_env(self, _get_remote_conf):
        local_file = os.path.join(os.path.dirname(__file__), '../resources', 'app_with_env.json')
        _get_remote_conf.return_value = local_file
        self._configure_env("dev", "dev.nexxera.com", "dokku",
                            "git@git.nexxera.com:environment-conf-dev/{group}.git master {name}.json")
        self.deployer.deploy(group="financial-platform", name="financial-platform-core", environment="dev")

        data_config = self._load_json_to_dict(local_file)
        self._assert_deploy_call(data_config["name"], data_config["deploy_name"],
                                 data_config["environment"]["name"],
                                 data_config["environment"]["deploy_host"],
                                 data_config["environment"]["type"])

    @mock.patch("ndeploy.deployer.Deployer._get_remote_conf")
    def test_should_raise_exception_if_remote_app_url_is_bad_formed(self, _get_remote_conf):
        # _get_remote_conf.return_value = {"name": "app", "deploy_name": "financial"}
        with self.assertRaises(BadFormedRemoteConfigUrlError):
            self._configure_env("qa", "qa.nexxera.com", "openshift",
                                "git@git.nexxera.com:environment-conf-qa/{group}.git")
            self.deployer.deploy(group="financial-platform", name="financial-platform-core",
                                 environment="qa")

    def test_undeploy_from_invalid_env_should_fail(self):
        self.env_repo.has_environment.side_effect = lambda e: e != "invalid"
        with self.assertRaises(InvalidArgumentError):
            self.deployer.undeploy(name="app", group="group", environment="invalid")

    @mock.patch("ndeploy.deployer.Deployer._get_remote_conf")
    def test_undeploy_should_call_correct_provider_to_undeploy(self, mock_get_remote_conf):
        local_file = os.path.join(os.path.dirname(__file__), '../resources', 'app.json')
        mock_get_remote_conf.return_value = local_file

        self._configure_env("qa", "qa.nexxera.com", "openshift",
                            "git@git.nexxera.com:environment-conf-qa/{group}.git master {name}.json")
        self.deployer.undeploy(name="app", group="group", environment="qa")
        self._assert_undeploy_call("my-app", "super-app", "qa", "qa.nexxera.com", "openshift")

    @mock.patch("ndeploy.deployer.Deployer._get_remote_conf")
    def test_undeploy_should_accept_n_apps_in_config_file(self, mock_get_remote_conf):
        local_file = os.path.join(os.path.dirname(__file__), '../resources', 'apps.json')
        mock_get_remote_conf.return_value = local_file

        self._configure_env("dev", "dev.nexxera.com", "openshift",
                            "git@git.nexxera.com:environment-conf-dev/{group}.git master {name}.json")

        self.deployer.undeploy(name="app", group="group", environment="dev")
        self.assertEqual(2, self.mocked_provider.undeploy.call_count)
        self._assert_undeploy_call_list(0, "my-app", "super-my-app", "dev", "dev.nexxera.com", "openshift")
        self._assert_undeploy_call_list(1, "other-app", "super-other-app", "dev", "dev.nexxera.com", "openshift")

    def test_undeploy_should_accept_local_config_file_with_env(self):
        local_file = os.path.join(os.path.dirname(__file__), '../resources', 'app_with_env.json')

        self.deployer.undeploy(file=local_file)
        self._assert_undeploy_call("my-app", "super-app", "dev", "dev.nexxera.com", "dokku")

    def test_deploy_should_be_with_empty_environment_variable(self):
        local_file = os.path.join(os.path.dirname(__file__), '../resources', 'app_with_variable_empty.json')
        self._configure_env("qa", "qa.nexx.com", "openshift", None)

        self.deployer.deploy(file=local_file, environment="qa")
        self._assert_deploy_call("my-app", "super-app", "qa", "qa.nexx.com", "openshift")

    def test_deploy_should_be_without_environment_variable(self):
        local_file = os.path.join(os.path.dirname(__file__), '../resources', 'app_without_variable.json')
        self._configure_env("qa", "qa.nexx.com", "openshift", None)

        self.deployer.deploy(file=local_file, environment="qa")
        self._assert_deploy_call("my-app", "super-app", "qa", "qa.nexx.com", "openshift")

    @mock.patch("os.path.exists")
    @mock.patch("ndeploy.deployer.Deployer._load_template_ndeploy_file")
    @mock.patch("ndeploy.deployer.Deployer._get_remote_conf")
    def test_deploy_should_be_possible_to_merge_the_local_template_with_remote_settings(
            self, mock_get_remote_conf, mock_load_template_ndeploy_file, mock_os_exists):
        local_file = os.path.join(os.path.dirname(__file__), '../resources', 'app.json')
        mock_os_exists.return_value = True
        self.deployer._app_data_template = self._load_json_to_dict(local_file)

        remote_file = os.path.join(os.path.dirname(__file__), '../resources', 'app_remote.json')
        mock_get_remote_conf.return_value = remote_file
        remote_data_config = self._load_json_to_dict(remote_file)

        self._configure_env("qa", "qa.nexx.com", "openshift",
                            "git@git.nexx.com:environment-conf-qa/{group}.git master {name}.json")
        self.deployer.deploy(group="platform", name="platform-core", environment="qa")
        self._assert_deploy_call(remote_data_config["name"], remote_data_config["deploy_name"],
                                 "qa", "qa.nexx.com", "openshift")

    @mock.patch("os.path.exists")
    def test_deploy_should_raise_exception_if_invalid_json_file(self, mock_template_ndeploy):
        mock_template_ndeploy.return_value = False
        local_file = os.path.join(os.path.dirname(__file__), '../resources', 'invalid_json.json')
        with self.assertRaises(InvalidEnvironmentFileError):
            self._configure_env("qa", "qa.nexxera.com", "openshift", None)
            self.deployer.deploy(file=local_file, environment="qa")

    def test_deploy_should_accept_n_apps_in_config_file(self):
        local_file = os.path.join(os.path.dirname(__file__), '../resources', 'apps.json')
        self._configure_env("dev", "dev.nexxera.com", "openshift",
                            "git@git.nexxera.com:environment-conf-dev/{group}.git master {name}.json")

        self.deployer.deploy(file=local_file, environment="dev")

        self.assertEqual(2, self.mocked_provider.deploy.call_count)
        self._assert_deploy_call_list(0, "my-app", "super-my-app", "dev", "dev.nexxera.com", "openshift")
        self._assert_deploy_call_list(1, "other-app", "super-other-app", "dev", "dev.nexxera.com", "openshift")

    def test_deploy_should_accept_n_apps_in_config_file_with_env(self):
        local_file = os.path.join(os.path.dirname(__file__), '../resources', 'apps_with_env.json')

        self.deployer.deploy(file=local_file)

        self.assertEqual(2, self.mocked_provider.deploy.call_count)
        self._assert_deploy_call_list(0, "my-app", "super-my-app", "dev", "dev.nexxera.com", "dokku")
        self._assert_deploy_call_list(1, "other-app", "super-other-app", "dev", "dev.nexxera.com", "dokku")

    @mock.patch("os.path.exists")
    @mock.patch("ndeploy.deployer.Deployer._load_template_ndeploy_file")
    @mock.patch("ndeploy.deployer.Deployer._get_remote_conf")
    def test_deploy_should_be_possible_to_merge_the_local_template_with_remote_settings_from_n_apps(
            self, mock_get_remote_conf, mock_load_template_ndeploy_file, mock_os_exists):
        local_file = os.path.join(os.path.dirname(__file__), '../resources', 'apps.json')
        mock_os_exists.return_value = True
        self.deployer._app_data_template = self._load_json_to_dict(local_file)

        remote_file = os.path.join(os.path.dirname(__file__), '../resources', 'apps_remote.json')
        mock_get_remote_conf.return_value = remote_file
        remote_data_config = self._load_json_to_dict(remote_file)

        self._configure_env("qa", "qa.nexx.com", "openshift",
                            "git@git.nexx.com:environment-conf-qa/{group}.git master {name}.json")
        self.deployer.deploy(group="platform", name="platform-core", environment="qa")
        self.assertEqual(2, self.mocked_provider.deploy.call_count)
        expected_app1 = remote_data_config["apps"][0]
        expected_app2 = remote_data_config["apps"][1]
        self._assert_deploy_call_list(0, expected_app1["name"], expected_app1["deploy_name"],
                                      "qa", "qa.nexx.com", "openshift")
        self._assert_deploy_call_list(1, expected_app2["name"], expected_app2["deploy_name"],
                                      "qa", "qa.nexx.com", "openshift")

    @mock.patch("os.path.exists")
    def test_deploy_should_raise_exception_if_invalid_yaml_file(self, mock_template_ndeploy):
        mock_template_ndeploy.return_value = False
        local_file = os.path.join(os.path.dirname(__file__), '../resources', 'invalid_yaml.yaml')
        with self.assertRaises(InvalidEnvironmentFileError):
            self.deployer.deploy(file=local_file, environment="qa")

    # -----------------------  Helpers  ---------------------------------

    def _configure_env(self, name, host, _type, url):
        self.env_repo.has_environment.side_effect = \
            lambda n: n == name
        self.env_repo.load_environment.side_effect = \
            lambda n: Environment(_type, name, host, url) if n == name else None

    def _assert_undeploy_call(self, expected_app_name, expected_app_deploy_name,
                              expected_env_name, expected_env_deploy_host, expected_env_type):
        self.provider_repo.get_provider_for.assert_called_with(expected_env_type)
        self.assertEqual(1, self.mocked_provider.undeploy.call_count)

        app_called = self.mocked_provider.undeploy.call_args[0][0]
        env_called = self.mocked_provider.undeploy.call_args[0][1]
        self._assertApp(expected_app_name, expected_app_deploy_name, app_called)
        self._assertEnv(expected_env_name, expected_env_deploy_host, expected_env_type, env_called)

    def _assert_deploy_call(self, expected_app_name, expected_app_deploy_name,
                            expected_env_name, expected_env_deploy_host, expected_env_type):
        self.provider_repo.get_provider_for.assert_called_with(expected_env_type)
        self.assertEqual(1, self.mocked_provider.deploy.call_count)

        app_called = self.mocked_provider.deploy.call_args[0][0]
        env_called = self.mocked_provider.deploy.call_args[0][1]
        self._assertApp(expected_app_name, expected_app_deploy_name, app_called)
        self._assertEnv(expected_env_name, expected_env_deploy_host, expected_env_type, env_called)

    def _assert_deploy_call_list(self, index_call_args, expected_app_name, expected_app_deploy_name,
                                 expected_env_name, expected_env_deploy_host, expected_env_type):
        call_args = self.mocked_provider.deploy.call_args_list[index_call_args]
        app_called = call_args[0][0]
        env_called = call_args[0][1]
        self._assertApp(expected_app_name, expected_app_deploy_name, app_called)
        self._assertEnv(expected_env_name, expected_env_deploy_host, expected_env_type, env_called)

    def _assert_undeploy_call_list(self, index_call_args, expected_app_name, expected_app_deploy_name,
                                   expected_env_name, expected_env_deploy_host, expected_env_type):
        call_args = self.mocked_provider.undeploy.call_args_list[index_call_args]
        app_called = call_args[0][0]
        env_called = call_args[0][1]
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
        loaded_dict = self._load_json_to_dict(json_file)
        self.assertEqual(loaded_dict, _dict)

    @staticmethod
    def _load_json_to_dict(json_file):
        with open(json_file) as json_data:
            return json.load(json_data)
