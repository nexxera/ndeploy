import pip
from paver.setuputils import setup
from pip.req import parse_requirements
from pkg_resources import iter_entry_points

install_reqs = parse_requirements('requirements-dev.txt', session=pip.download.PipSession())
requirements = [str(ir.req) for ir in install_reqs]
setup(
    name='ndeploy',
    packages=['ndeploy','supported_paas'],
    install_requires=requirements,
    dependency_links=[],
    version='0.0.1',
    url='http://www.nexxera.com/',
    author='isaac.souza',
    author_email='isaac.souza@nexxera.com',
    entry_points={
        'console_scripts': [
            'ndeploy = ndeploy_click:main',
        ],
    }
)

for entry_point in iter_entry_points(group='nexxera.setuputils', name=None):
    entry_point.load()()
