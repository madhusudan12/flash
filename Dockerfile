FROM python:3.6.12-slim-buster

RUN apt-get update && apt-get install -y jq less git vim curl && useradd -m appuser
RUN mkdir -p /home/appuser/.ssh && mkdir -p /home/appuser/app
ENV PATH "${PATH}:/home/appuser/.local/bin"

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY requirements.txt /
RUN pip3 install -r /requirements.txt

COPY . /app
COPY --chown=appuser . /home/appuser/app
WORKDIR /home/appuser/app