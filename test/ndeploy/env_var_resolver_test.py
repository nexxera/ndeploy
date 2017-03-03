import os
import unittest
from unittest.mock import MagicMock, Mock

from ndeploy.env_var_resolver import EnvVarResolver


class EnvVarResolverTest(unittest.TestCase):
    """
    Tests the environment variable resolution.
    """

    def setUp(self):
        self.resolver = EnvVarResolver()

    def test_should_resolve_empty_vars(self):
        resolved = self.resolver.resolve_vars(dict(), MagicMock(), dict())
        self.assertEqual(len(resolved), 0)

    def test_should_resolve_simple_vars(self):
        resolved = self.resolver.resolve_vars({"var": "value"}, MagicMock(), dict())
        self.assertEqual(len(resolved), 1)
        self.assertEqual("value", resolved["var"])

    def test_should_replace_env_vars(self):
        os.environ['ENVIRON'] = 'test'

        resolved = self.resolver.resolve_vars({"var": "{env:ENVIRON}"}, MagicMock(), dict())
        self.assertEqual(len(resolved), 1)
        self.assertEqual("test", resolved["var"])

    def test_should_replace_more_than_one_var(self):
        os.environ['TEST_HOST'] = '192.165.465.1'
        os.environ['TEST_PORT'] = '8088'

        resolved = self.resolver.resolve_vars({"var": "{env:TEST_HOST}:{env:TEST_PORT}"}, MagicMock(), dict())
        self.assertEqual(len(resolved), 1)
        self.assertEqual("192.165.465.1:8088", resolved["var"])

    def test_should_replace_var_asking_service(self):
        services = {"postgres": lambda _, resource: "192.168.136.12" if resource == "host" else ""}
        resolved = self.resolver.resolve_vars({"var": "{service:postgres:host}"}, MagicMock(), services)
        self.assertEqual(len(resolved), 1)
        self.assertEqual("192.168.136.12", resolved["var"])

    def test_should_replace_var_by_app_url(self):
        paas = Mock()
        paas.app_url.side_effect = lambda app: "192.168.136.12" if app == "ping" else ""
        resolved = self.resolver.resolve_vars({"var": "{app:ping}"}, paas, dict())
        self.assertEqual(len(resolved), 1)
        self.assertEqual("192.168.136.12", resolved["var"])
