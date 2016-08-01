"""
Módulo com implementações referentes ao que uma PaaS precisa ter mapeada para possibilitar o deploy de aplicações.
"""
import importlib
import inspect
import os
import pkgutil
from abc import abstractmethod
from .env_var_resolver import EnvVarResolver

"""
Services que são carregados para que possam ser invocado no processo de deploy.
Todo método anotado com @service é carregado neste dicionário com o nome informado no decorador.
 """
services = {}

def service(name):
    """
    Decorador usado para identificar os métodos que carregam serviços durante o processo de deploy.
    Args:
        name: Nome do service. Usado apartir do valor informado no campo "env_vars", ex.: DATABASE_URL = service:postgres, postgres será o nome do service.

    Returns: Wrap

    """
    def wrap(func):
        services[name] = func
    return wrap

def load_avaliable_paas():
    """
    Carrega as implementações de PaaS
    Returns: dicionário com o nome/instancia das PaaS implementadas.
    """

    #Avaliar posteriormente a possibilidade de usuário poder incluir novos módulos.
    avaliable_paas_paths = ["supported_paas"]

    avaliable_paas = {}
    for finder_module, name, _ in pkgutil.iter_modules(avaliable_paas_paths):
        module = importlib.import_module('%s.%s' % (finder_module.path, name))
        for name, cls in inspect.getmembers(module):
            if inspect.isclass(cls) and issubclass(cls, AbstractPaas) and cls.__type__:
                avaliable_paas[cls.__type__] = cls()
    return avaliable_paas


class AbstractPaas:
    """
    Classe abstrata que define o que um PaaS precisa ter implementado para possibilitar o deploy de aplicações.
    """

    __type__ = None

    def __init__(self):
        self.env_resolver = EnvVarResolver()

    @abstractmethod
    def deploy_by_git_push(self, app):
        """
        Método usado para realização de deploy através de git push no diretório informado em app.repository ou do diretório corrente.

        Args:
            app: Objeto App com os dados que serão usados para o deploy.

        Returns:

        """
        pass


    @abstractmethod
    def deploy_by_image(self, app):
        """
        Método usado para realização de deploy através de imagem docker conforme url informada em app.image.
        Args:
            app:

        Returns:

        """
        pass


    @abstractmethod
    def app_url(self, resource):
        """
        Método usado para capturar a url de acesso a aplicação em execução no mesmo PaaS.
        Args:
            resource:

        Returns: Deve retornar uma String com url da aplicação.

        """
        pass

    def deploy(self, app, environment):
        """
        Método invocado para realização do deploy da aplicação.
        Args:
            app: Objeto App com dados da aplicação a ser deployada.
            environment: Environment no qual será feito o deploy.

        Returns:

        """

        print("Selected PaaS: %s" % (environment.type))
        app.env_vars = self._resolve_env_vars(app.env_vars)

        #Quando informado URL da imagem docker, essa tem prioridade de deploy.
        if app.image:
            self.deploy_by_image(app)
        else:
            self.deploy_by_git_push(app)

    def _resolve_env_vars(self, env_vars):
        """
        Faz a resolução dos valores para cada variável.
        Args:
            env_vars: Mapa de variáveis que deve ter o valor resolvido.

        Returns:

        """
        return self.env_resolver.resolve_vars(env_vars, self, services)


