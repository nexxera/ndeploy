# ndeploy
scripts to deploy N microservices to N PaaS, with a focus on development. It uses config files which can be templated, jinja2-style.

It is bare bones for now. Personal use.

# PaaS supported

  * dokku
  * openshift origin
  
# Pre-requisites

You need the CLI versions of each PaaS already installed:

 * dokku : https://github.com/dokku/dokku
 
  * redis plugin: https://github.com/dokku/dokku-redis
  * postgres single container plugin: https://github.com/Flink/dokku-psql-single-container
  * rabbitmq plugin: https://github.com/dokku/dokku-rabbitmq
  * mongo plugin: https://github.com/dokku/dokku-mongo
   
 * oc in the case of openshift origin
 
You need the PaaS already installed. You probably want to start with them under Vagrant on your PC. For each one of them, you want the plugins installed (PostgreSQL, RabbitMQ, etc).

# How to install

 * git clone this project
 * create a virtual env, install requirements.txt
 * run paver as described under "How to deploy"

# How to configure your project

You need to build a directory structure with some files/subdirs:

 * repos-to-clone.txt : a CSV file with 2 columns (3rd column optional): repository URL, branch to fetch [, app name when deployed]. Example:
```
git@bitbucket.org:sglebs/messenger-server.git,master
git@bitbucket.org:sglebs/core-server.git,master
```
 * databases : a directory with empty *.sql files, one for each app that needs its own database. Example: core-server.sql  messenger-server.sql
 * mongos : a directory with empty *.txt files, one for each app that needs its own MongoDB. Example: core-server.txt  messenger-server.txt
 * envs : a directory with *.env files (key=value format), defining environment variable for each one. Example: core-server.env as below
```
GUNICORN_BACKLOG=2048
GUNICORN_WORKER_CONNECTIONS=750
LANG=pt_BR.UTF-8
LOGLEVEL=DEBUG
```
 * rabbitmqs : a directory with:
   * A services.txt file, where each line lists teh name of the service and the 4 RabbitMQ exposed ports. Example:
   ```
   financial-platform,5672,5673,15672,15673
   ```
   * *.txt files with the names of the apps, and inside this file the name of the RabbitMQ service needed (from services.txt).  This will inject the env var RABBITMQ_URL in your app. Example: core-server.txt as below:
   ```
   financial-platform
   ```
   * *.json files with the names of the apps, and inside this file the configuration of RabbitMQ
 * redis : a directory with:
   * A services.txt file, where each line lists the name of the (redis) service. Example:
   ```
   redis-photos-cache
   ```
   * *.txt files with the names of the apps, and inside this file the name of the Redis service needed (from services.txt). This will inject the env var REDIS_URL in your app. Example: core-server.txt as below:
   ```
   redis-photos-cache
   ```
 * openshift_templates : Optional *.txt files with the names of the apps, and inside this file the custom parameters to "oc new-app" if you need to override somehow. You can use templated variable. Example:
 ```
 python:3.5 --name={appname} {repourl}#{branch} -l app={appname}
 ```
 * dokku_docker-options: Optional *.txt files with the names of the apps, and inside this file the custom parameters to docker-options, with the syntax phase=options. Example:
```
run=-m 128m
```

# How to Deploy

```
paver deployhost=dokku-vagrant.sglebs.com configdir=/my/configdir deploy
```
In the case of openshift, you may have exposed URLs using a different hostname. In these cases, use exposehost:
```
paver deployhost=dokku-vagrant.sglebs.com exposehost=my.domain.com configdir=/my/configdir deploy
```
You may want to "ifdef" dev/staging/live. This can be done using jinja2 syntax. Example of a repos-to-clone.txt:
```
{% if scenario|string() == "debug"%}
https://github.com/sglebs/ping.git,master,pong
{% endif %}
```
Obviously, for this to work you need to pass scenario=debug to paver:
```
paver deployhost=dokku-vagrant.sglebs.com configdir=/my/configdir scenario=debug deploy
```
If you need to template based on the target PaaS ("system" parameter, which can be passed in or auto-detected) or the deployhost, it can also be done, like this:
```
{% if system|string() == "dokku" or deployhost|string() == "openshift.sglebs.com"%}
https://github.com/sglebs/mykibana.git,master
https://github.com/sglebs/myelasticsearch.git,master
{% endif %}
```







