#!make
include .env
export

all:	build push

build:
	cd ./api-service-books/ && \
		docker build -t soobinrho/17647-bookstore-api-service-books:latest -t soobinrho/17647-bookstore-api-service-books:$(git rev-parse --short HEAD) .
	cd ./api-service-customers/ && \
		docker build -t soobinrho/17647-bookstore-api-service-customers:latest -t soobinrho/17647-bookstore-api-service-customers:$(git rev-parse --short HEAD) .
	cd ./bff-main/ && \
		docker build -t soobinrho/17647-bookstore-bff-main:latest -t soobinrho/17647-bookstore-bff-main:$(git rev-parse --short HEAD) .
	cd ./bff-mobile/ && \
		docker build -t soobinrho/17647-bookstore-bff-mobile:latest -t soobinrho/17647-bookstore-bff-mobile:$(git rev-parse --short HEAD) .

push:
	cd ./api-service-books/ && \
		docker push soobinrho/17647-bookstore-api-service-books:latest && \
		docker push soobinrho/17647-bookstore-api-service-books:$(git rev-parse --short HEAD)
	cd ./api-service-customers/ && \
		docker push soobinrho/17647-bookstore-api-service-customers:latest && \
		docker push soobinrho/17647-bookstore-api-service-customers:$(git rev-parse --short HEAD)
	cd ./bff-main && \
		docker push soobinrho/17647-bookstore-bff-main:latest && \
		docker push soobinrho/17647-bookstore-bff-main:$(git rev-parse --short HEAD)
	cd ./bff-mobile && \
		docker push soobinrho/17647-bookstore-bff-mobile:latest && \
 		docker push soobinrho/17647-bookstore-bff-mobile:$(git rev-parse --short HEAD)

test:
	docker run --rm --detach --name dev-bookstore-main-db -p 3306:3306 --add-host host.docker.internal:host-gateway --env MARIADB_RANDOM_ROOT_PASSWORD='True' --env MARIADB_USER='bookstore' --env MARIADB_PASSWORD='RwIIWUoToKe6L1LZAlUlFy9r4iRl4' --env MARIADB_DATABASE='bookstore' mariadb:latest
	docker run --rm --name dev-bookstore-api-service-books \
		-p 3000:3000 \
		--add-host host.docker.internal:host-gateway \
		--env BOOKSTORE_BACKEND_DB_USER="${BOOKSTORE_BACKEND_DB_USER}" \
		--env BOOKSTORE_BACKEND_DB_PASS="${BOOKSTORE_BACKEND_DB_PASS}" \
		--env BOOKSTORE_BACKEND_DB_URL='host.docker.internal' \
		--env GEMINI_API_KEY="${GEMINI_API_KEY}" \
		soobinrho/17647-bookstore-api-service-books:latest
	docker run --rm --name dev-bookstore-api-service-customers \
		-p 3001:3001 \
		--add-host host.docker.internal:host-gateway \
		--env BOOKSTORE_BACKEND_DB_USER="${BOOKSTORE_BACKEND_DB_USER}" \
		--env BOOKSTORE_BACKEND_DB_PASS="${BOOKSTORE_BACKEND_DB_PASS}" \
		--env BOOKSTORE_BACKEND_DB_URL='host.docker.internal' \
		--env GEMINI_API_KEY="${GEMINI_API_KEY}" \
		soobinrho/17647-bookstore-api-service-customers:latest
	docker run --rm --name dev-bookstore-bff-main \
		-p 8000:8000 \
		--add-host host.docker.internal:host-gateway \
		soobinrho/17647-bookstore-bff-main:latest
	docker run --rm --name dev-bookstore-bff-mobile \
		-p 8001:8001 \
		--add-host host.docker.internal:host-gateway \
		soobinrho/17647-bookstore-bff-mobile:latest
	echo 'Port 8000: dev-bookstore-bff-main'
	echo 'Port 8001: dev-bookstore-bff-mobile'
	echo 'Port 3000: dev-bookstore-api-service-books'
	echo 'Port 3001: dev-bookstore-api-service-customers-'

test-cleanup:
	docker ps --filter 'name=dev-bookstore-main-db' -aq | xargs docker stop | xargs docker rm
	docker ps --filter 'name=dev-bookstore-api-service-books' -aq | xargs docker stop | xargs docker rm
	docker ps --filter 'name=dev-bookstore-api-service-customers' -aq | xargs docker stop | xargs docker rm
	docker ps --filter 'name=dev-bookstore-bff-main' -aq | xargs docker stop | xargs docker rm
	docker ps --filter 'name=dev-bookstore-bff-mobile' -aq | xargs docker stop | xargs docker rm

.SILENT: test test-cleanup
