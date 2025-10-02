#!/usr/bin/env bash
set -o errexit

echo "Installing dependencies..."
pip install --upgrade pip
pip install --no-cache-dir -r requirements.txt

echo "Collecting static files..."
python manage.py collectstatic --no-input --clear

echo "Running migrations..."
python manage.py migrate --no-input

echo "Resetting admin password..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
try:
    user = User.objects.get(username='admin1')  # Change 'admin' to your username
    user.set_password('Aryan@7827')  # Change to your new password
    user.save()
    print('Password reset successfully!')
except User.DoesNotExist:
    print('User does not exist')
EOF

echo "Build completed successfully!"