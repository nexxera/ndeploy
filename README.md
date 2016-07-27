Ferramenta que possibilita o deploy de aplicações em N plataformas PaaS.

O ndeploy possibilita a gestão de configuração de deploy apartir de arquivos no formato json onde
pode ser informado todos os dados e dependências necessárias para deployar a aplicação.

Também é posśivel realizar o deploy em N plataformas PaaS, conforme implementação disponível.

Abaixo exemplos do arquivo de deployment:

- [Deploy de uma única aplicação, contendo os dados do ambiente pra deploy.](https://git.nexxera.com/ci-utils/ndeploy/snippets/1)

    - Comando: ndeploy deploy -f app.json

- [Deploy de uma única aplicação, informando dados do ambiente via linha de comando.](https://git.nexxera.com/ci-utils/ndeploy/snippets/2)

    - Comando: ndeploy deploy -f app.json -h dev.nexxera.com -t dokku

- [Deploy de uma única aplicação, informando o ambiente via linha de comando.](https://git.nexxera.com/ci-utils/ndeploy/snippets/2)

    - É necessário ter cadastrado o ambiente, através do comando: ndeploy addenv
    - Comando: ndeploy deploy -f app.json -e dev

- [Deploy de várias aplicações, informando o ambiente via linha de comando.](https://git.nexxera.com/ci-utils/ndeploy/snippets/3)

    - É necessário ter cadastrado o ambiente, através do comando: ndeploy addenv
    - Comando: ndeploy deploy -f app.json -e dev

