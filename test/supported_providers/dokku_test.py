import unittest
from unittest.mock import MagicMock, patch

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

    def test_when_the_deploy_image_it_is_redirected_port_80_host_to_8080_container(self):
        self._deploy_and_validate_by_image(env_vars={"DATA": "teste do juca", "URL": "http://jb.com.br"})

        self.dokku.dokku_exec.assert_any_call("config:set --no-restart {app_name} "
                                              "DATA=\"teste do juca\" URL=\"http://jb.com.br\""
                                              .format(app_name=self.app.deploy_name))
        self.dokku.dokku_exec.assert_any_call("proxy:ports-add {app_name} http:80:8080"
                                              .format(app_name=self.app.deploy_name))

    def test_should_be_possible_deploy_by_local_source(self):
        branch_name = "develop"
        self.git_exec.get_current_branch_name.return_value = branch_name

        source_repository = ".@{branch_name}".format(branch_name=branch_name)
        self._deploy_and_validate_app_create_by_source(source_repository)
        self.git_exec.remote_git_add.assert_any_call(source_repository.split("@")[0],
                                                     DokkuProvider.DOKKU_REMOTE_NAME, "dokku@dev.com:myapp")
        self.git_exec.git_push.assert_any_call(source_repository.split("@")[0], DokkuProvider.DOKKU_REMOTE_NAME,
                                               branch_name, "master")

    def test_should_be_possible_injected_env_var_into_container_when_deploy_by_source(self):
        self.git_exec.get_current_branch_name.return_value = "develop"

        source_repository = ".@develop"
        self._deploy_and_validate_app_create_by_source(source_repository=source_repository,
                                                       env_vars={"DATA": "teste do juca", "URL": "http://jb.com.br"})
        self.dokku.dokku_exec.assert_any_call("config:set --no-restart {app_name} "
                                              "DATA=\"teste do juca\" URL=\"http://jb.com.br\""
                                              .format(app_name=self.app.deploy_name))
        self.git_exec.remote_git_add.assert_any_call(source_repository.split("@")[0], DokkuProvider.DOKKU_REMOTE_NAME,
                                                     "dokku@dev.com:myapp")
        self.git_exec.git_push.assert_any_call(source_repository.split("@")[0], DokkuProvider.DOKKU_REMOTE_NAME,
                                               source_repository.split("@")[1], "master")

    def test_when_does_not_have_the_branch_in_the_repository_is_set_the_current_work_branch_by_default(self):
        self.git_exec.get_current_branch_name.return_value = "develop"

        source_repository = "."
        self._deploy_and_validate_app_create_by_source(source_repository)
        self.git_exec.remote_git_add.assert_any_call(source_repository, DokkuProvider.DOKKU_REMOTE_NAME,
                                                     "dokku@dev.com:myapp")
        self.git_exec.git_push.assert_any_call(source_repository, DokkuProvider.DOKKU_REMOTE_NAME, "develop", "master")

    @patch('ndeploy.utils.create_temp_directory')
    def test_should_be_possible_deploy_by_remote_source(self, mock_create_temp_directory):
        repository = "https://git.nexx.com/utils/ndeploy.git"
        branch_name = "master"
        source_full_path = "/tmp/test"
        source_repository = "{0}@{1}".format(repository, branch_name)
        mock_create_temp_directory.return_value = source_full_path

        self._deploy_and_validate_app_create_by_source(source_repository)
        mock_create_temp_directory.assert_any_call(prefix=self.app.name)
        self.git_exec.git_clone_from.assert_any_call(repository, source_full_path, branch_name)
        self.git_exec.remote_git_add.assert_any_call(source_full_path, DokkuProvider.DOKKU_REMOTE_NAME,
                                                     "dokku@dev.com:myapp")
        self.git_exec.git_push.assert_any_call(source_full_path, DokkuProvider.DOKKU_REMOTE_NAME, branch_name, "master")

    @patch('ndeploy.utils.get_temp_dir_app_if_exists')
    def test_when_have_local_cache_of_the_remote_repository_the_source_must_be_updated_to_deploy(self,
                                                                                                 mock_get_temp_dir):
        branch_name = "master"
        source_repository = "https://git.nexx.com/utils/ndeploy.git@{branch_name}".format(branch_name=branch_name)
        self.git_exec.get_current_branch_name.return_value = branch_name
        temp_dir = "/temp/appteste-33-ndeploy"
        mock_get_temp_dir.return_value = temp_dir

        self._deploy_and_validate_app_create_by_source(source_repository)
        self.git_exec.get_current_branch_name.assert_any_call(temp_dir)
        self.git_exec.git_pull.assert_any_call(temp_dir)
        self.git_exec.remote_git_add.assert_any_call(temp_dir, DokkuProvider.DOKKU_REMOTE_NAME, "dokku@dev.com:myapp")
        self.git_exec.git_push.assert_any_call(temp_dir, DokkuProvider.DOKKU_REMOTE_NAME, branch_name, "master")

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
