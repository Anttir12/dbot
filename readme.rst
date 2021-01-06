I'm a Dbot

Install requirements found in requirements.txt. Also see the file for some additional info (especially for windows)

Download & install ffmpeg https://ffmpeg.org/download.html

copy .env.template to .env and modify the necessary settings.

in project root run:

| ``python manage.py migrate``
| ``python manage.py collectstatic``
| ``python manage.py createsuperuser``

ready to go