import unittest
from unittest.mock import MagicMock

from ndeploy.model import App, Environment
from supported_providers.dokku import DokkuProvider


class DokkuTest(unittest.TestCase):

    def setUp(self):
        self.dokku = DokkuProvider()
        self.shell_exec = MagicMock()
        self.dokku.set_shell_exec(self.shell_exec)
        self.git_exec = MagicMock()
        self.dokku.set_git_exec(self.git_exec)
        self._configure_dokku_exec()
        self.env = Environment("dokku", "dev", "dev.com")
        self.app = None

    def test_deploy_by_image(self):
        self._deploy_and_validate_by_image()

    def test_should_be_possible_injected_env_var_into_container_when_deploy_by_image(self):
        self._deploy_and_validate_by_image(env_vars={"DATA": "teste do juca", "URL": "http://jb.com.br"})

        self.dokku.dokku_exec.assert_any_call("config:set --no-restart {app_name} "
                                              "DATA=\"teste do juca\" URL=\"http://jb.com.br\""
                                              .format(app_name=self.app.deploy_name))

    def test_should_be_possible_deploy_by_local_source(self):
        source_repository = ".@develop"
        self._deploy_and_validate_app_create_by_source(source_repository)
        self.git_exec.remote_git_add.assert_any_call(source_repository.split("@")[0], DokkuProvider.REMOTE_NAME, "dokku@dev.com:myapp")
        self.git_exec.git_push.assert_any_call(source_repository.split("@")[0], DokkuProvider.REMOTE_NAME, "develop", "master")

    def test_should_be_possible_injected_env_var_into_container_when_deploy_by_source(self):
        source_repository = ".@develop"
        self._deploy_and_validate_app_create_by_source(source_repository=source_repository, env_vars={"DATA": "teste do juca", "URL": "http://jb.com.br"})
        self.dokku.dokku_exec.assert_any_call("config:set --no-restart {app_name} "
                                              "DATA=\"teste do juca\" URL=\"http://jb.com.br\""
                                              .format(app_name=self.app.deploy_name))
        self.git_exec.remote_git_add.assert_any_call(source_repository.split("@")[0], DokkuProvider.REMOTE_NAME, "dokku@dev.com:myapp")
        self.git_exec.git_push.assert_any_call(source_repository.split("@")[0], DokkuProvider.REMOTE_NAME, "develop", "master")

    def test_when_does_not_have_the_branch_in_the_repository_is_set_the_master_by_default(self):
        source_repository = "."
        self._deploy_and_validate_app_create_by_source(source_repository)
        self.git_exec.remote_git_add.assert_any_call(source_repository, DokkuProvider.REMOTE_NAME, "dokku@dev.com:myapp")
        self.git_exec.git_push.assert_any_call(source_repository, DokkuProvider.REMOTE_NAME, "master", "master")

    # Helpers

    def _configure_dokku_exec(self):
        self.dokku.dokku_exec = MagicMock(return_value=("", ""))

    def _deploy_and_validate_by_image(self, env_vars={}):
        self.app = App("myapp", "mygroup", image="image1.dev.registry.com", env_vars=env_vars)
        self.dokku.deploy(self.app, self.env)

        self.dokku.dokku_exec.assert_any_call("docker-direct pull {}".format(self.app.image))
        self.dokku.dokku_exec.assert_any_call("docker-direct tag {image} dokku/{app_name}:{image_tag}"
                                              .format(image=self.app.image, app_name=self.app.deploy_name,
                                                      image_tag=self.dokku.get_image_tag()))
        self.dokku.dokku_exec.assert_any_call("apps:create {app_name}".format(app_name=self.app.deploy_name))
        self.dokku.dokku_exec.assert_any_call("tags:deploy {app_name} {image_tag}"
                                              .format(app_name=self.app.deploy_name,
                                                      image_tag=self.dokku.get_image_tag()))

    def _deploy_and_validate_app_create_by_source(self, source_repository="", env_vars={}):
        self.app = App("myapp", "mygroup", repository=source_repository, env_vars=env_vars)
        self.dokku.deploy(self.app, self.env)
        self.dokku.dokku_exec.assert_any_call("apps:create {app_name}".format(app_name=self.app.deploy_name))
