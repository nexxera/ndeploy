
from ndeploy.paas import AbstractPaas

class OpenshiftPaas(AbstractPaas):
    """
    Implementação dos métodos para deploy em PaaS Dokku.
    """

    __type__ = 'openshift'

    def deploy_by_image(self, app):
        print(app.env_vars)
        print("Deploying app: %s, image: %s" % (app.name, app.image))

    def deploy_by_git_push(self, app):
        print("Deploying app: %s, repository: %s" % (app.name, app.repository))

    def load_service(self, name, resource):
        if name == 'postgres':
            return self._load_postgres(resource)

    def app_url(self, name):
        return "http://%s.com" % (name)

    def _load_postgres(self, resource):
        return "postgres://user:senha@localhost:5432/%s" % (resource)

