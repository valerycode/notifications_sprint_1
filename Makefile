include .env

auth-init:
	docker compose exec auth flask db upgrade
	docker compose exec auth flask insert-roles
	docker compose exec auth flask createsuperuser --email ${AUTH_SUPERUSER_LOGIN} --password ${AUTH_SUPERUSER_PASSWORD}

admin-notifications-init:
	docker compose exec admin_notifications python manage.py migrate
	docker compose exec admin_notifications python manage.py collectstatic --no-input
	docker compose exec -e DJANGO_SUPERUSER_PASSWORD=${DJANGO_ADMIN_NOTICE_SUPERUSER_PASSWORD} admin_notifications python manage.py createsuperuser --username ${DJANGO_ADMIN_NOTICE_SUPERUSER_LOGIN} --email admin@example.com --no-input


dev-run:
	docker compose up --build -d
	sleep 5  # ждем запуск постгрес для применения миграций
	$(MAKE) auth-init
	$(MAKE) admin-notifications-init
	docker compose exec auth python fake_data.py


format:
	black .
	isort .

lint:
	black --check .
	isort --check-only .
	flake8 .
