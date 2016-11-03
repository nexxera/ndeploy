import unittest
from unittest.mock import patch, MagicMock

from ndeploy.git_exec import GitExec


class GitExecTest(unittest.TestCase):

    def setUp(self):
        self.git_exec = GitExec()

    @patch('git.Repo')
    def test_should_be_possible_to_add_a_remote_repository(self, repo_mock):
        remote_name = "dokku"
        remote_url = "dokku@localhost:django"
        mock_instance = repo_mock.return_value
        mock_instance.create_remote.return_value = MagicMock()

        remote_repo = self.git_exec.remote_git_add(".", remote_name, remote_url)
        self.assertTrue(remote_repo.exists())
        mock_instance.create_remote.assert_called_once_with(remote_name, remote_url)
