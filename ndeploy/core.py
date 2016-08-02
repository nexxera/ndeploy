"""
Módulo principal da aplicação que concentra todos os "comandos" possível.
"""
from ndeploy.model import Environment

"""
Mapeamento com os PaaS dispoíveis. Posteriormente deve-se implementar uma factory dinâmica
que possibilite o carregamento dos PaaS implementados na própria solução e outros PaaS implementados por terceiros.
"""


class NDeployCore:
    """
    Facade para a api do ndeploy. Deve delegar suas funcionalidades para os outros módulos
    """

    def __init__(self, env_repository, deployer):
        self.environment_repository = env_repository
        self.deployer = deployer

    def add_environment(self, name, type, deploy_host, app_deployment_file_url):
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
        self.environment_repository.add_environment(environment)

    def remove_environment(self, name):
        """
        Remove o Environment informado e salva o arquivo de environments
        Args:
            name: Nome do Environment a ser removido.

        Returns:

        """
        self.environment_repository.remove_environment(name)

    def list_environments(self):
        """
        Carrega os Environments salvos.
        Returns: Lista de objetos do tipo Environment

        """
        return self.environment_repository.list_environments()

    def deploy(self, file=None, group=None, name=None, environment=None):
        """
        Faz o deploy de uma aplicação.
        Args:
            file: path do arquivo com os dados para deploy.
            group: nome do grupo do projeto, usado em conjunto com name caso não seja informado o file.
            name: nome do projeto, usado em conjunto com group caso não seja informado o file.
            enviroment: nome do environment onde será feita o deploy.

        Returns:

        """
        self.deployer.deploy(file, group, name, environment)


