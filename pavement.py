from paver.setuputils import setup
from pkg_resources import iter_entry_points

setup(
    name='ndeploy',
    packages=['ndeploy','supported_paas','ndeploy_cli'],
    install_requires=["click", "pycrypto>=2.7a1", "timeout-decorator"],
    # estamos usando a tag por conta desse bug -> https://github.com/dlitz/pycrypto/issues/99
    # quando promoverem a versão 2.7 para o pip poderemos usar a versão default do pip
    dependency_links=["https://github.com/dlitz/pycrypto/tarball/v2.7a1#egg=pycrypto-2.7a1"],
    version='0.0.1',
    url='http://www.nexxera.com/',
    author='isaac.souza',
    author_email='isaac.souza@nexxera.com',
    entry_points={
        'console_scripts': [
            'ndeploy = ndeploy_cli.ndeploy_click:ndeploy',
        ],
    }
)

for entry_point in iter_entry_points(group='nexxera.setuputils', name=None):
    entry_point.load()()
