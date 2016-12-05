import unittest
from unittest.mock import patch, MagicMock
from git import PushInfo

from ndeploy.git_exec import GitExec, GitExecError


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

    @patch('git.Repo')
    def test_should_be_possible_to_run_git_push_for_repository(self, repo_mock):
        repo_full_path = "/tmp/appteste-ndeploy"
        remote_name = "dokku-deploy"
        branch_local_name = "master"
        branch_remote_name = "master"
        mock_instance = repo_mock.return_value
        mock_remote = mock_instance.remote.return_value
        mock_remote.push = MagicMock(return_value=[PushInfo(flags=0, local_ref=branch_local_name,
                                                            remote_ref_string=branch_remote_name, remote=remote_name)])

        self.git_exec.git_push(repo_full_path, remote_name, branch_local_name, branch_remote_name)
        mock_instance.remote.assert_called_with(remote_name)
        mock_remote.push.assert_called_with("{branch_local}:{branch_remote}"
                                            .format(branch_local=branch_local_name, branch_remote=branch_remote_name),
                                            progress=self.git_exec.progress)

    @patch('git.Repo')
    def test_when_the_remote_repository_reject_the_push_is_returned_exception(self, repo_mock):
        repo_full_path = "/tmp/appteste-ndeploy"
        remote_name = "dokku-deploy"
        branch_local_name = "master"
        branch_remote_name = "master"
        mock_instance = repo_mock.return_value
        mock_remote = mock_instance.remote.return_value
        mock_remote.push = MagicMock(return_value=[PushInfo(flags=GitExec.REMOTE_REJECTED, local_ref=branch_local_name,
                                                            remote_ref_string=branch_remote_name, remote=remote_name)])

        with self.assertRaises(expected_exception=GitExecError):
            self.git_exec.git_push(repo_full_path, remote_name, branch_local_name, branch_remote_name)

    @patch('git.Repo')
    def test_should_be_possible_to_clone_of_a_branch_remote(self, repo_mock):
        source_repository = "https://git.nexx.com/utils/ndeploy.git"
        repo_full_path = "/tmp/appteste-ndeploy"
        branch_name = "develop"

        self.git_exec.git_clone_from(source_repository, repo_full_path, branch_name)
        repo_mock.clone_from.assert_called_with(source_repository, repo_full_path,
                                                branch=branch_name, progress=self.git_exec.progress)

    @patch('git.Repo')
    def test_should_be_possible_to_pull_local_repository(self, mock_repo):
        repo_full_path = "/tmp/appteste-ndeploy"

        self.git_exec.git_pull(repo_full_path)
        mock_instance = mock_repo.return_value
        mock_remotes_pull = mock_instance.remotes.origin.pull
        mock_remotes_pull.assert_called_once_with(progress=self.git_exec.progress)

    @patch('git.Repo')
    def test_should_be_possible_to_get_the_name_of_the_current_branch(self, mock_repo):
        branch_name = "develop"
        repo_full_path = "/tmp/appteste-ndeploy"
        mock_instance = mock_repo.return_value
        attributes = {'active_branch.name': branch_name}
        mock_instance.configure_mock(**attributes)

        current_branch_name = self.git_exec.get_current_branch_name(repo_full_path)
        self.assertEqual(branch_name, current_branch_name)
