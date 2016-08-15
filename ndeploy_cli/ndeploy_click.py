import click
import os

from ndeploy import core
from ndeploy import environment_repository
from ndeploy import deployer
from ndeploy import provider
from ndeploy.shell_exec import ShellExec

# dependencies resolution
NDEPLOY_HOME = os.environ['HOME']+"/.ndeploy"
env_repository = environment_repository.EnvironmentRepository(NDEPLOY_HOME, ShellExec())
provider_repository = provider.ProviderRepository()
deployer = deployer.Deployer(provider_repository, env_repository)
ndeploy_core = core.NDeployCore(env_repository, deployer)


@click.group()
def ndeploy():
    pass


@click.option('-f','--file_url', prompt='App deployment file URL', help="App deployment file URL, ex.: git@myhost.com/myconfs/{group}/{name}.json.")
@click.option('-h','--deploy_host', prompt='Deploy deploy_host', help="Deploy deploy_host.")
@click.option('-n','--name', prompt='Environment name', help='Environment name.')
@click.option('-t', '--type', prompt='Provider type', help="Provider type.",
              type=click.Choice(provider_repository.get_available_providers().keys()))
@ndeploy.command()
def addenv(**kwargs):
    ndeploy_core.add_environment(name=kwargs['name'],
                                 type=kwargs['type'],
                                 deploy_host=kwargs['deploy_host'],
                                 app_deployment_file_url=kwargs['file_url'])


@ndeploy.command()
@click.option('-n', '--name', prompt='Environment name', help="Environment name.")
def delenv(**kwargs):
    ndeploy_core.remove_environment(kwargs['name'])


@click.option('-f', '--file_url', prompt='App deployment file URL', help="App deployment file URL, ex.: git@myhost.com/myconfs/{group}/{name}.json.")
@click.option('-h', '--deploy_host', prompt='Deploy deploy_host', help="Deploy deploy_host.")
@click.option('-t', '--type', prompt='Provider type', help="Provider type.",
              type=click.Choice(provider_repository.get_available_providers().keys()))
@click.option('-n', '--name', prompt='Environment name', help='Environment name.')
@ndeploy.command()
def updatenv(**kwargs):
    ndeploy_core.update_environment(name=kwargs['name'],
                                    type=kwargs['type'],
                                    deploy_host=kwargs['deploy_host'],
                                    app_deployment_file_url=kwargs['file_url'])
    print("Environment updated.")


@ndeploy.command()
def listenv(**kwargs):
    environments = ndeploy_core.list_environments()
    for environment in environments:
        print("name:%s, \ttype:%s, \tdeploy_host:%s" % (environment.name, environment.type, environment.deploy_host))


@ndeploy.command()
@click.option('-n', '--name', prompt='Environment name', help="Environment name.")
def keyenv(**kwargs):
    print(ndeploy_core.get_environment_key(kwargs['name']))


@ndeploy.command()
@click.option('-f','--file', help="App deployment file.")
@click.option('-g','--group', help="Group name of project.")
@click.option('-n','--name', help="Name project.")
@click.option('-e','--environment', help="Environment configured.")
def deploy(**kwargs):
    ndeploy_core.deploy(file=kwargs['file'],
                        group=kwargs['group'],
                        name=kwargs['name'],
                        environment=kwargs['environment'])


if __name__ == '__main__':
    ndeploy()
