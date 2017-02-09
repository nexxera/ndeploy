import json
import os
import unittest

from ndeploy.model import App, Environment
from ndeploy.provider import AbstractProvider, service
from unittest.mock import MagicMock


class MockProvider(AbstractProvider):

    def __init__(self):
        super().__init__()
        self.result = {}

    def deploy_by_image(self, app, env):
        self.result['deploy_method'] = 'by_image'
        self.result['app'] = app

    def deploy_by_git_push(self, app, env):
        self.result['deploy_method'] = 'by_git_push'
        self.result['app'] = app

    def app_url(self, name):
        return "http://%s.com" % (name)

    def undeploy(self, app, environment):
        pass

    @service("postgres")
    def load_postgres(self, resource):
        return "postgres://user:senha@localhost:5432/%s" % (resource)


class AssembleModelTest(unittest.TestCase):
    """
    Test assemble models.
    """

    def test_deploy_app(self):

        os.environ['BLA'] = 'teste'

        file = os.path.join(os.path.dirname(__file__), '../resources', 'app.json')
        json_data = open(file).read()

        data = json.loads(json_data)
        app = App(**data)

        mock_paas = MockProvider()
        mock_paas.set_shell_exec(MagicMock())
        mock_paas.deploy(app, Environment(name='dev', deploy_host='localhost', type='mock'))

        env_vars = dict(
            APP_ENV="Development",
            TESTE="Oi teste",
            APP_NOTIFICATION_URL="http://notification.com",
            DATABASE_URL="postgres://user:senha@localhost:5432/teste",
            URL_OPEN_ID="http://www.teste.com",
            SCHEDULER="{\"hour\": \"*/10\"}"
        )

        self.assertEqual(app.env_vars, env_vars)
