import json
import os
import unittest

from ndeploy.model import App, Environment
from ndeploy.exception import BadFormedRemoteConfigUrlError
from .test_helpers import get_valid_deployment_file_url


class AssembleModelTest(unittest.TestCase):
    """
    Test assemble models.
    """

    def test_should_assemble_app(self):
        file = os.path.join(os.path.dirname(__file__), '../resources', 'model_app.json')
        json_data = open(file).read()

        data = json.loads(json_data)

        app = App(**data)

        app_expected = App(name="my-app",
                           deploy_name="super-app",
                           repository="git@gitlab.nexxera.com:group/my-app.git",
                           image="gitlab-dreg.nexxera.com/group/my-app",
                           env_vars=dict(APP_ENV="Development", EMAIL_HOST="smtp@domain.com"))

        self.assertEqual(app.__dict__, app_expected.__dict__)

    def test_should_assemble_environment(self):
        file = os.path.join(os.path.dirname(__file__), '../resources', 'model_environment.json')
        json_data = open(file).read()

        data = json.loads(json_data)

        environment = Environment(**data)

        environment_expected = Environment(
            type="dokku",
            name="integrated-dev",
            deploy_host="integrated-dev.nexxera.com",
            app_deployment_file_url=get_valid_deployment_file_url())

        self.assertEqual(environment.__dict__, environment_expected.__dict__)

    def test_create_empty_app(self):
        app = App("name")
        self.assertEquals("name", app.name)
        self.assertEquals("name", app.deploy_name)
        self.assertEquals("", app.image)
        self.assertEquals("", app.repository)
        self.assertEquals({}, app.env_vars)

    def test_app_without_deploy_name_use_name(self):
        app = App("name")
        self.assertEqual("name", app.deploy_name)

    def test_wrong_app_deployment_file_url(self):
        with self.assertRaises(BadFormedRemoteConfigUrlError):
            Environment(type="dokku", name="qa", deploy_host="qa.nexxera.com",
                        app_deployment_file_url="git@git.nexxera.com")

    # def test_null_app_deployment_file_url_should_be_accepted(self):
    #     with self.assertRaises(BadFormedRemoteConfigUrlError):
    #         Environment(type="dokku", name="qa", deploy_host="qa.nexxera.com",
    #                     app_deployment_file_url="git@gitlab.nexxera.com:group/{mygroup}.git")
