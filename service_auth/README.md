### Структура /src

- /app - непосредственно приложение
  - \_\_init__.py - application factory
  - /models - модели
  - /services - бизнес-логика
  - /views - ендпойнты
  - /db - модули с абстракциями для базы данных и редис
  - /core - общие модули
  - /docs - информация по сервису
  
- /migrations - миграции alembic
- config.py - конфигурация Flask
- manage.py - создание экземпляра приложения, консольные команды

### Локальный запуск

- Перейти в папку auth `cd ./auth`
- Переименовать env.local.example в .env.local `cp .env.local.example .env.local`
- Запустить контейнеры postgres и redis при необходимости `make run-db`
- Применить миграции `make upgrade` (если миграций нет - то создать и применить `make init`)
- Запустить сервис `make run`
- По завершении работы удалить контейнеры `make stop-db` (контейнеры без volume - все данные удалятся)

Для создания новой миграции `make migrate msg='migration description here`


### Тесты

- Переименовать env.test.example в .env.test `cp .env.test.local.example .env.test.local`
- Запустить контейнеры для тестов `make run-test-db`
- Запустить тесты `make test`
- По завершении тестирования удалить контейнеры `make stop-test-db`

### Использование
Описание API (Swagger) можно получить по адресу (при запущенном сервисе локально) http://localhost:5000/auth/openapi/  
Файл описания API находится в /docs/openapi.yaml
Jaeger UI доступен по адресу http://127.0.0.1:16686/ 
