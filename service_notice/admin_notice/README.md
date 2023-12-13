Админ панель для создания рассылок

Перед началом работы с админкой необходимо выполнить следующие команды:

1. Применить миграции
```
docker-compose exec admin_notifications python manage.py migrate
```
2. Создать суперпользователя
```
docker-compose exec admin_notifications python manage.py createsuperuser
```
3. Загрузить статические файлы
```
docker-compose exec admin_notifications python manage.py collectstatic --no-input
```