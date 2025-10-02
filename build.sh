#!/usr/bin/env bash
set -o errexit

echo "Installing dependencies..."
pip install --upgrade pip
pip install --no-cache-dir -r requirements.txt

echo "Collecting static files..."
python manage.py collectstatic --no-input --clear

echo "Running migrations..."
python manage.py migrate --no-input

echo "Creating superuser..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
username = 'admin1'
email = 'admin@example.com'
password = 'Aryan@7827'

# Delete old user if exists and create fresh
if User.objects.filter(username=username).exists():
    User.objects.filter(username=username).delete()
    print(f'Deleted existing user: {username}')

User.objects.create_superuser(username=username, email=email, password=password)
print(f'Created superuser: {username}')
EOF

echo "Build completed successfully!"