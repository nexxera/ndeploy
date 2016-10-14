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

    # -------------------------------------Helpers------------------------------------
    def _configure_dokku_exec(self):
        self.dokku.dokku_exec = MagicMock(return_value=("", ""))

    def _deploy_by_image(self, env_vars={}):
        self.app = App("myapp", "mygroup", image="image1.dev.nexxera.com", env_vars=env_vars)
        env = Environment("dokku", "dev", "dev.com")
        self.dokku.deploy(self.app, env)

    # --------------------------------------------------------------------------------

    def test_deploy_by_image(self):
        app = App("myapp", "mygroup", image="image1.dev.nexxera.com", env_vars={})
        env = Environment("dokku", "dev", "dev.com")
        self.dokku.deploy(app, env)
        self.dokku.dokku_exec.assert_any_call("docker-direct pull {}".format(app.image))
        self.dokku.dokku_exec.assert_any_call("docker-direct tag {image} dokku/{app_name}:{image_tag}"
                                              .format(image=app.image, app_name=app.deploy_name,
                                                      image_tag=self.dokku.get_image_tag()))
        self.dokku.dokku_exec.assert_any_call("apps:create myapp")
        self.dokku.dokku_exec.assert_any_call("tags:deploy {app_name} {image_tag}"
                                              .format(app_name=app.deploy_name, image_tag=self.dokku.get_image_tag()))

    def test_can_be_possible_injected_env_var_into_container_when_deploy_by_image(self):
        self._deploy_by_image(env_vars={"DATA": "teste do juca", "URL": "http://jb.com.br"})
        self.dokku.dokku_exec.assert_any_call("apps:create myapp")
        self.dokku.dokku_exec.assert_any_call("config:set --no-restart {app_name} "
                                              "DATA=\"teste do juca\" URL=\"http://jb.com.br\""
                                              .format(app_name=self.app.deploy_name))
