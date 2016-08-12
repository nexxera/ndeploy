import os
from ndeploy.paas import AbstractPaas
import socket
from ndeploy.exception import NDeployError
import timeout_decorator


class OpenShiftNotLoggedError(NDeployError):
    def __str__(self):
        return "Could not continue deploying because openshift command line is not logged. " \
               "You have to execute 'oc login' before executing ndeploy."


class OpenShiftNameTooLongError(NDeployError):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return "The app deploy name {} is too long for openshift handle.\n" \
               "Use a name shorter than 24 characteres in App deploy_name field."\
            .format(self.name)


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
        self.validate_deploy_name(app)
        self.handle_login()
        self.configure_project(env)
        create_app_callback(app, env)
        self.expose_service(app, env)

    def validate_deploy_name(self, app):
        if len(app.deploy_name) > 24:
            raise OpenShiftNameTooLongError(app.deploy_name)

    def create_app_by_image(self, app, env):
        """
        Creates the app in the environment by image

        Args:
            app: App to be deployed
            env: Environment object
        """
        print(app.env_vars)
        print("Deploying app by image: %s, image: %s" % (app.deploy_name, app.image))

        project = self.get_openshift_area_name(env)
        self.openshift_exec("new-app {image_url} --name {app_name}"
                            .format(image_url=app.image,
                                    app_name=app.deploy_name), project)

        # this triggers another deployment
        self.openshift_exec("env dc/{app_name} {env_vars}"
                            .format(app_name=app.deploy_name,
                                    env_vars=self.prepare_env_vars(app.env_vars)), project)

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
                            .format(source_repo=app.repository,
                                    app_name=app.deploy_name), project)

        self.shell_exec.execute_system(
            "oc patch bc %s -p "
            "'{\"spec\":{\"source\":{\"sourceSecret\":{\"name\":\"scmsecret\"}}}}'"
            " -n %s" % (app.deploy_name, project))

        self.openshift_exec("start-build {app_name} --follow".format(app_name=app.deploy_name), project)
        self.openshift_exec("env dc/{app_name} {env_vars}"
                            .format(app_name=app.deploy_name,
                                    env_vars=self.prepare_env_vars(app.env_vars)), project)

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
        route_name = app.deploy_name
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
        cmd = "expose service/%s --hostname=%s" % (app.deploy_name,
                                                   self.get_openshift_app_host(app, env))
        print("...Creating app route for %s : %s" % (app.deploy_name, cmd))
        self.openshift_exec(cmd, self.get_openshift_area_name(env))

    def get_openshift_app_host(self, app, env):
        """
        Returns the host where app will be deployed

        Args:
            app (App): App object
            env (Environment): Environment object

        Return the host url of the app
        """
        return "%s-%s.%s" % (app.deploy_name, self.get_openshift_area_name(env), env.deploy_host)

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
        self.shell_exec.execute_system("oc secrets new scmsecret "
                                       "ssh-privatekey=$HOME/.ssh/id_rsa -n {}".format(project))
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
        return not self.oc_return_error("get project {project}"
                                        .format(project=project), "")

    def secret_exist(self, secret, project):
        """
        Verifies if the secret exists

        Args:
            secret: the secret to verify
            project: the project name

        Returns:
            True if exists, False otherwise
        """
        return not self.oc_return_error("get secret {secret_name}"
                                        .format(secret_name=secret), project)

    def route_exist(self, route, project):
        """
        Verifies if the route exists

        Args:
            route: the route to verify
            project: the project name

        Returns:
            True if exists, False otherwise
        """
        return not self.oc_return_error("get routes {route}"
                                        .format(route=route), project)

    def openshift_exec(self, oc_cmd, project_name):
        """
        Exec a command with oc client.
        If project_name != '' the command will have the project option at the end.
        Ex:
            openshift_exec('get routes', 'project_name')

            will execute > oc get routes -n project_name

            openshift_exec('get routes', '')

            will execute > oc get routes

        Args:
            oc_cmd: oc command to execute
            project_name: the project where the command will be executed

        Returns:
            tuple (err, out) containing response from ShellExec.execute_program

        """
        return self.shell_exec.execute_program("oc {cmd} {project}"
                                               .format(cmd=oc_cmd,
                                                       project="-n " + project_name if project_name != "" else ""))

    def oc_return_error(self, cmd, project_name):
        """
        Executes a oc command and verifies if execution returned error
        Args:
            cmd: oc command
            project_name: the project where the command will be executed or '' if

        Returns:
            err: err != None if returned error
        """
        err, out = self.openshift_exec(cmd, project_name)
        return err

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

    def _load_postgres(self, resource):
        return "postgres://user:senha@localhost:5432/%s" % resource

    def prepare_env_vars(self, env_vars):
        """
        Format the env_vars dict as a string with the format below:

            self.prepare_env_vars({ "ENV1": "value1", "ENV2": "value2" })
                -> ENV1=value1 ENV2=value2

        Args:
            env_vars (dict): dict containing environment keys and values

        Returns:
            str containing the formatted values

        """
        env_vars_as_str = ' '.join('{}="{}"'.format(k, v) \
                                   for k, v in sorted(env_vars.items()))
        return env_vars_as_str

    def get_openshift_area_name(self, env):
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
