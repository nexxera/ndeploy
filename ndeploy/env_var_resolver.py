
import os, string, re


class EnvVarResolver:
    """
    Classe responsável por resolver as variáveis de ambiente da aplicação de acordo com as seguintes regras:

    Valor explícito:
        O valor da variável não muda, ou seja, o valor de entrada é o mesmo de saída.
        Ex: { "var" : "value" } -> { "var" : "value" }

    Substituição por variáveis de ambiente:
        Algum pedaço do valor da variável é substituído por uma variável de ambiente do SO.
        Ex: { "email" : "{env:EMAIL_USER}" } -> { "email" : "user@nexxera.com" }

    Substituição por variáveis usando serviços:
        É possível substituir uma variável solicitando o valor dela para um serviço externo
        Ex: { "var" : "{service:postgres:host}" } -> { "var" : "192.168.154.13" }

    Substituição por variáveis usando apps:
        É possível substituir uma variável solicitando o valor dela para uma outra aplicação
        Ex: { "var" : "{app:other-app}" } -> { "var" : "other-app.192.168.165.4" }
    """

    def __init__(self):
        self.services = {}
        self.provider = None

    def resolve_vars(self, env_vars, provider, services):
        self.services = services
        self.provider = provider

        for key, value in env_vars.items():
            real_value = self._process_variable_value(value)
            env_vars[key] = real_value

        return env_vars

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
        def replace_func(match):
            return self._resolve_var(match.group(0).replace("{", "").replace("}", "").split(":"))

        formatted_value = re.sub("\{.*?\}", replace_func, value)

        return formatted_value

    def _resolve_var(self, parsed_var):
        """
        Recebe uma tupla contendo os pedaços da variável e retorna uma string com o valor resolvido
        Args:
            parsed_var:

        Returns:
            string contendo o valor resolvido
        """

        assert len(parsed_var) >= 2, "syntax error in variable " + ":".join(parsed_var)

        var_type = parsed_var[0]
        if var_type == "env":
            return self._resolve_env(parsed_var)
        elif var_type == "service":
            return self._resolve_service(parsed_var)
        elif var_type == "app":
            return self._resolve_app(parsed_var)

        raise Exception("cant reach")

    def _resolve_env(self, parsed_var):
        assert len(parsed_var) == 2, "syntax error in env variable " + ":".join(parsed_var)
        return os.environ[parsed_var[1]]

    def _resolve_service(self, parsed_var):
        assert len(parsed_var) >= 2, "syntax error in service variable " + ":".join(parsed_var)
        # quando é um service, usa os serviços mapeados apartir do decorador @service.
        name = parsed_var[1]
        resource = parsed_var[2] if len(parsed_var) == 3 else None
        return self.services[name](self.provider, resource)

    def _resolve_app(self, parsed_var):
        assert len(parsed_var) == 2, "syntax error in app variable " + ":".join(parsed_var)
        return self.provider.app_url(parsed_var[1])




