from ndeploy.exception import NDeployError
from ndeploy.provider import AbstractProvider, service
from ndeploy import utils


class DokkuBranchNameError(NDeployError):
    def __init__(self, branch_name):
        self.branch_name = branch_name

    def __str__(self):
        return "Could not continue deploying because the current branch is not the same. " \
               "Make a switch in the repository local for branch {}".format(self.branch_name)


class DokkuProvider(AbstractProvider):
    """
    Implementação dos métodos para deploy em PaaS Dokku.
    """

    __type__ = 'dokku'

    DOKKU_REMOTE_NAME = 'dokku_deploy'
    DELIMITER_BRANCH_NAME = '@'

    def __init__(self):
        super().__init__()
        self.app = None
        self.env = None

    def deploy_by_image(self, app, env):
        """
        Deploy de uma aplicação passando uma imagem. A app deve ter um campo imagem.

        Args:
            app (App): a app para deploy.
            env (Environment): o environment para deploy.
        """
        assert app.image != ""

        self.app = app
        self.env = env

        print("...Deploying app {app_name} by image\n...Image url: {image}"
              .format(app_name=self.app.name, image=self.app.image))
        self._pull_image()
        self._tag_image()
        self._create_app_if_does_not_exist()
        self._update_env_vars()
        self._tag_deploy()

    def deploy_by_git_push(self, app, env):
        """
        Deploy de uma aplicação por código fonte. A app deve ter uma campo repository.

        Args:
            app (App): a app para deploy
            env (Environment): o environment para deploy
        """
        assert app.repository != ""

        self.app = app
        self.env = env

        print("Deploying app {app_name} by source repository: {repo}".format(app_name=app.name, repo=app.repository))
        self._create_app_if_does_not_exist()
        self._update_env_vars()

        source_full_path, branch_name = self._get_source_path_and_branch_name(self.app.repository)

        self._remote_git_add(source_full_path, self.DOKKU_REMOTE_NAME)
        self.git_exec.git_push(source_full_path, self.DOKKU_REMOTE_NAME, branch_name, "master")

    def _remote_git_add(self, repo_full_path, remote_name):
        """
        Adiciona o git remoto do dokku no repositório local para deploy

        Args:
            repo_full_path (str): diretório da app
            remote_name (str): nome remoto da app
        """
        remote_repo = self._get_remote_repo(self.app.deploy_name, self.env.deploy_host)
        self.git_exec.remote_git_add(repo_full_path, remote_name, remote_repo)

    def app_url(self, name):
        return "http://%s.com" % (name)

    def undeploy(self, app, environment):
        pass

    @service("postgres")
    def postgres(self, resource):
        return "postgres://user:senha@localhost:5432/%s" % (resource)

    def dokku_exec(self, dokku_cmd):
        """
        Executa comandos do dokku.
        Ex:
            dokku_exec(self, 'apps:create showdomilhao'):
        Args:
            dokku_cmd: dokku command para executar
        Returns:
            tuple (err, out) contendo a resposta do ShellExec.execute_program
        """
        return self.shell_exec.execute_program("ssh dokku@{deploy_host} {cmd}"
                                               .format(deploy_host=self.env.deploy_host, cmd=dokku_cmd))

    def _create_app_if_does_not_exist(self):
        """
        Cria uma app no dokku caso não exista
        """
        print("...Creating app {deploy_name} .......".format(deploy_name=self.app.deploy_name), end="")
        err, out = self.dokku_exec("apps:create {app_name}".format(app_name=self.app.deploy_name))
        if len(err) > 0 and 'already taken' in err:
            print("...App already registered....", end="")
        print("[OK]")

    def _pull_image(self):
        """
        Pull da imagem da aplicação para o registro docker.
        """
        print("...Pull image {}".format(self.app.image))
        self.dokku_exec("docker-direct pull {}".format(self.app.image))

    def _tag_image(self):
        """
        Tag da imagem no registro docker.
        """
        print("...Tagging image {}".format(self.app.image))
        self.dokku_exec("docker-direct tag {image} dokku/{app_name}:{image_tag}"
                        .format(image=self.app.image, app_name=self.app.deploy_name, image_tag=self.get_image_tag()))

    def _tag_deploy(self):
        """
        Deploy da imagem no dokku.
        """
        print("...Deploying image {}".format(self.app.image))
        self.dokku_exec("tags:deploy {app_name} {image_tag}"
                        .format(app_name=self.app.deploy_name, image_tag=self.get_image_tag()))

    def _update_env_vars(self):
        """
        Atualiza as variáveis de ambiente para a aplicação
        """
        print("...Configuring environment variables")
        env_vars = self.prepare_env_vars(self.app.env_vars)
        self.dokku_exec("config:set --no-restart {app_name} {env_vars}"
                        .format(app_name=self.app.deploy_name, env_vars=env_vars))

    @staticmethod
    def _get_remote_repo(deploy_name, deploy_host):
        """
        Retorna o repositorio remoto do dokku
        Returns:
            string: url git dokku
        """
        return "dokku@{host}:{app_name}".format(host=deploy_host, app_name=deploy_name)

    def _get_branch_name_and_repository(self, repository):
        """
        Retorna o nome do branch passado no repository e o repositório
        Args:
            repository: repositorio do source contendo o nome do branch a ser baixado
        Returns:
            string (repository): endereço ou path do repositório git
            string (branch_name): nome do branch passado no repository
        """
        repo = repository.split(self.DELIMITER_BRANCH_NAME)
        repository = repo[0]
        branch_name = repo[-1] if len(repo) > 1 else None
        return repository, branch_name

    def _get_source_path_and_branch_name(self, repository):
        """
        Retona a url ou diretório do repósitorio git e nome da branch passados no repository
        Args:
            repository: repositório do source contendo o nome do branch a ser baixado
        Returns:
            source_repository: url ou diretório do repositório git
            branch_name: nome do branch
        """
        source_repository, branch_name = self._get_branch_name_and_repository(repository)

        if self._is_url(source_repository):
            source_full_path = self._clone_or_pull_source(source_repository, branch_name)
        else:
            source_full_path = source_repository
            if branch_name is None:
                branch_name = self._get_current_branch_name(source_full_path)
            else:
                self._validate_actual_branch(branch_name, source_full_path)

        return source_full_path, branch_name

    @staticmethod
    def _is_url(source_repository):
        """
        Verifica se o source é uma url para clone
        Args:
           source_repository: endereço do source
        Returns:
            bool: True para repositório url, False para o contrário
        """
        return source_repository.startswith('http')

    @staticmethod
    def _create_temp_dir(app_name):
        """
        Cria um diretório temporário
        Args:
            app_name: nome da aplicação
        Returns:
            string: diretório temporário
        """
        return utils.create_temp_directory(prefix=app_name)

    def _clone_or_pull_source(self, source_repository, branch_name):
        """
        Cria um diretório temporário e clona o repositório remoto,
        caso exista um diretório com o nome da aplicação será feito um pull da aplicação

        Args:
            source_repository: endereço do source
            branch_name: nome da branch a se clonada
        Returns:
             string: diretório do clone do repositório
        """
        temp_dir_app = utils.get_temp_dir_app_if_exists(self.app.deploy_name)
        if temp_dir_app is None:
            temp_dir_app = self._create_temp_dir(self.app.deploy_name)
            self.git_exec.git_clone_from(source_repository, temp_dir_app, branch_name)
        else:
            self._validate_actual_branch(branch_name, temp_dir_app)
            self.git_exec.git_pull(temp_dir_app)

        return temp_dir_app

    def _validate_actual_branch(self, branch_name, dir_app):
        """
        Valida se branch local é igual a branch de deploy
        Args:
            branch_name: nome da branch de deploy
            dir_app: diretório temporário do repositório git
        """
        if branch_name is None:
            print("...Using current branch: {0}....".format(self._get_current_branch_name(dir_app)))
            return

        if branch_name != self._get_current_branch_name(dir_app):
            raise DokkuBranchNameError(branch_name)

    def _get_current_branch_name(self, dir_app):
        return self.git_exec.get_current_branch_name(dir_app)
