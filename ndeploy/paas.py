"""
Módulo com implementações referentes ao que uma PaaS precisa ter mapeada para possibilitar o deploy de aplicações.
"""
import importlib
import inspect
import os
import pkgutil
from abc import abstractclassmethod, abstractmethod
from importlib import abc

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

        Returns:

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
        self._resolve_env_vars(app.env_vars)

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
        for key, value in env_vars.items():
            real_value = self._process_variable_value(value)
            env_vars[key] = real_value

    def _process_variable_value(self, value):
        """
        Processa o valor da variável.
        Args:
            value: O valor pode ser informado de alguma maneiras:
                - Valor explicito: String com valor fixo a ser aplicado na variável.
                - Composição com variável ambientes: No meio da String pode usar chaves referentes a outras variáveis de ambiente,
                    ex.: http://{EMAIL_USER}:{EMAIL_PASS}@deploy_host.com. Os valores EMAIL_USER e EMAIL_PASS serão substítuidos pelo valor real da variável de ambiente.
                - Uso de serviços: Pode-se informar no valor a necessidade do uso de um serviço especifíco, ex.: service:postgres ou service:postgres:mydb,
                    onde service indica que um serviço deve ser usado, postgres é o nome do serviço e mydb é o nome do resource a ser usado.
                - Uso de outras apps: Pode-se informar no valor a necessidade do uso de um link com outra aplicação, ex.: app:other-app,
                    onde app indica que um link com outra app deve ser usado, other-app é o nome da app que deve ser verificado a url para composição do link.

        Returns: O valor real da variável.

        """
        formatted_value = value.format(**os.environ)
        splitted_value = formatted_value.split(':')
        real_value = formatted_value

        if len(splitted_value) > 1:
            variable_type = splitted_value[0]
            name = splitted_value[1]
            resource = splitted_value[2] if len(splitted_value) == 3 else None
            real_value = self._process_variable_type(variable_type, name, resource) or formatted_value

        return real_value

    def _process_variable_type(self, variable_type, name, resource):
        """
        Se a variável é referente a um serviço ou aplicação, esse método carrega o serviço ou link da aplicação.
        Args:
            variable_type: Tipo de serviço
            name: Nome do serviço
            resource: Resource publicado no serviço.

        Returns:

        """
        value = None
        if variable_type == 'service':
            #Quando é um service, usa os serviços mapeados apartir do decorador @service.
            value = services[name](self, resource)
        if variable_type == 'app':
            value = self.app_url(name)

        return value
