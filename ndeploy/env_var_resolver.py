import os
import re
from ndeploy.exception import InvalidVarTypeError


class EnvVarResolver:
    """
    Class responsible for resolving the env_vars field for an ndeploy.model.App
    with the following rules.

    Explicitly value:
        The var value won't change. The output value will be the same of input.
        Ex:
            >> env_var.resolve_vars({ "var" : "value" })
            >> { "var" : "value" }

    OS Environment variable:
        The var value will be replaced by an OS environment variable.
        Ex:
            >> env_var.resolve_vars({ "email" : "{env:EMAIL_USER}" })
            >> { "email" : "user@nexxera.com" }

    Replacement asking service:
        The var value will be resolved by asking to a external service.
        Ex:
            >> env_var.resolve_vars({ "POSTGRES_HOST" : "{service:postgres:host}" })
            >> { "POSTGRES_HOST" : "192.168.154.13" }

    Replacement by app url:
        The var value will be resolved with another app url.
        Ex:
            >> env_var.resolve_vars({ "another_app" : "{app:another_app}" })
            >> { "another_app" : "http://192.168.154.28:8080" }

    """

    def __init__(self):
        self.services = {}
        self.provider = None

    def resolve_vars(self, env_vars, provider, services):
        """
        Resolves the environment variables with the rules specified above.

        Args:
            env_vars (dict):
            provider (AbstractProvider): provider implementation
            services (list): list of services registered with @service decorator

        Returns:
            dict containing the resolved env_vars
        """
        self.services = services
        self.provider = provider

        for key, value in env_vars.items():
            real_value = self._process_variable_value(value)
            env_vars[key] = real_value

        return env_vars

    def _process_variable_value(self, value):
        """
        Searches for ocorrences of {} and calls the appropriated rule
        to handle the resolution

        Args:
            value (str): str containing the value of a var

        Returns:
            The processed value

        """
        def replace_func(match):
            return self._resolve_var(match.group(0)
                                     .replace("{", "")
                                     .replace("}", "")
                                     .split(":"))

        formatted_value = re.sub("\{[env|service|app]\B.*?\}", replace_func, value)

        return formatted_value

    def _resolve_var(self, parsed_var):
        """
        Receives a tuple containing the parsed var pieces
        and returns a str with the resolved value for those variables

        Args:
            parsed_var (tuple): tuple of str containing the var pieces
                ex: if original var is {service:postgres:host}:
                    will call this function with:
                    -> _resolve_var(("service", "postgres", "host"))
                    and will return:
                    -> "http://150.162.12.1:5432"

        Raises:
            InvalidVarTypeError:
                if some variable type cannot be resolved

        Returns:
            string containing the resolved value
        """

        assert len(parsed_var) >= 2, "syntax error in variable " + ":"\
            .join(parsed_var)

        var_type = parsed_var[0]
        if var_type == "env":
            return self._resolve_env(parsed_var)
        elif var_type == "service":
            return self._resolve_service(parsed_var)
        elif var_type == "app":
            return self._resolve_app(parsed_var)

        raise InvalidVarTypeError(var_type)

    def _resolve_env(self, parsed_var):
        """
        Resolves the parsed_var value with env variable type.
        Will get the variable from os environment variables.
        Ex:
            $ export HOST=http://150.165.43.13

            _resolve_env(('env', 'HOST')) -> "http://150.165.43.13"

        Args:
            parsed_var (tuple): tuple with two strings, first should be
                'env' and second will be the value that will be resolved
                in os environment variable

        Returns:
            Str containing the resolved os environment value
        """
        assert len(parsed_var) == 2, "syntax error in env variable " \
                                     + ":".join(parsed_var)
        assert parsed_var[0] == 'env'
        return os.environ[parsed_var[1]]

    def _resolve_service(self, parsed_var):
        """
        Resolves the parsed var with the rules specified for a service

        Args:
            parsed_var (tuple): tuple with two or more strings, first should be
                'service', second will be the service name and the rest will
                be the value that will be resolved with the service

        Returns:
            Str containing the resolved service value

        """
        assert len(parsed_var) >= 2, \
            "syntax error in service variable " + ":".join(parsed_var)
        assert parsed_var[0] == 'service'
        name = parsed_var[1]
        resource = parsed_var[2] if len(parsed_var) == 3 else None
        return self.services[name](self.provider, resource)

    def _resolve_app(self, parsed_var):
        """
        Resolves the parsed var with the rules specified for an app

        Args:
            parsed_var (tuple): tuple with two strings, first should be
                'app', second will be the app name that will be resolved
                by the app url

        Returns:
            Str containing the resolved app url value
        """
        assert len(parsed_var) == 2, \
            "syntax error in app variable " + ":".join(parsed_var)
        assert parsed_var[0] == 'app'
        return self.provider.app_url(parsed_var[1])
