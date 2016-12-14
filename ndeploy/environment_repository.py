"""
Repositório para persistencia dos dados referentes ao Environment.
Há implementação apenas para inserir, apagar e listar.
Não há como atualizar os dados, se necessário usuário deve apagar e inserir um environment novo.
Posteriormente pode-se implementar a atualização, mas não é algo tão necessário.
"""
import json
import os
import sys
from ndeploy.model import Environment


DIR_ENVS = os.environ['HOME']+"/.ndeploy"
FILE_ENVS = DIR_ENVS + "/environments.json"


def add_environment(environment):
    """
    Adiciona um novo Environment e salva o arquivo de environments
    Args:
        environment: Environment a ser salvo

    Returns:

    """
    enviroments = _load_environments_dict()

    for _environment in enviroments:
        if _environment['name'] == environment.name:
            sys.exit('Environment already exists!')

    enviroments.append(environment)
    _save_environments(enviroments)


def remove_environment(name):
    """
    Remove o Environment informado e salva o arquivo de environments
    Args:
        name: Nome do Environment a ser removido.

    Returns:

    """
    enviroments = _load_environments_dict()

    for _environment in enviroments:
        if _environment['name'] == name:
            enviroments.remove(_environment)

    _save_environments(enviroments)


def list_environments():
    """
    Carrega os Environments salvos.
    Returns: Lista de objetos do tipo Environment

    """
    _enviroments = _load_environments_dict()
    enviroments = []

    for _enviroment in _enviroments:
        enviroment = Environment(**_enviroment)
        enviroments.append(enviroment)

    return enviroments


def load_environment(name):
    """
    Carrega um Environment específico que esteja salvo.
    Args:
        name: Nome do Environment a ser carregado.

    Returns: Objeto Environment com os dados salvos.

    """
    enviroments = _load_environments_dict()
    enviroment = None

    for _environment in enviroments:
        if _environment['name'] == name:
            enviroment = Environment(**_environment)

    return enviroment


def _load_environments_dict():
    """
    Carrega os Environments salvos.
    Returns: Lista de dicionários com dados salvos.

    """
    enviroments = []
    if os.path.isfile(FILE_ENVS):
        json_data = open(FILE_ENVS).read()
        data = json.loads(json_data)
        enviroments = data
    return enviroments


def _save_environments(enviroments):
    """
    Salva os Environments no arquivo local de persistência no formato Json.
    Args:
        enviroments: Lista de Environments a ser salvos.

    Returns:

    """
    if not os.path.isdir(DIR_ENVS):
        os.makedirs(DIR_ENVS)

    with open(FILE_ENVS, 'w+') as fp:
        json_data = json.dumps(enviroments, default=lambda o: o.__dict__);
        fp.write(json_data)
        fp.close()
