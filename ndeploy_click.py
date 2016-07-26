import click

from ndeploy import core
from ndeploy.core import avaliable_paas


@click.group()
def ndeploy():
    pass


@click.option('-f','--file_url', prompt='App deployment file URL', help="App deployment file URL, ex.: git@myhost.com/myconfs/{group}/{name}.json.")
@click.option('-h','--deploy_host', prompt='Deploy deploy_host', help="Deploy deploy_host.")
@click.option('-n','--name', prompt='Environment name', help='Environment name.')
@click.option('-t', '--type', prompt='PaaS type', help="PaaS type.", type=click.Choice(avaliable_paas.keys()))
@ndeploy.command()
def addenv(**kwargs):
    core.add_environment(name=kwargs['name'],
                         type=kwargs['type'],
                         deploy_host=kwargs['deploy_host'],
                         app_deployment_file_url=kwargs['file_url'])


@ndeploy.command()
@click.option('-n', '--name', prompt='Environment name', help="Environment name.")
def delenv(**kwargs):
    core.remove_environment(kwargs['name'])


@ndeploy.command()
def listenv(**kwargs):
    environments = core.list_environments()
    for environment in environments:
        print("name:%s, \ttype:%s, \tdeploy_host:%s" % (environment.name, environment.type, environment.host))


@ndeploy.command()
@click.option('-f','--file', prompt='App deployment file', help="App deployment file.")
@click.option('-g','--group', prompt="Group name of project", help="Group name of project.")
@click.option('-n','--name', prompt="Name project", help="Name project.")
@click.option('-e','--environment', prompt="Environment configured", help="Environment configured.")
def deploy(**kwargs):
    core.deploy(file=kwargs['file'],
                group=kwargs['group'],
                name=kwargs['name'],
                environment=kwargs['environment'])


if __name__ == '__main__':
    ndeploy()
