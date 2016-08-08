import pprint

from ndeploy.paas import AbstractPaas, service


class DokkuPaas(AbstractPaas):
    """
    Implementação dos métodos para deploy em PaaS Dokku.
    """

    __type__ = 'dokku'

    def deploy_by_image(self, app, env):
        print("Deploying app: %s, image: %s" % (app.name, app.image))
        pprint.pprint(app.env_vars)

    def deploy_by_git_push(self, app, env):
        print("Deploying app: %s, repository: %s" % (app.name, app.repository))
        pprint.pprint(app.env_vars)

    def app_url(self, name):
        return "http://%s.com" % (name)

    @service("postgres")
    def postgres(self, resource):
        return "postgres://user:senha@localhost:5432/%s" % (resource)
