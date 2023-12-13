# Проектная работа 10 спринта
Основной репозиторий: https://github.com/Pummas/notifications_sprint_1

Над проектом работали:  
* Михаил Лукин (Тимлид) https://github.com/Pummas
* Валерия Малышева https://github.com/valerycode
* Роман Боровский https://github.com/RomanBorovskiy
* Сергей Моричев https://github.com/s-morichev

### Структура разделов
* /service_auth - сервис аутентификации и авторизации
* /service_notice - сервис нотификации
* /service_notice/admin_notice - админ-панель сервиса

### Запуск сервисов

Переименуйте env.example в .env. Затем выполните `make dev-run`


Админка доступна по адресу http://127.0.0.1/admin, логин superuser, пароль
password (можно поменять в .env файле.) При создании рассылок в поле recipients
нужно вставлять id из списка `c3696fea-68d3-4de6-a854-0d101304d85d, 18e28a84-78bb-453b-8108-cf33c934fedb, 
30d063a1-9289-4235-a78e-21d79afadfbc, 5ba55f12-94f2-45d9-8483-bd5dc4812e6e, 
b7571439-33d3-4122-95f9-16d57e9d9265` или весь список.


Документация (openapi) апи уведомлений доступна по адресу http://127.0.0.1/api/openapi

