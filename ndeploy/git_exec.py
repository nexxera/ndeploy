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
    """
    Classe responsável por executar os comandos git
    """
    REMOTE_REJECTED = 16

    def __init__(self):
        self.progress = Progress()

    @staticmethod
    def remote_git_add(repo_full_path, remote_name, remote_repo):
        """
        Adiciona um repositório remoto no repositório local

        Args:
            repo_full_path: diretório completo do repositório git
            remote_name: nome do repositório remote
            remote_repo: endereço do repositório remoto
        """
        repo = git.Repo(repo_full_path)
        return repo.create_remote(remote_name, remote_repo)

    def git_push(self, repo_full_path, remote_name, branch_local_name, branch_remote_name):
        """
        Push para o repositório remoto

        Args:
            repo_full_path: diretório completo do repositório git
            remote_name: nome do repositório remoto
            branch_local_name: nome da branch local
            branch_remote_name: nome da branch remota
        """
        repo = git.Repo(repo_full_path)
        repo_remote = repo.remote(remote_name)
        ref_spec = "{branch_local}:{branch_remote}".format(branch_local=branch_local_name, branch_remote=branch_remote_name)
        push_info = repo_remote.push(ref_spec, progress=self.progress)[0]

        if push_info.flags & GitExec.REMOTE_REJECTED:
            raise GitExecError("Failed push for {remote_repo} repo full path {repo_full_path}"
                               .format(remote_repo=remote_name, repo_full_path=repo_full_path))

    def git_clone_from(self, source_repository, repo_full_path, branch_name=None):
        """
        Clone de uma branch de um repositório remoto

        Args:
            source_repository: endereço do repositório do fonte
            repo_full_path: diretório completo para clone do fonte
            branch_name: nome do branch a ser clonada
        """
        kwargs = {"progress": self.progress}
        if branch_name:
            kwargs["branch"] = branch_name
        git.Repo.clone_from(source_repository, repo_full_path, **kwargs)

    def git_pull(self, temp_path_app):
        """
        Pull do repositório remoto

        Args:
            temp_path_app: diretório completo do repositório para pull
        """
        repo = git.Repo(temp_path_app)
        origin = repo.remotes
        origin.pull(progress=self.progress)

