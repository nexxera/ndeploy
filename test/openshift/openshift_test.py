import unittest
from supported_providers.openshift import OpenshiftProvider, \
    OpenShiftNotLoggedError, OpenShiftNameTooLongError
from ndeploy.model import App, Environment
from unittest.mock import MagicMock


class OpenShiftTest(unittest.TestCase):

    def setUp(self):
        self.openshift = OpenshiftProvider()
        self.shell_exec = MagicMock()
        self.openshift.set_shell_exec(self.shell_exec)
        self._configure_is_logged(True)
        self._configure_openshift_exec()

    def test_should_raise_exception_if_user_is_not_logged(self):
        with self.assertRaises(expected_exception=OpenShiftNotLoggedError):
            self._configure_is_logged(False)
            self._deploy_by_image()

    def test_should_create_project_if_does_not_exist(self):
        self._configure_project_exist("mygroup", False)
        self._configure_secret_exist("scmsecret", "mygroup", True)
        self._deploy_by_image()
        self.openshift.openshift_exec.assert_any_call("new-project mygroup", "")

    def test_should_not_create_project_if_exist(self):
        self._configure_project_exist("mygroup", True)
        self._configure_secret_exist("scmsecret", "mygroup", True)
        self.openshift.create_project = MagicMock()
        self._deploy_by_image()
        self.assertEqual(0, self.openshift.create_project.call_count)

    def test_should_create_secret_if_does_not_exist(self):
        self._configure_project_exist("mygroup", True)
        self._configure_secret_exist("scmsecret", "mygroup", False)
        self._deploy_by_image()
        self.shell_exec.execute_system.assert_any_call(
            "oc secrets new scmsecret ssh-privatekey=$HOME/.ssh/id_rsa -n mygroup")
        self.openshift.openshift_exec.assert_any_call(
            "secrets add serviceaccount/builder secrets/scmsecret", "mygroup")

    def test_should_not_create_secret_if_exist(self):
        self._configure_project_exist("mygroup", True)
        self._configure_secret_exist("scmsecret", "mygroup", True)
        self.openshift.create_secret = MagicMock()
        self._deploy_by_image()
        self.assertEqual(0, self.openshift.create_secret.call_count)

    def test_deploy_by_image(self):
        self._deploy_by_image()
        self.openshift.openshift_exec.assert_any_call(
            "new-app image1.dev.nexxera.com --name myapp", "mygroup")
        self.openshift.openshift_exec.assert_any_call(
            "env dc/myapp ", "mygroup")

    def test_deploy_by_source(self):
        self._deploy_by_source()
        self.openshift.openshift_exec.assert_any_call(
            "new-app git@git.nexxera.com/myapp --name myapp", "mygroup")
        self.shell_exec.execute_system.assert_any_call(
            "oc patch bc myapp -p '{\"spec\":{\"source\":{\"sourceSecret\":{\"name\":\"scmsecret\"}}}}' -n mygroup")

    def test_should_expose_service_if_does_not_exist(self):
        self._configure_route_exist("myapp", "mygroup", False)
        self._deploy_by_source()
        self.openshift.openshift_exec.assert_any_call(
            "expose service/myapp --hostname=myapp-mygroup.dev.com", "mygroup")
        self.openshift.openshift_exec.assert_any_call(
            """patch route myapp -p '{"spec": {"tls": {"termination": "edge", "insecureEdgeTerminationPolicy": "Redirect"}}}'"""
            , "mygroup")

    def test_should_not_expose_service_if_exist(self):
        self._configure_route_exist("myapp", "mygroup", True)
        self.openshift.create_route = MagicMock()
        self._deploy_by_source()
        self.assertEqual(0, self.openshift.create_route.call_count)

    def test_env_vars_should_be_injected_into_container_when_deploy_by_image(self):
        self._deploy_by_image({"MY_VAR": "Ola amigo", "DUMMY": "156546"})
        self.openshift.openshift_exec.assert_any_call(
            'new-app image1.dev.nexxera.com --name myapp', "mygroup")
        self.openshift.openshift_exec.assert_any_call(
            "env dc/myapp DUMMY=\"156546\" MY_VAR=\"Ola amigo\"", "mygroup")

    def test_env_vars_should_be_injected_into_container_when_deploy_by_source(self):
        self._deploy_by_source({"MY_VAR": "Ola amigo", "DUMMY": "156546"})
        self.openshift.openshift_exec.assert_any_call(
            'new-app git@git.nexxera.com/myapp --name myapp', "mygroup")
        self.openshift.openshift_exec.assert_any_call(
            "env dc/myapp DUMMY=\"156546\" MY_VAR=\"Ola amigo\"", "mygroup")

    def test_app_with_long_deploy_name_should_raise_exception(self):
        with self.assertRaises(OpenShiftNameTooLongError):
            self._deploy(App("myapp", "mygroup", deploy_name="pneumoultramicroscopicossilicovulcanoconiótico",
                         image="image", env_vars={}))

    def test_undeploy_should_call_delete(self):
        self._undeploy()
        self.openshift.openshift_exec.assert_any_call(
            "delete all -l app=myapp", "mygroup")

    # helpers

    def _deploy_by_image(self, env_vars={}):
        app = App("myapp", "mygroup", image="image1.dev.nexxera.com", env_vars=env_vars)
        self._deploy(app)

    def _deploy_by_source(self, env_vars={}):
        app = App("myapp", "mygroup", repository="git@git.nexxera.com/myapp", env_vars=env_vars)
        self._deploy(app)

    def _undeploy(self):
        self.openshift.undeploy(App("myapp", "mygroup"),
                                Environment("openshift", "dev", "dev.com"))

    def _deploy(self, app):
        env = Environment("openshift", "dev", "dev.com")
        self.openshift.deploy(app, env)

    def _configure_is_logged(self, is_logged):
        self.openshift.is_logged = MagicMock(return_value=is_logged)

    def _configure_project_exist(self, project, exist):
        self.openshift.project_exist = MagicMock(side_effect=lambda p: exist if p == project else False)

    def _configure_secret_exist(self, secret, project, exist):
        self.openshift.secret_exist = MagicMock(
            side_effect=lambda s, p: exist if s == secret and p == project else False)

    def _configure_route_exist(self, route, project, exist):
        self.openshift.route_exist = MagicMock(side_effect=lambda r, p: exist if p == project and r == route else False)

    def _configure_openshift_exec(self):
        self.openshift.openshift_exec = MagicMock(return_value=(None, ""))

