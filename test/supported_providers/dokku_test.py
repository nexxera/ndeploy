import unittest
from unittest.mock import MagicMock

from ndeploy.model import App, Environment
from supported_providers.dokku import DokkuProvider


class DokkuTest(unittest.TestCase):

    def setUp(self):
        self.dokku = DokkuProvider()
        self.shell_exec = MagicMock()
        self.dokku.set_shell_exec(self.shell_exec)
        self._configure_dokku_exec()
        self.app = App("myapp", "mygroup", image="image1.dev.registry.com")

    # -------------------------------------Helpers------------------------------------
    def test_deploy_by_image(self):
        self._deploy_and_validate_by_image()

    def test_should_be_possible_injected_env_var_into_container_when_deploy_by_image(self):
        self._deploy_and_validate_by_image(env_vars={"DATA": "teste do juca", "URL": "http://jb.com.br"})

        self.dokku.dokku_exec.assert_any_call("config:set --no-restart {app_name} "
                                              "DATA=\"teste do juca\" URL=\"http://jb.com.br\""
                                              .format(app_name=self.app.deploy_name))


    # Helpers

    def _configure_dokku_exec(self):
        self.dokku.dokku_exec = MagicMock(return_value=("", ""))

    def _deploy_and_validate_by_image(self, env_vars={}):
        self.app.env_vars = env_vars
        env = Environment("dokku", "dev", "dev.com")
        self.dokku.deploy(self.app, env)

        self.dokku.dokku_exec.assert_any_call("docker-direct pull {}".format(self.app.image))
        self.dokku.dokku_exec.assert_any_call("docker-direct tag {image} dokku/{app_name}:{image_tag}"
                                              .format(image=self.app.image, app_name=self.app.deploy_name,
                                                      image_tag=self.dokku.get_image_tag()))
        self.dokku.dokku_exec.assert_any_call("apps:create {app_name}".format(app_name=self.app.deploy_name))
        self.dokku.dokku_exec.assert_any_call("tags:deploy {app_name} {image_tag}"
                                              .format(app_name=self.app.deploy_name,
                                                      image_tag=self.dokku.get_image_tag()))
