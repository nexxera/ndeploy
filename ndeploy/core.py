"""
Módulo principal da aplicação que concentra todos os "comandos" possível.
"""
import json

from ndeploy import environment_repository
from ndeploy.model import Environment, App
from ndeploy.paas import load_avaliable_paas

"""
Mapeamento com os PaaS dispoíveis. Posteriormente deve-se implementar uma factory dinâmica
que possibilite o carregamento dos PaaS implementados na própria solução e outros PaaS implementados por terceiros.
"""

avaliable_paas = load_avaliable_paas()


def add_environment(name, type, deploy_host, app_deployment_file_url):
    """
    Adiciona e salva um novo Environment.
    Args:
        type: Tipo de ambiente, relacionado a ferramenta Paas a qual os dados do ambiente se refere, ex.: dokku, openshift, heroku, etc.
        name: Nome do Environment, ex.: dev, qa, stage, production, etc.
        deploy_host: Host de acesso a ferramenta Paas onde é realizado o deploy.
        app_deployment_file_url: Template usado para baixar arquivo de configuração da aplicação a ser deployada.

    Returns:

    """
    environment = Environment(name=name,
                              type=type,
                              deploy_host=deploy_host,
                              app_deployment_file_url=app_deployment_file_url)
    environment_repository.add_environment(environment)


def remove_environment(name):
    """
    Remove o Environment informado e salva o arquivo de environments
    Args:
        name: Nome do Environment a ser removido.

    Returns:

    """
    environment_repository.remove_environment(name)


def list_environments():
    """
    Carrega os Environments salvos.
    Returns: Lista de objetos do tipo Environment

    """
    return environment_repository.list_environments()


def deploy(file=None, group=None, name=None, environment=None):
    """
    Faz o deploy de uma aplicação.
    Args:
        file: path do arquivo com os dados para deploy.
        group: nome do grupo do projeto, usado em conjunto com name caso não seja informado o file.
        name: nome do projeto, usado em conjunto com group caso não seja informado o file.
        enviroment: nome do environment onde será feita o deploy.

    Returns:

    """
    environment = environment_repository.load_environment(environment)

    if not file:
        #TODO: não está fazendo nada de util, mas deve baixar o arquivo que contém os dados de deploy apartir da url montada.
        app_deployment_file_url = environment.app_deployment_file_url.format(group=group, name=name)
        #TODO: file deve ser o path do arquivo que foi baixado conforme comentário acima.
        file = app_deployment_file_url

    json_data = open(file).read()
    data = json.loads(json_data)
    app = App(**data)

    avaliable_paas[environment.type].deploy(app, environment)
