"""
Módulo com implementações referentes ao que uma PaaS precisa ter mapeada para possibilitar o deploy de aplicações.
"""
import importlib
import inspect
import pkgutil
from abc import abstractmethod
from ndeploy.env_var_resolver import EnvVarResolver
from ndeploy.shell_exec import ShellExec
from ndeploy.git_exec import GitExec


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


class AbstractProvider:
    """
    Classe abstrata que define o que um provider precisa ter implementado para possibilitar o deploy de aplicações.
    """

    __type__ = None

    def __init__(self):
        self.env_resolver = EnvVarResolver()
        self.shell_exec = None
        self.git_exec = None

    @abstractmethod
    def deploy_by_git_push(self, app, env):
        """
        Método usado para realização de deploy através de git push no diretório informado em app.repository ou do diretório corrente.

        Args:
            app: Objeto App com os dados que serão usados para o deploy.
            env: Objecto Environment com os dados que serão usados para o deploy

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

    def deploy(self, app, env):
        """
        Método invocado para realização do deploy da aplicação.
        Args:
            app: Objeto App com dados da aplicação a ser deployada.
            env: Environment no qual será feito o deploy.

        Returns:

        """
        assert self.shell_exec # shell_exec should exist at this point

        print("...Beginning deploy on %s" % env.type)
        print("Environment name: %s" % env.name)
        print("Environment deploy host: %s" % env.deploy_host)
        print("Environment app url file: %s" % env.app_deployment_file_url)
        print("App name: %s" % app.name)
        print("App deploy name: %s" % app.deploy_name)
        print("App group: %s" % app.group)
        print("App image: %s" % app.image)
        print("App repository: %s" % app.repository)
        app.env_vars = self._resolve_env_vars(app.env_vars)

        # by image has priority
        if app.image:
            self.deploy_by_image(app, env)
        else:
            self.deploy_by_git_push(app, env)

    @abstractmethod
    def undeploy(self, app, env):
        """

        Args:
            app (App): App object
            env (Environment): Environment object

        """
        pass

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

    def set_git_exec(self, git_exec):
        self.git_exec = git_exec

    def get_image_tag(self):
        """
        Retorna a tag da imagem de app.image url ou 'latest' quando não possui tag na url

        Returns:
            str: nome tag da imagem da aplicação atual
        """
        assert self.app.image, "can only be used if app has image"
        tokens = self.app.image.split(":")
        assert len(tokens) == 1 or len(tokens) == 2, "url should have only one ':' or not have at all"
        return tokens[1] if ":" in self.app.image else "latest"

    @staticmethod
    def prepare_env_vars(env_vars):
        """
        Format the env_vars dict as a string with the following format:

            $ self.prepare_env_vars({ "ENV1": "value1", "ENV2": "value2" })
            $ ENV1=value1 ENV2=value2

        Args:
            env_vars (dict): dict containing environment keys and values

        Returns:
            str containing the formatted values

        """
        env_vars_as_str = ' '.join('{}="{}"'.format(k, v)
                                   for k, v in sorted(env_vars.items()))
        return env_vars_as_str


class ProviderRepository:
    """
    Repositório de AbstractProvider.
    Carrega módulos definidos no diretório supported_providers que implementem AbstractProvider
    """

    def __init__(self):
        self.available_providers = ProviderRepository.load_available_providers()

    def get_available_providers(self):
        return self.available_providers

    def get_provider_for(self, provider_type):
        return self.available_providers[provider_type]

    @staticmethod
    def load_available_providers():
        """
        Carrega as implementações de AbstractProvider
        Returns: dicionário com o nome/instancia das PaaS implementadas.
        """

        # avaliar posteriormente a possibilidade de usuário poder incluir novos módulos.
        import supported_providers
        supported_providers_path = supported_providers.__path__[0]

        _available_providers = {}
        for finder_module, name, _ in pkgutil.iter_modules([supported_providers_path]):
            module = importlib.import_module('%s.%s' % ("supported_providers", name))
            for _1, cls in inspect.getmembers(module):
                if inspect.isclass(cls) and issubclass(cls, AbstractProvider) and cls.__type__:
                    new_provider = cls()
                    new_provider.set_shell_exec(ShellExec())
                    new_provider.set_git_exec(GitExec())
                    _available_providers[cls.__type__] = new_provider
        return _available_providers

