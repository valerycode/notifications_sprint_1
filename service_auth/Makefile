run-db:
	docker run --env-file .env.local --name postgres_auth -p 25432:5432 -d postgres:15.1-alpine
	docker run --name redis_auth -p 26379:6379 -d redis:7.0.5-alpine
	docker run --name jaeger -p 6831:6831/udp -p 16686:16686 -d  jaegertracing/all-in-one:1.41

stop-db:
	docker rm --force postgres_auth
	docker rm --force redis_auth
	docker rm --force jaeger

init:
	sh -c "export FLASK_SKIP_DOTENV=1 && export FLASK_APP='./src/manage.py' && flask db init --directory src/migrations && flask db migrate --directory src/migrations && flask db upgrade --directory src/migrations"

upgrade:
	sh -c "export FLASK_SKIP_DOTENV=1 && export FLASK_APP='./src/manage.py' && flask db upgrade --directory src/migrations"

migrate:
	sh -c "export FLASK_SKIP_DOTENV=1 && export FLASK_APP='./src/manage.py' && flask db migrate --directory src/migrations -m '${msg}'"

run:
	sh -c "export FLASK_SKIP_DOTENV=1 && python3 ./src/manage.py"

run-test-db:
	docker run --env POSTGRES_USER=app --env POSTGRES_PASSWORD=123qwe --env POSTGRES_DB=auth_database_test --name postgres_auth_test -p 45432:5432 -d postgres:15.1-alpine
	docker run --name redis_auth_test -p 46379:6379 -d redis:7.0.5-alpine

test:
	pytest ./tests

stop-test-db:
	docker rm --force postgres_auth_test
	docker rm --force redis_auth_test
