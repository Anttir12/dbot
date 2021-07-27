FROM python:3.8.11

RUN mkdir /app
WORKDIR /app
ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC
RUN apt-get update && apt-get install -y libffi-dev python3-dev libnacl-dev build-essential ffmpeg opus-tools libogg0 libopus0 libmagic1 git espeak-ng espeak

RUN pip install daphne

COPY requirements_no_cache_dir.txt .
RUN pip --no-cache-dir install -r requirements_no_cache_dir.txt

COPY requirements.txt .
RUN pip install -r requirements.txt

ADD . /app/
RUN python bot/tts.py
RUN python manage.py collectstatic --noinput --settings=dbot.no_bot_settings
EXPOSE 4322
