import git

from ndeploy.exception import NDeployError


class GitExecError(NDeployError):
    def __init__(self, name):
        self.name = name


class Progress(git.RemoteProgress):
    def line_dropped(self, line):
        print(self._cur_line)

    def update(self, *args):
        print(self._cur_line)


class GitExec:
    REMOTE_REJECTED = 16

    def __init__(self):
        self.progress = Progress()

    @staticmethod
    def remote_git_add(repo_full_path, remote_name, remote_repo):
        repo = git.Repo(repo_full_path)
        return repo.create_remote(remote_name, remote_repo)

    def git_push(self, repo_full_path, repo_remote_name, branch_local_name, branch_remote_name):
        repo = git.Repo(repo_full_path)
        repo_remote = repo.remote(repo_remote_name)
        ref_spec = "{branch_local}:{branch_remote}".format(branch_local=branch_local_name, branch_remote=branch_remote_name)
        push_info = repo_remote.push(ref_spec, progress=self.progress)[0]

        if push_info.flags & GitExec.REMOTE_REJECTED:
            raise GitExecError("Failed push for {remote_repo} repo full path {repo_full_path}"
                               .format(remote_repo=repo_remote_name, repo_full_path=repo_full_path))
