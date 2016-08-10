import os
from ndeploy.paas import AbstractPaas
import socket
from ndeploy.exception import NDeployError
import timeout_decorator


class OpenShiftNotLoggedError(NDeployError):
    def __str__(self):
        return "Could not continue deploying because openshift command line is not logged. " \
               "You have to execute 'oc login' before executing ndeploy."


class OpenshiftPaas(AbstractPaas):
    """
    Implementação dos métodos para deploy no openshift.
    """

    __type__ = 'openshift'

    def deploy_by_image(self, app, env):
        """
        Deploys the app passing an image. The app should have an image field.

        Args:
            app (App): the app to deploy.
            env (Environment): the environment to deploy.

        """
        assert app.image != ""

        self.openshift_deploy(app, env, self.create_app_by_image)

    def deploy_by_git_push(self, app, env):
        """
        Deploys the app by source. The app should have a repository field

        Args:
            app: the App to deploy
            env: the Environment to deploy
        """
        assert app.repository != ""

        self.openshift_deploy(app, env, self.create_app_by_source)

    def openshift_deploy(self, app, env, create_app_callback):
        """
        Do all the flow needed to deploy an app on openshift.
        The real deploy should be made by the 'create_app_callback' function

        Args:
            app: App
            env: Environment
            create_app_callback: function that makes the deploy
                            signature: fn(app, env)
        """
        self.handle_login()
        self.configure_project(env)
        create_app_callback(app, env)
        self.expose_service(app, env)

    def create_app_by_image(self, app, env):
        """
        Creates the app in the environment by image

        Args:
            app: App to be deployed
            env: Environment object
        """
        print(app.env_vars)
        print("Deploying app by image: %s, image: %s" % (app.name, app.image))

        project = self.get_openshift_area_name(env)
        self.openshift_exec("new-app {image_url} --name {app_name}"
                            .format(image_url=app.image, app_name=app.name), project)
        self.openshift_exec("deploy {app_name} --latest"
                            .format(app_name=app.name), project)

    def create_app_by_source(self, app, env):
        """
        Creates the app in the environment by source

        Args:
            app (App): app to be deployed
            env (Environment): environment object
        """
        print("Deploying app by source: %s, group: repository: %s" % (app.name, app.repository))

        project = self.get_openshift_area_name(env)
        self.openshift_exec("new-app {source_repo} --name {app_name}"
                            .format(source_repo=app.repository, app_name=app.name), project)

        self.shell_exec.execute_system(
            "oc patch bc %s -p "
            "'{\"spec\":{\"source\":{\"sourceSecret\":{\"name\":\"scmsecret\"}}}}'"
            " -n %s" % (app.name, project))

        self.openshift_exec("start-build {app_name}".format(app_name=app.name), project)

    def load_service(self, name, resource):
        if name == 'postgres':
            return self._load_postgres(resource)

    def app_url(self, name):
        return "http://%s.com" % name

    def handle_login(self):
        """
        Verifies if the oc client is logged. Raise OpenShiftNotLoggedError
        if not logged
        """
        if not self.is_logged():
            # raising exception for now. We need to think in a better solution for this
            raise OpenShiftNotLoggedError
            # self.login(env)

    def expose_service(self, app, env):
        """
        Expose the openshift route if it doesn't exist.
        The created route will have the name of the app

        Args:
            app (App): App object
            env (Environment): Environment object
        """
        route_name = app.name
        project = self.get_openshift_area_name(env)

        if not self.route_exist(route_name, project):
            self.create_route(app, env)
        else:
            print("Route {} already exists. Using it.".format(route_name))

    def create_route(self, app, env):
        """
        Creates the route for the app.
        The route name will be the app name.

        Args:
            app (App): app object
            env (Environment): environment
        """
        cmd = "expose service/%s --hostname=%s" % (app.name,
                                                   self.get_openshift_app_host(app, env))
        print("...Creating app route for %s : %s" % (app.name, cmd))
        self.openshift_exec(cmd, self.get_openshift_area_name(env))

    def get_openshift_app_host(self, app, env):
        """
        Returns the host where app will be deployed

        Args:
            app (App): App object
            env (Environment): Environment object

        Return the host url of the app
        """
        return "%s-%s.%s" % (app.name, self.get_openshift_area_name(env), env.deploy_host)

    def configure_project(self, env):
        """
        Configure the openshift project where the app will be deployed.
        Creates the project and the secret for the scm if they doesn't exist

        Args:
            env (Environment): Environment object

        """
        project = self.get_openshift_area_name(env)
        self.create_project_if_does_not_exist(project)
        self.create_secret_if_does_not_exist(project)

    def create_project(self, project):
        """
        Creates a new project on openshift

        Args:
            project: the project name
        """
        self.openshift_exec("new-project " + project, "")

    def create_project_if_does_not_exist(self, project):
        """
        Verifies if the project exists and creates a new project if it doesn't exist
        Args:
            project: the project name
        """
        if not self.project_exist(project):
            self.create_project(project)
        else:
            print("...Project {} already exists. Using it.".format(project))

    def create_secret(self, project):
        """
        Creates a new secret with the default ssh key of current user (located at
        $HOME/.ssh/id_rsa) to allow openshift to access the git repo.
        The secret will be create with 'scmsecret' as name

        Args:
            project: the project name
        """
        # temos que executar com os.system por causa do parâmatro ssh-privatekey.
        # Por algum motivo não funciona com subprocess
        self.shell_exec.execute_system("oc secrets new scmsecret ssh-privatekey=$HOME/.ssh/id_rsa -n {}".format(project))
        self.openshift_exec("secrets add serviceaccount/builder secrets/scmsecret", project)

    def create_secret_if_does_not_exist(self, project):
        """
        Creates a secret if it doesn't exist.
        The secret will be named 'scmsecret'

        Args:
            project: the project name
        """
        if not self.secret_exist("scmsecret", project):
            self.create_secret(project)
        else:
            print("...Secret {} already exists. Using it.".format("scmsecret"))

    def project_exist(self, project):
        """
        Verifies if the project exists

        Args:
            project: the project name

        Returns:
            True if exists, False otherwise
        """
        return not self.shell_exec.program_return_error("oc get project " + project)

    def secret_exist(self, secret, project):
        """
        Verifies if the secret exists

        Args:
            secret: the secret to verify
            project: the project name

        Returns:
            True if exists, False otherwise
        """
        return not self.shell_exec.program_return_error("oc get secret {secret_name} -n {project}"
                                                        .format(secret_name=secret, project=project))

    def route_exist(self, route, project):
        """
        Verifies if the route exists

        Args:
            route: the route to verify
            project: the project name

        Returns:
            True if exists, False otherwise
        """
        return not self.shell_exec.program_return_error("oc get routes {route} -n {project}"
                                                        .format(route=route, project=project))

    def openshift_exec(self, openshift_cmd, project_name):
        """
        Exec a command with oc client.
        If project_name != '' the command will have the project option at the end.
        Ex:
            openshift_exec('get routes', 'project_name')

            will execute > oc get routes -n project_name

            openshift_exec('get routes', '')

            will execute > oc get routes

        Args:
            openshift_cmd: oc command to execute
            project_name: the project where the command will be executed
        """
        self.shell_exec.execute_program("oc {cmd} -n {project}"
                                        .format(cmd=openshift_cmd,
                                                project=project_name if project_name != "" else ""))

    def is_logged(self):
        """
        Verifies if oc client is logged

        Returns:
            True if logged, False otherwise
        """
        cmd = "oc whoami"
        try:
            err, out = self.shell_exec.execute_program_with_timeout(cmd)
            if "system:anonymous" in err or "provide credentials" in err:
                return False
            else:
                return True
        except timeout_decorator.TimeoutError:
            return False

    def login(self, env):
        """
        Login at openshift host.
        Args:
            env (Environment): environment object
        """
        # login has to be by IP because of teh https/ssl signed certificate
        ip = socket.gethostbyname(env.deploy_host)
        self.shell_exec.execute_program("oc login https://%s:8443" % ip)

    @staticmethod
    def _load_postgres(resource):
        return "postgres://user:senha@localhost:5432/%s" % resource

    @staticmethod
    def get_openshift_area_name(env):
        """
        Returns the current openshift project name.
        By now the project name will be the env.name. In sgslebs/ndeploy the project
        name will be the name of the user executing ndeploy
        or 'area' option passed in command line.

        Args:
            env: Environment
        Returns:
            the current openshift project name
        """
        return env.name
        # sgslebs/ndeploy implementation
        # default = getpass.getuser()
        # return options.get("area", default).replace(".", "")
