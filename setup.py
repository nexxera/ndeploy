from setuptools import setup


install_requires = ["click==6.6", "timeout-decorator==0.3.2", "GitPython==2.1.1"]

setup(
    name='ndeploy',
    description='Deploy N microservices to N PaaS.',
    packages=['ndeploy', 'supported_providers', 'ndeploy_cli'],
    install_requires=install_requires,
    dependency_links=[],
    version='1.0.0',
    url='https://github.com/nexxera/ndeploy',
    download_url='https://github.com/nexxera/ndeploy',
    author='isaac.souza',
    author_email='isaac.souza@nexxera.com',
    entry_points={
        'console_scripts': [
            'ndeploy = ndeploy_cli.ndeploy_click:ndeploy',
        ],
    },
    classifiers=[
        "Topic :: Utilities",
        "Programming Language :: Python",
        'Programming Language :: Python :: 3'
    ],
)
