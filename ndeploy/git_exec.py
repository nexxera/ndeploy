import git


class GitExec:

    @staticmethod
    def remote_git_add(repo_full_path, remote_name, remote_repo):
        # assert not repo.bare
        repo = git.Repo(repo_full_path)
        repo.create_remote(remote_name, remote_repo)

    @staticmethod
    def git_push(url_repository, branch_name, branch_remote_name):
        pass
