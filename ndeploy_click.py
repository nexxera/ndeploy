import click

from ndeploy import core
from ndeploy.core import avaliable_paas


@click.group()
def ndeploy():
    pass


@click.option('-n','--name', prompt='Environment name please', help="Environment name.")
@click.option('-t', '--type', prompt='Environment type please (dokku, openshift)', help="Environment type.", type=click.Choice(
    avaliable_paas.keys()))
@click.option('-h','--host', prompt='Deploy host please', help="Deploy host")
@click.option('-c','--conf_app_file', prompt='URL file configuration please', help="URL file configuration, ex.: git@myhost.com/myconfs/{group}/{name}.json")
@ndeploy.command()
def addenv(**kwargs):
    core.add_environment(**kwargs)


@ndeploy.command()
@click.option('-n', '--name', prompt='Environment name please', help="Environment name.")
def delenv(**kwargs):
    core.remove_environment(kwargs['name'])


@ndeploy.command()
def listenv(**kwargs):
    environments = core.list_environments()
    for environment in environments:
        print("name:%s, type:%s, host:%s" % (environment.name, environment.type, environment.host))


@ndeploy.command()
@click.option('-f','--file', help="File name deploy configurations.")
@click.option('-g','--group', help="Group name of project")
@click.option('-n','--name', help="Name project")
@click.option('-e','--environment', help="Name the Configured environment from deploy")
def deploy(**kwargs):
    core.deploy(file=kwargs['file'],
                group=kwargs['group'],
                name=kwargs['name'],
                environment=kwargs['environment'])


if __name__ == '__main__':
    ndeploy()
