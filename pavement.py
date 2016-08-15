from paver.setuputils import setup
from pkg_resources import iter_entry_points

setup(
    name='ndeploy',
    packages=['ndeploy','supported_providers','ndeploy_cli'],
    install_requires=["click", "timeout-decorator"],
    dependency_links=[],
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
