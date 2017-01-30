
# **Deploy de N aplicações em N plataformas**.

A frase acima é a que define melhor e de forma mais sucinta o que é o ndeploy, 
mas ele vai além pois o ndeploy possibilita a gestão de configuração de deploy apartir de arquivos no formato json 
onde pode ser informado todos os dados e dependências necessárias para deployar sua aplicação.

# **Funcionalidades do NDeploy**

O NDeploy foi concebido para viabilizar o deploy de aplicações de várias formas, sendo assim fica a cargo do usuário decidir como ele deseja usar o ndeploy.
Abaixo segue a lista de possíveis formas de utilização:

#### Gestão de ambientes

O NDeploy possibilita ao usuário informar o ambiente no qual será realizado o deploy das seguintes formas:

- Dados via linha de comando: na execução do ndeploy o usuário informa os dados do ambiente no qual será realizado o deploy.
- Dados no arquivo json de deployment: no arquivo json é possível definir os dados do ambiente onde será relizado o deploy, desta forma é possível que
esses dados possam ser versionados junto com o projeto. É indicado um arquivo de deployment para cada ambiente.
- Cadastramento do ambiente na ferramenta: Através de comandos na ferramenta, é possível incluir ambientes que serão persistidos no diretório $HOME do usuário,
esses ambientes ganham um nome e no momento da execução do deploy deve ser informado o nome do ambiente que deve ser usado.

#### Fonte do deploy

O Ndeploy possibilita que o deploy seja realizado apartir de duas fontes, o **repositório git do projeto** ou a **imagem docker gerada do projeto**.
Desta forma o usuário que decide através dos dados informados no arquivo de deployment qual fonte o ndeploy deve usar conforme sequência abaixo:
- Imagem docker: se informado o endereço de publicação de uma imagem docker, essa será a fonte prioritária para deploy;
- Repositório git: se informado o endereço do repositório o ndeploy faz a baixa do código fonte e faz um "git push" do fonte para o ambiente informado.
Ainda é possível informar o repositório local com "." (para diretório corrente) ou "/git/application" (para full path do diretório), para que o ndeploy considere que a execução do "git push" seja feita sobre o diretório do projeto local.<br>
Nesse caso, é possível passar a branch que será atribuida para o deploy utilizando um "@" após o repositório e incluindo o nome da branch.

#### PaaS Suportadas
   * OpenShift
   * Dokku

# **Como instalar o NDeploy**

O NDploy é uma ferramenta implementada em **Python** (3.5.1), e para sua instalação é necessário ter instalado também o PIP.
Para instalar o NDeploy basta executar o comando:

```
pip install git+https://github.com/nexxera/ndeploy.git 
```

# **Como atualizar o NDeploy**

```
pip install --upgrade git+https://github.com/nexxera/ndeploy.git
```

# **Como alterar o código**
Para desenvolver o código é preciso instalar os requirements de desenvolvimento. Para isso proceda da seguinte maneira:

Clonar o repositório:

```
git clone https://github.com/nexxera/ndeploy.git
```

Instalar dependências:

```
pip install -r "requirements.txt"
```

Rodar testes:

```
paver coverage 
```

# **Exemplos do arquivo de deployment**

- [Deploy de uma única aplicação, contendo os dados do ambiente pra deploy.](docs/json_examples/simgle-app-env.json)

    - Comando: ndeploy deploy -f app.json

- [Deploy de uma única aplicação, informando dados do ambiente via linha de comando.](docs/json_examples/simgle-app.json)

    - Comando: ndeploy deploy -f app.json -h dev.nexxera.com -t dokku

- [Deploy de uma única aplicação, informando o ambiente via linha de comando.](docs/json_examples/simgle-app.json)

    É necessário ter cadastrado o ambiente, através do comando: ndeploy addenv
    - Comando: ndeploy deploy -f app.json -e dev
    

# **Descrição dos campos do arquivo json**
| **Campo** | **Obrigatório** | **Descrição** | **Default** |
|---------|:---------:|---------------------------|----------------------------|
| name | sim | Nome da aplicação, que deve ser o mesmo nome da aplicação no repositório git. | -- |
| group | sim | Nome do grupo dessa aplicação, que deve ser o mesmo nome do grupo no repositório git. | -- |
| deploy_name | não | Nome da aplicação a ser deployada. | Usado campo name quando não informado. |
| deploy_group | não | Grupo da aplicação a ser deployada. | Usado o campo group quando não informado. |
| image | não | Endereço do registry da imagem docker. <br>Exemplo: "dockerhub.com/ivanilson/django_exemplo:master" | -- |
| repository | não | Endereço do repositório git, sendo remoto ou local. <br>Exemplo remoto: "https://github.com/Zapelini/django_exemplo.git@master" <br>Exemplo local: ".@master" ou "~/git/django_exemplo@master" | -- |
| env_vars | sim | Dicionário com as variáveis de ambientes que devem ser setadas na aplicação. | -- |


# **Agradecimentos**

Gostariamos de agradecer ao [Marcio Marchini](http://www.betterdeveloper.net), idealizador da solução e por seu apoio na reestruturação e evolução do projeto.
Esse projeto foi iniciado a partir do projeto [script ndeploy](https://github.com/sglebs/ndeploy).
