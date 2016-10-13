from ndeploy.provider import AbstractProvider, service


class DokkuProvider(AbstractProvider):
    """
    Implementação dos métodos para deploy em PaaS Dokku.
    """

    __type__ = 'dokku'

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

        print("Deploying app: %s, repository: %s" % (app.name, app.repository))
        raise NotImplemented()

    def app_url(self, name):
        return "http://%s.com" % (name)

    def undeploy(self, app, environment):
        pass

    @service("postgres")
    def postgres(self, resource):
        return "postgres://user:senha@localhost:5432/%s" % (resource)

    def dokku_exec(self, dokku_cmd):
        return self.shell_exec.execute_program("ssh dokku@{deploy_host} {cmd}"
                                               .format(deploy_host=self.env.deploy_host, cmd=dokku_cmd))

    def _create_app_if_does_not_exist(self):
        print("...Creating app {deploy_name} .......".format(deploy_name=self.app.deploy_name), end="")
        err, out = self.dokku_exec("apps:create {app_name}".format(app_name=self.app.deploy_name))
        if len(err) > 0 and 'already taken' in err:
            print("App already registered.")
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
