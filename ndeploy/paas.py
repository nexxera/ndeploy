"""
Módulo com implementações referentes ao que uma PaaS precisa ter mapeada para possibilitar o deploy de aplicações.
"""
import importlib
import inspect
import os
import pkgutil
from abc import abstractmethod
from ndeploy.env_var_resolver import EnvVarResolver
from ndeploy.shell_exec import ShellExec


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


class AbstractPaas:
    """
    Classe abstrata que define o que um PaaS precisa ter implementado para possibilitar o deploy de aplicações.
    """

    __type__ = None

    def __init__(self):
        self.env_resolver = EnvVarResolver()
        self.shell_exec = None

    @abstractmethod
    def deploy_by_git_push(self, app, env):
        """
        Método usado para realização de deploy através de git push no diretório informado em app.repository ou do diretório corrente.

        Args:
            app: Objeto App com os dados que serão usados para o deploy.

        Returns:

        """
        pass


    @abstractmethod
    def deploy_by_image(self, app, env):
        """
        Método usado para realização de deploy através de imagem docker conforme url informada em app.image.
        Args:
            app: Objecto App com os dados que serão usados para o deploy
            env: Objecto Environment com os dados que serão usados para o deploy

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
        assert self.shell_exec # shell_exec should exist at this point

        print("Selected PaaS: %s" % environment.type)
        app.env_vars = self._resolve_env_vars(app.env_vars)

        # quando informado URL da imagem docker, essa tem prioridade de deploy.
        if app.image:
            self.deploy_by_image(app, environment)
        else:
            self.deploy_by_git_push(app, environment)

    def _resolve_env_vars(self, env_vars):
        """
        Faz a resolução dos valores para cada variável.
        Args:
            env_vars: Mapa de variáveis que deve ter o valor resolvido.

        Returns:

        """
        return self.env_resolver.resolve_vars(env_vars, self, services)

    def set_shell_exec(self, shell_exec):
        self.shell_exec = shell_exec



class PaasRepository:
    """
    Repositório de AbstractPaas.
    Carrega módulos definidos no diretório supported_paas que implementem AbstractPaas
    """

    def __init__(self):
        self.available_paas = PaasRepository.load_available_paas()

    def get_available_paas(self):
        return self.available_paas

    def get_paas_for(self, paas_type):
        return self.available_paas[paas_type]

    @staticmethod
    def load_available_paas():
        """
        Carrega as implementações de PaaS
        Returns: dicionário com o nome/instancia das PaaS implementadas.
        """

        # avaliar posteriormente a possibilidade de usuário poder incluir novos módulos.
        import supported_paas
        supported_paas_path = supported_paas.__path__[0]

        _available_paas = {}
        for finder_module, name, _ in pkgutil.iter_modules([supported_paas_path]):
            module = importlib.import_module('%s.%s' % ("supported_paas", name))
            for _1, cls in inspect.getmembers(module):
                if inspect.isclass(cls) and issubclass(cls, AbstractPaas) and cls.__type__:
                    new_paas = cls()
                    new_paas.set_shell_exec(ShellExec())
                    _available_paas[cls.__type__] = new_paas
        return _available_paas

