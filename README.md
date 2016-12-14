# ndeploy
Aplicação que possibilita o deploy de aplicações em N plataformas PaaS.
=======
Aplicação que possibilita o deploy de aplicações em N provedores PaaS.

O ndeploy possibilita a gestão de configuração de deploy apartir de arquivos no formato json onde
pode ser informado todos os dados e dependências necessárias para deployar a aplicação.

Também é posśivel realizar o deploy em N plataformas PaaS, conforme implementação disponível.

Abaixo exemplos do arquivo de deployment:

- Deploy de uma única aplicação, contendo os dados do ambiente pra deploy.
```
{
  "name": "my-app",
  "deploy_name": "super-app",
  "repository": "git@gitlab.nexxera.com:group/my-app.git",
  "image": "gitlab-dreg.nexxera.com/group/my-app",
  "env_vars": {
    "APP_ENV": "Development",
    "TESTE": "Oi {BLA}",
    "APP_NOTIFICATION_URL": "app:notification",
    "DATABASE_URL": "service:postgres:teste",
    "URL_OPEN_ID": "http://www.teste.com"
  },
  "environment" : {
    "type": "dokku",
    "deploy-host": "dev.nexxera.com"
  }
}
```

- Deploy de uma única aplicação, informando dados do ambiente via linha de comando:

Comando: ndeploy deploy -f app.json -h dev.nexxera.com -t dokku
```
{
  "name": "my-app",
  "deploy_name": "super-app",
  "repository": "git@gitlab.nexxera.com:group/my-app.git",
  "image": "gitlab-dreg.nexxera.com/group/my-app",
  "env_vars": {
    "APP_ENV": "Development",
    "TESTE": "Oi {BLA}",
    "APP_NOTIFICATION_URL": "app:notification",
    "DATABASE_URL": "service:postgres:teste",
    "URL_OPEN_ID": "http://www.teste.com"
  }
}
```
- Deploy de uma única aplicação, informando o ambiente via linha de comando:

É necessário ter cadastrado o ambiente, através do comando: ndeploy addenv
Comando: ndeploy deploy -f app.json -e dev
```
{
  "name": "my-app",
  "deploy_name": "super-app",
  "repository": "git@gitlab.nexxera.com:group/my-app.git",
  "image": "gitlab-dreg.nexxera.com/group/my-app",
  "env_vars": {
    "APP_ENV": "Development",
    "TESTE": "Oi {BLA}",
    "APP_NOTIFICATION_URL": "app:notification",
    "DATABASE_URL": "service:postgres:teste",
    "URL_OPEN_ID": "http://www.teste.com"
  }
}
```
- Deploy de várias aplicações, informando o ambiente via linha de comando:

É necessário ter cadastrado o ambiente, através do comando: ndeploy addenv
Comando: ndeploy deploy -f app.json -e dev
```
{
    "apps" : [
    {
      "name": "my-app",
      "deploy_name": "super-app",
      "repository": "git@gitlab.nexxera.com:group/my-app.git",
      "image": "gitlab-dreg.nexxera.com/group/my-app",
      "env_vars": {
        "APP_ENV": "Development",
        "TESTE": "Oi {BLA}",
        "APP_NOTIFICATION_URL": "app:notification",
        "DATABASE_URL": "service:postgres:teste",
        "URL_OPEN_ID": "http://www.teste.com"
      }
    },
    {
      "name": "other-app",
      "repository": "git@gitlab.nexxera.com:group/my-app.git",
      "image": "gitlab-dreg.nexxera.com/group/my-app",
      "env_vars": {
        "APP_ENV": "Development",
        "DATABASE_URL": "service:postgres:teste2",
        "URL_OPEN_ID": "http://www.teste.com"
      }
    }
}
```
