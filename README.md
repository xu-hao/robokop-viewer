# ROBOKOP-viewer

ROBOKOP-viewer is a tool for viewing knowledge graphs as part of the NCATS translator and reasoner programs. The ROBOKOP system consists of a web based user interface, an API server, and several worker servers. The code is separated into three separate repositories.

* robokop - https://github.com/xu-hao/robokop-viewer - UI and entry point

This repository is the main repository for the user interface and storage modules. It is also used for issue tracking associated with the entire stack.

## Example Installation
See an instance at http://robokop.renci.org

## Setup Instructions 

### Structure of source code

We create a root robokop directory and clone the three repos into it: robokop, robokop-interfaces, and robokop-rank. 

In the root directory, we create shared and logs diretories. 

Into the "shared" directory we need a "robokop.env" file with setup environment variables. This is discussed in more detail below.

This is our directory structure:
```
robokop-root
├── logs
├── robokop
├── robokop-interfaces
├── robokop-rank
└── shared
    └── robokop.env
```

A few more folders will be created in this directory depending on which docker containers are in use.

### Prerequisites

Robokop requires docker, docker-compose and Node.js. These must be installed and configured correctly. For additional install notes for CentOS 7. See [here](./doc/centos_installation.md). For installation on Windows, please refer to the section on [Windows installation](#windows)

### Docker-Compose Files

Robokop uses a collection of docker containers managed through several instances of docker-compose. Independent docker-compose files are used to enable different parts of the system to be deployed on separate machines. 

* robokop/deploy/backend - Rabbit MQ message broker, Celery results redis backend, NLP machine
* robokop/deploy/manager - Web UI, API server, UI storage, Graphql server
* robokop/deploy/graph - Neo4j graph database
* robokop/deploy/cache - Redis cache of http requests
* robokop-rank/deploy/ranker - API server for ranking service
* robokop-rank/deploy/omnicorp - Postgres storage for omnicorp pairs
* robokop-interfaces/deploy - API server for knowledge graph construction service

Each of these docker-compose files will control one or more docker containers. Some of these containers such as the Neo4j database (robokop/deploy/graph) and the Omnicorp (robokop-rank/deploy/omnicorp) can be rather resource intensive. It may be advantageous to place those containers on different machines.  Communications between all of these containers can then be done using a common Docker network or WAN. These settings are configurable through environmental variables.

### Environment settings

`robokop-root/shared/robokop.env` needs to hold a variety of configuration parameters. These parameters specify public ports and the location of other components of the system. 

```
#################### ROBOKOP Environmental Variables ####################

# Web Interface and API
ROBOKOP_HOST=127.0.0.1
ROBOKOP_PROTOCOL=http
MANAGER_PORT=80

COMPOSE_PROJECT_NAME=robokop

```
You'll need to supply values for the secret things at the end.

### Building Containers

For each container listed above you will need to build the container with specified user and group permissions so that log file ownership does not get elevated. For example for the primary robokop UI container

```
$ cd robokop-viewer
$ docker build --build-arg UID=$(id -u) --build-arg GID=$(id -g) -t robokop_manager -f deploy/manager/Dockerfile .
```

This process should be repeated for `robokop-interfaces/deploy` and `robokop-rank/deploy/ranker`. Other containers can be built using `docker-compose build`.

## Starting Containers

Once all containers are built each can be started using 

```
docker-compose up
```

This process must be completed such that each docker-compose is started. It is not required that each container is running on the same machine, but the environmental variables must be modified to note the location where different services are running. For example, for the environmental variables shown above, two machines are in use. `robokopdb.renci.org` is used to host the Neo4j database, the Omnicorp database, and the redis HTTP request cache. This is reflected in the environmental variables `NEO4J_HOST`, `OMNICORP_HOST` and, `CACHE_HOST`. All other containers are running on `robokop.renci.org`. These containers are all on the same docker network and can then be routed using their container names. With this configuration this same set of environmental variables can be used on both machines. It is possible that other configurations may require different environmental variables on each machine, for example if the `ranker` and `manager` where running on different machines.  


## Web Interfaces

With all containers started you can now monitor each component using the urls below (using the port settings listed above).

* http://127.0.0.1 - The robokop-viewer user interface
* http://127.0.0.1/apidocs/ - The robokop-viewer user interface API

## <a name="windows"></a>Windows Installation
To install on Windows, we recommend utilizing the Windows subsystem for Linux (WSL). 
1. First, you will need to install Docker for Windows. Then follow the instructions [here](https://nickjanetakis.com/blog/setting-up-docker-for-windows-and-wsl-to-work-flawlessly) to get docker working on WSL.

2. Install Node.js in WSL

3. Docker does not correctly follow the symlinks in the `.env` file in each of the "Docker-Compose Files" section when executed on Windows / WSL. To get `docker-compose build` and `docker-compose up` to work correctly, you will need to do the following in any given bash session prior to executing any docker commands. These will ensure that the env variables defined in `/shared/robokop.env` are correctly exported when executing the docker commands
    1. `set -a`
    2. `source ../../../shared/robokop.env`

4. You can add the 2 commands above to your `.bashrc` file in WSL to ensure that these env variables are always available and correctly exported and made available to docker. Note that the relative path to the `/shared/robokop.env` file will differ based on your current working directory in your bash session.

5. Run the steps outlined in the "Web Interface Compilation" section
