import unittest
from supported_providers.openshift import OpenshiftProvider, \
    OpenShiftNotLoggedError, OpenShiftNameTooLongError
from ndeploy.model import App, Environment
from unittest.mock import MagicMock, call


class OpenShiftTest(unittest.TestCase):

    def setUp(self):
        self.openshift = OpenshiftProvider()
        self.shell_exec = MagicMock()
        self.openshift.set_shell_exec(self.shell_exec)
        self._configure_is_logged(True)
        self._configure_openshift_exec()
        self._configure_get_deploy_revision([0, 1])
        self._configure_route_exist("myapp-mygroup.dev.com", True)

    def test_should_raise_exception_if_user_is_not_logged(self):
        with self.assertRaises(expected_exception=OpenShiftNotLoggedError):
            self._configure_is_logged(False)
            self._deploy_by_image()

    def test_should_create_project_if_does_not_exist(self):
        self._configure_project_exist("mygroup", False)
        self._configure_secret_exist("scmsecret", True)
        self._deploy_by_image()
        self.openshift.openshift_exec.assert_any_call("new-project mygroup", False)

    def test_should_not_create_project_if_exist(self):
        self._configure_project_exist("mygroup", True)
        self._configure_secret_exist("scmsecret", True)
        self.openshift.create_project = MagicMock()
        self._deploy_by_image()
        self.assertEqual(0, self.openshift.create_project.call_count)

    def test_should_create_secret_if_does_not_exist(self):
        self._configure_project_exist("mygroup", True)
        self._configure_secret_exist("scmsecret", False)
        self._deploy_by_image()
        self.shell_exec.execute_system.assert_any_call(
            "oc secrets new scmsecret ssh-privatekey=$HOME/.ssh/id_rsa -n mygroup")
        self.openshift.openshift_exec.assert_any_call(
            "secrets add serviceaccount/builder secrets/scmsecret")

    def test_should_not_create_secret_if_exist(self):
        self._configure_project_exist("mygroup", True)
        self._configure_secret_exist("scmsecret", True)
        self.openshift.create_secret = MagicMock()
        self._deploy_by_image()
        self.assertEqual(0, self.openshift.create_secret.call_count)

    def test_should_add_annotations_in_project(self):
        self._configure_project_exist("mygroup", True)
        self._configure_secret_exist("scmsecret", True)
        self.openshift.create_secret = MagicMock()
        self._deploy_by_image()
        self.assertEqual(0, self.openshift.create_secret.call_count)

        self.openshift.openshift_exec.assert_any_call(
            'patch namespace mygroup --patch \'{"metadata": {"annotations": '
            '{"openshift.io/node-selector": "region=dev"}}}\'')

    def test_deploy_by_image(self):
        self._configure_app_exist("myapp", False)
        env_vars = {"APP": "jucabala", "DB": "TESTE"}
        self._deploy_by_image(env_vars=env_vars)
        self.openshift.openshift_exec.assert_any_call(
            "new-app image1.dev.nexxera.com --name myapp --env={}".format(self.openshift.prepare_env_vars(env_vars)))
        self.openshift.openshift_exec.assert_any_call("env dc/myapp {env_vars}"
                                                      .format(env_vars=self.openshift.prepare_env_vars(env_vars)))

    def test_deploy_by_source(self):
        self._configure_app_exist("myapp", False)
        self._deploy_by_source()
        self.openshift.openshift_exec.assert_any_call(
            "new-app git@git.nexxera.com/myapp --name myapp")
        self.shell_exec.execute_system.assert_any_call(
            "oc patch bc myapp -p '{\"spec\":{\"source\":{\"sourceSecret\":{\"name\":\"scmsecret\"}}}}' -n mygroup")

    def test_should_expose_service_if_does_not_exist(self):
        self._configure_route_exist("myapp-mygroup.dev.com", False)
        self._deploy_by_source()
        self.openshift.openshift_exec.assert_any_call(
            "expose service/myapp --hostname=myapp-mygroup.dev.com --name=myapp-affcd2")
        self.openshift.openshift_exec.assert_any_call(
            "patch route myapp-affcd2 -p '{\"spec\": {\"tls\": {\"termination\": \"edge\", "
            "\"insecureEdgeTerminationPolicy\": \"Redirect\"}}}'"
            )

    def test_should_not_expose_service_if_exist(self):
        self._configure_route_exist("myapp-mygroup.dev.com", True)
        self.openshift.create_route = MagicMock()
        self._deploy_by_source()
        self.assertEqual(0, self.openshift.create_route.call_count)

    def test_env_vars_should_be_injected_into_container_when_deploy_by_image(self):
        self._configure_app_exist("myapp", False)
        env_vars = {"MY_VAR": "Ola amigo", "DUMMY": "156546"}
        self._deploy_by_image(env_vars=env_vars)
        self.openshift.openshift_exec.assert_any_call(
            'new-app image1.dev.nexxera.com --name myapp --env={}'.format(self.openshift.prepare_env_vars(env_vars)))
        self.openshift.openshift_exec.assert_any_call(
            "env dc/myapp {}".format(self.openshift.prepare_env_vars(env_vars)))

    def test_env_vars_should_be_injected_into_container_when_deploy_by_source(self):
        self._configure_app_exist("myapp", False)
        self._deploy_by_source({"MY_VAR": "Ola amigo", "DUMMY": "156546"})
        self.openshift.openshift_exec.assert_any_call(
            'new-app git@git.nexxera.com/myapp --name myapp')
        self.openshift.openshift_exec.assert_any_call(
            "env dc/myapp DUMMY=\"156546\" MY_VAR=\"Ola amigo\"")

    def test_app_with_long_deploy_name_should_raise_exception(self):
        with self.assertRaises(OpenShiftNameTooLongError):
            self._deploy(App("myapp", "mygroup",
                         deploy_name="pneumoultramicroscopicossilicovulcanoconiótico",
                         image="image", env_vars={}))

    def test_undeploy_should_call_delete(self):
        self._undeploy()
        self.openshift.openshift_exec.assert_any_call(
            "delete all -l app=myapp")

    def test_should_not_create_app_if_app_already_exists(self):
        self._configure_app_exist("myapp", True)
        self.openshift.create_app = MagicMock()
        self._deploy_by_image()
        self.openshift.create_app.assert_not_called()

    def test_should_import_latest_image_if_image_url_tag_is_not_specified(self):
        self._configure_app_exist("myapp", False)
        self._deploy_by_image()
        self.openshift.openshift_exec.assert_any_call(
            "import-image myapp:latest")

    def test_should_import_image_with_tag_specified_in_image_url(self):
        self._configure_app_exist("myapp", False)
        self._deploy_by_image(image="image1.dev.nexxera.com:release-candidate")
        self.openshift.openshift_exec.assert_any_call(
            "import-image myapp:release-candidate")

    def test_should_import_image_if_app_does_not_exist(self):
        self._configure_app_exist("myapp", False)
        self._deploy_by_image()
        self.openshift.openshift_exec.assert_any_call(
            "import-image myapp:latest")

    def test_should_force_deploy_if_nothing_changes(self):
        self._configure_app_exist("myapp", True)
        self._configure_get_deploy_revision([1, 1])
        self._deploy_by_image()
        self.openshift.openshift_exec.assert_any_call(
            "deploy myapp --latest")

    def test_should_be_route_exist(self):
        self.openshift = OpenshiftProvider()
        self.openshift.app = self._create_app()
        self._configure_openshift_exec(("", '{"items": [{"spec": '
                                            '{"host": "myapp-group.dev.com", "to": {"name": "myapp"}}}]}'))
        self.assertTrue(self.openshift.route_exist("myapp-group.dev.com"))

    def test_should_not_be_route_exist(self):
        self.openshift = OpenshiftProvider()
        self.openshift.app = self._create_app()
        self._configure_openshift_exec(("", '{"items": []}'))
        self.assertFalse(self.openshift.route_exist("myapp-group.dev.com"))

    def test_should_not_check_if_route_exists_with_invalid_json(self):
        self.openshift = OpenshiftProvider()
        self.openshift.app = self._create_app()
        self._configure_openshift_exec(("", '{invalid_json}'))
        self.assertFalse(self.openshift.route_exist("myapp-group.dev.com"))

    def test_should_expose_domains_if_does_not_exist(self):
        domains = ["myapp.dev.com", "myapp2.dev.com"]
        self._deploy_by_image(domains=domains)

        calls_expected = [
            call("expose service/myapp --hostname=myapp.dev.com --name=myapp-553a89"),
            call("patch route myapp-553a89 -p '{\"spec\": {\"tls\": {\"termination\": \"edge\", "
                 "\"insecureEdgeTerminationPolicy\": \"Redirect\"}}}'"),
            call("expose service/myapp --hostname=myapp2.dev.com --name=myapp-03cda5"),
            call("patch route myapp-03cda5 -p '{\"spec\": {\"tls\": {\"termination\": \"edge\", "
                 "\"insecureEdgeTerminationPolicy\": \"Redirect\"}}}'"),
        ]
        self.openshift.openshift_exec.assert_has_calls(calls_expected, any_order=False)

    # helpers

    @staticmethod
    def _create_app(env_vars={}, image=None, repository=None, domains=list()):
        return App("myapp", "mygroup", image=image if image is not None else "image1.dev.nexxera.com",
                   repository=repository if repository is not None else "git@git.nexxera.com/myapp",
                   env_vars=env_vars, domains=domains)

    def _deploy_by_image(self, env_vars={}, image=None, domains=list()):
        app = self._create_app(env_vars=env_vars, image=image, domains=domains, repository="")
        self._deploy(app)

    def _deploy_by_source(self, env_vars={}):
        app = self._create_app(env_vars=env_vars, repository="git@git.nexxera.com/myapp", image="")
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

    def _configure_secret_exist(self, secret, exist):
        self.openshift.secret_exist = MagicMock(
            side_effect=lambda s: exist if s == secret else False)

    def _configure_route_exist(self, route, exist):
        self.openshift.route_exist = MagicMock(
            side_effect=lambda r: exist if r == route else False)

    def _configure_app_exist(self, app, exist):
        self.openshift.app_exist = MagicMock(
            side_effect=lambda a: exist if a.name == app else False)

    def _configure_get_deploy_revision(self, revisions):
        self.openshift.get_app_deploy_revision = MagicMock(
            side_effect=revisions)

    def _configure_openshift_exec(self, return_value=None):
        self.openshift.openshift_exec = MagicMock(return_value=return_value if return_value else (None, ""))

    def _configure_generate_md5(self, md5_value="123456"):
        self.openshift._generate_unique_id = MagicMock(return_value=md5_value)
