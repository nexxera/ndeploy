import io
import tarfile

import git

from ndeploy.exception import NDeployError


class GitExecError(NDeployError):
    def __init__(self, message):
        self.message = "Git exec error: {}".format(message)


class GitRemoteRepoError(NDeployError):
    def __init__(self, name):
        self.name = name


class GitNoSuchPathError(NDeployError):
    def __init__(self, repository):
        self.repository = repository

    def __str__(self):
        return "The path {} is not a git repository.".format(self.repository)


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
        try:
            repo = git.Repo(repo_full_path)
            return repo.create_remote(remote_name, remote_repo)
        except git.NoSuchPathError:
            raise GitNoSuchPathError(repo_full_path)
        except git.GitCommandError as e:
            error_string = "remote {} already exists".format(remote_name)
            if error_string in e.stderr:
                raise GitRemoteRepoError("Remote {} already exists".format(remote_name))
            else:
                raise GitExecError(e)

    @staticmethod
    def remote_set_url(repo_full_path, remote_name, remote_repo):
        try:
            repo = git.Repo(repo_full_path)
            repo.remote(remote_name).set_url(remote_repo)
        except git.NoSuchPathError:
            raise GitNoSuchPathError(repo_full_path)

    def git_push(self, repo_full_path, remote_name, branch_local_name, branch_remote_name):
        """
        Push para o repositório remoto

        Args:
            repo_full_path: diretório completo do repositório git
            remote_name: nome do repositório remoto
            branch_local_name: nome da branch local
            branch_remote_name: nome da branch remota
        """
        try:
            repo = git.Repo(repo_full_path)
            repo_remote = repo.remote(remote_name)
            ref_spec = "{branch_local}:{branch_remote}".format(branch_local=branch_local_name,
                                                               branch_remote=branch_remote_name)
            push_infos = repo_remote.push(ref_spec, progress=self.progress)

            print(push_infos[0].summary)

            if push_infos[0].flags & GitExec.REMOTE_REJECTED:
                raise GitExecError("Failed push for {remote_repo} repo full path {repo_full_path}"
                                   .format(remote_repo=remote_name, repo_full_path=repo_full_path))
        except git.NoSuchPathError:
            raise GitNoSuchPathError(repo_full_path)

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
        try:
            git.Repo.clone_from(source_repository, repo_full_path, **kwargs)
        except git.GitCommandError as e:
            raise GitExecError(e)

    def git_pull(self, temp_path_app):
        """
        Pull do repositório remoto

        Args:
            temp_path_app: diretório completo do repositório para pull
        """
        try:
            repo = git.Repo(temp_path_app)
            origin = repo.remotes.origin
            origin.pull(progress=self.progress)
        except git.NoSuchPathError:
            raise GitNoSuchPathError(temp_path_app)

    @staticmethod
    def get_current_branch_name(repo_app_full_path):
        """
        Retorna a branch corrente do repitório

        Args:
            repo_app_full_path: diretório completo do repositório

        Returns:
            string: nome do branch corrente
        """
        try:
            repo = git.Repo(repo_app_full_path)
            return repo.active_branch.name
        except git.NoSuchPathError:
            raise GitNoSuchPathError(repo_app_full_path)

    @staticmethod
    def archive_clone(rsa_path, repo_url, branch, local_folder, file_relative_path):
        """
        Clone a git repository file

        Args:
            rsa_path (str): path to the repo rsa private key
            repo_url (str): the remote repo url
            branch (str): git branch name
            local_folder (str): the path of the dir to the clone
            file_relative_path (str): the path of the file relative to the repo root

        Returns:
            full path for the cloned file
        """
        try:
            cmd_archive_clone = ["git", "archive", "--remote={repo_url}".format(repo_url=repo_url),
                                 branch, file_relative_path]
            g = git.Git()
            ssh_executable = 'ssh -i {rsa_path}'.format(rsa_path=rsa_path)
            with g.custom_environment(GIT_SSH_COMMAND=ssh_executable):
                out = g.execute(command=cmd_archive_clone)
                with io.BytesIO(bytearray(map(ord, out))) as f:
                    with tarfile.open(fileobj=f) as tar:
                        tar.extractall(members=None, path=local_folder)

            return '{}/{}'.format(local_folder, file_relative_path)
        except git.GitCommandError as e:
            raise GitExecError("Git command error:{}".format(e))
        except Exception as e:
            raise GitExecError(e)
