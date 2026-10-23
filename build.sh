#!/usr/bin/env bash
# Roda na hospedagem a cada deploy
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
