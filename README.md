# **Deploy de N aplicações em N plataformas**.

A frase acima é a que define melhor e de forma mais sucinta o que é o ndeploy, 
mas ele vai além pois o ndeploy possibilita a gestão de configuração de deploy apartir de arquivos no formato json 
onde pode ser informado todos os dados e dependências necessárias para deployar sua aplicação.

# **Funcionalidades do NDeploy**

O NDeploy foi concebido para viabilizar o deploy de aplicações de várias formas, sendo assim fica a cargo do usuário decidir como ele deseja usar o ndeploy.
Abaixo segue a lista de possíveis forma de utilização:

#### Gestão de ambientes

O NDeploy possibilita ao usuário informar o ambiente no qual será realizado o deploy das seguintes formas:

- Dados via linha de comando: na execução do ndeploy o usuário informa os dados do ambiente no qual será realizado o deploy.
- Dados no arquivo json de deployment: no arquivo json é possível definir os dados do ambiente onde será relizado o deploy, desta forma é possível que
esses dados possam ser versionados junto com o projeto. É indicado um arquivo de deployment para cada ambiente.
- Cadastramento do ambiente na ferramenta: Através de comandos na ferramenta, é possível incluir ambientes que serão persistidos no diretóri o $HOME do usuário,
esses ambientes ganham um nome e no momento da execução do deploy deve ser informado o nome do ambiente que deve ser usado.

#### Fonte do deploy

O Ndeploy possibilita que o deploy seja realizado apartir de duas fontes, o **repositório git do projeto** ou a **imagem docker gerada do projeto**.
Desta forma o usuário que decide através do dados informados no arquivo de deployment qual fonte o ndeploy deve usar conforme sequência abaixo:
- Imagem docker: se informado o endereço de publicação de uma imagem docker, essa será a fonte prioritária para deploy
- Repositório git: se informado o endereço do repositório o ndeploy faz baixa o código fonte e faz um "git push" do fonte para o ambiente informado.
Ainda é possível apenas informar o repositório como "this" para que o ndeploy considere que a execução está sendo feita no próprio diretório git do projeto,
sendo assim o git push será feito sobre o diretório d eexecução do ndeploy.

#### Deploy e uma ou várias aplicações

No arquivo de deployment é possível informar os dados de uma ou mais aplicações a serem deployadas.
Geralmente o uso de uma aplicação do arquivo de deployment é para processo de integração contínua.
O Uso de várias aplicações no arquivo de deployment se dá para casos onde o usuário deseja fazer o deploy de N aplicações para montar um cenário de execução
local ou para testes onde ele não quer ter que baixar todos os fontes do projeto e fazer uma implantação manual de aplicação por aplicação.

# **Como instalar o NDeploy**

O NDploy é uma ferramenta implementada em **Python** (3.5.1), e para sua instalação é necessário ter instalado também o PIP.
Para instalar o NDeploy basta executar o comando:

```
pip install git+https://git.nexxera.com/ci-utils/ndeploy.git
```

# **Exemplos do arquivo de deployment**

- [Deploy de uma única aplicação, contendo os dados do ambiente pra deploy.](ci-utils/ndeploy$1)

    - Comando: ndeploy deploy -f app.json

- [Deploy de uma única aplicação, informando dados do ambiente via linha de comando.](https://git.nexxera.com/ci-utils/ndeploy/snippets/2)

    - Comando: ndeploy deploy -f app.json -h dev.nexxera.com -t dokku

- [Deploy de uma única aplicação, informando o ambiente via linha de comando.](https://git.nexxera.com/ci-utils/ndeploy/snippets/2)

    - É necessário ter cadastrado o ambiente, através do comando: ndeploy addenv
    - Comando: ndeploy deploy -f app.json -e dev

- [Deploy de várias aplicações, informando o ambiente via linha de comando.](https://git.nexxera.com/ci-utils/ndeploy/snippets/3)

    - É necessário ter cadastrado o ambiente, através do comando: ndeploy addenv
    - Comando: ndeploy deploy -f app.json -e dev

