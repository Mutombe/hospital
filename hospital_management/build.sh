#!/usr/bin/env bash
# Exit on error
set -o errexit

cd backend
pip install -r requirements.txt

# Convert static asset files
python manage.py collectstatic --no-input

# Apply any outstanding database migrations
python manage.py migrate

#python manage.py createsuperuser --noinput --username zim-rec --email simbamtombe@gmail.com 