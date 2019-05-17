# This Dockerfile is used to build ROBOKOP

FROM python:3.6.6-stretch

LABEL maintainer="patrick@covar.com"
ENV REFRESHED_AT 2018-06-05

ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

## Install basic tools
RUN apt-get update
RUN apt-get install -yq \
    vim

## Install NodeJS
RUN curl -sL https://deb.nodesource.com/setup_8.x | bash -
RUN apt-get install -y nodejs

## This thing is required for node? IDK
RUN apt-get install -yq \
    libkrb5-dev

## Set up home directory
ARG UID=1000
ARG GID=1000
RUN groupadd -g $GID murphy
RUN useradd -m -u $UID -g $GID -s /bin/bash murphy

WORKDIR /home/murphy/robokop-viewer

COPY requirements.txt requirements.txt

## Install all requirements
RUN pip install -r ./requirements.txt --src /usr/local/src

COPY package.json package.json
COPY package-lock.json package-lock.json

RUN npm install

## Get ROBOKOP software
COPY src src
COPY assets assets
COPY shared ../shared
COPY webpack.common.js webpack.common.js
COPY webpack.dev.js webpack.dev.js
COPY webpack.prod.js webpack.prod.js

RUN npm run webpackProd

COPY manager manager
COPY templates templates

WORKDIR /home/murphy

## Finish up
ENV HOME=/home/murphy
ENV USER=murphy

ENTRYPOINT ["python", "robokop-viewer/manager/server.py"]