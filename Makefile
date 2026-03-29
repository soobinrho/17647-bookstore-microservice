#!make
include .env
export
GIT_HASH := $(shell git rev-parse --short HEAD)

all:	build push

build:
	cd ./api-service-books/ && \
		docker build -t soobinrho/17647-bookstore-api-service-books:latest \
		-t soobinrho/17647-bookstore-api-service-books:$(GIT_HASH) .
	cd ./api-service-customers/ && \
		docker build -t soobinrho/17647-bookstore-api-service-customers:latest \
		-t soobinrho/17647-bookstore-api-service-customers:$(GIT_HASH) .
	cd ./bff-desktop/ && \
		docker build -t soobinrho/17647-bookstore-bff-desktop:latest \
		-t soobinrho/17647-bookstore-bff-desktop:$(GIT_HASH) .
	cd ./bff-mobile/ && \
		docker build -t soobinrho/17647-bookstore-bff-mobile:latest \
		-t soobinrho/17647-bookstore-bff-mobile:$(GIT_HASH) .

push:
	cd ./api-service-books/ && \
		docker push soobinrho/17647-bookstore-api-service-books:latest && \
		docker push soobinrho/17647-bookstore-api-service-books:$(GIT_HASH)
	cd ./api-service-customers/ && \
		docker push soobinrho/17647-bookstore-api-service-customers:latest && \
		docker push soobinrho/17647-bookstore-api-service-customers:$(GIT_HASH)
	cd ./bff-desktop && \
		docker push soobinrho/17647-bookstore-bff-desktop:latest && \
		docker push soobinrho/17647-bookstore-bff-desktop:$(GIT_HASH)
	cd ./bff-mobile && \
		docker push soobinrho/17647-bookstore-bff-mobile:latest && \
 		docker push soobinrho/17647-bookstore-bff-mobile:$(GIT_HASH)

prod-deploy-ec2-bookstore-a: ensure-env-file-exists prod-docker-reset
	docker pull soobinrho/17647-bookstore-bff-desktop:latest
	docker run --detach --name bookstore-bff-desktop \
		-p 80:80 \
		--env API_SERVICES_LOAD_BALANCER_URL="${API_SERVICES_LOAD_BALANCER_URL}" \
		soobinrho/17647-bookstore-bff-desktop:latest
	docker pull soobinrho/17647-bookstore-api-service-customers:latest
	docker run --detach --name bookstore-api-service-customers \
		-p 3000:3000 \
		--env DB_USER="${DB_USER}" \
		--env DB_PASS="${DB_PASS}" \
		--env DB_URL="${DB_URL}" \
		--env GEMINI_API_KEY="${GEMINI_API_KEY}" \
		soobinrho/17647-bookstore-api-service-customers:latest

prod-deploy-ec2-bookstore-b: ensure-env-file-exists prod-docker-reset
	docker pull soobinrho/17647-bookstore-bff-desktop:latest
	docker run --detach --name bookstore-bff-desktop \
		-p 80:80 \
		--env API_SERVICES_LOAD_BALANCER_URL="${API_SERVICES_LOAD_BALANCER_URL}" \
		soobinrho/17647-bookstore-bff-desktop:latest
	docker pull soobinrho/17647-bookstore-api-service-books:latest
	docker run --detach --name bookstore-api-service-books \
		-p 3000:3000 \
		--env DB_USER="${DB_USER}" \
		--env DB_PASS="${DB_PASS}" \
		--env DB_URL="${DB_URL}" \
		--env GEMINI_API_KEY="${GEMINI_API_KEY}" \
		soobinrho/17647-bookstore-api-service-books:latest

prod-deploy-ec2-bookstore-c: ensure-env-file-exists prod-docker-reset
	docker pull soobinrho/17647-bookstore-bff-mobile:latest
	docker run --detach --name bookstore-bff-mobile \
		-p 80:80 \
		--env API_SERVICES_LOAD_BALANCER_URL="${API_SERVICES_LOAD_BALANCER_URL}" \
		soobinrho/17647-bookstore-bff-mobile:latest
	docker pull soobinrho/17647-bookstore-api-service-books:latest
	docker run --detach --name bookstore-api-service-books \
		-p 3000:3000 \
		--env DB_USER="${DB_USER}" \
		--env DB_PASS="${DB_PASS}" \
		--env DB_URL="${DB_URL}" \
		--env GEMINI_API_KEY="${GEMINI_API_KEY}" \
		soobinrho/17647-bookstore-api-service-books:latest

prod-deploy-ec2-bookstore-d: ensure-env-file-exists prod-docker-reset
	docker pull soobinrho/17647-bookstore-bff-mobile:latest
	docker run --detach --name bookstore-bff-mobile \
		-p 80:80 \
		--env API_SERVICES_LOAD_BALANCER_URL="${API_SERVICES_LOAD_BALANCER_URL}" \
		soobinrho/17647-bookstore-bff-mobile:latest
	docker pull soobinrho/17647-bookstore-api-service-customers:latest
	docker run --detach --name bookstore-api-service-customers \
		-p 3000:3000 \
		--env DB_USER="${DB_USER}" \
		--env DB_PASS="${DB_PASS}" \
		--env DB_URL="${DB_URL}" \
		--env GEMINI_API_KEY="${GEMINI_API_KEY}" \
		soobinrho/17647-bookstore-api-service-customers:latest

prod-docker-reset:
	docker ps --filter 'name=bookstore-' -aq | xargs docker stop | xargs docker rm

test-desktop-books: ensure-env-file-exists
	docker run --rm --detach --name dev-bookstore-bff-desktop \
		-p 80:80\
		--add-host host.docker.internal:host-gateway \
		--env API_SERVICES_LOAD_BALANCER_URL='http://host.docker.internal:3000' \
		soobinrho/17647-bookstore-bff-desktop:latest
	docker run --rm --detach --name dev-bookstore-api-service-books \
		-p 3000:3000 \
		--add-host host.docker.internal:host-gateway \
		--env DB_USER="${DB_USER}" \
		--env DB_PASS="${DB_PASS}" \
		--env DB_URL='host.docker.internal' \
		--env GEMINI_API_KEY="${GEMINI_API_KEY}" \
		soobinrho/17647-bookstore-api-service-books:latest
	docker ps
	echo 'Port 80: dev-bookstore-bff-desktop'
	echo 'Port 3000: dev-bookstore-api-service-books'

test-desktop-customers: ensure-env-file-exists
	docker run --rm --detach --name dev-bookstore-bff-desktop \
		-p 80:80\
		--add-host host.docker.internal:host-gateway \
		--env API_SERVICES_LOAD_BALANCER_URL='http://host.docker.internal:3000' \
		soobinrho/17647-bookstore-bff-desktop:latest
	docker run --rm --detach --name dev-bookstore-api-service-customers \
		-p 3000:3000 \
		--add-host host.docker.internal:host-gateway \
		--env DB_USER="${DB_USER}" \
		--env DB_PASS="${DB_PASS}" \
		--env DB_URL='host.docker.internal' \
		--env GEMINI_API_KEY="${GEMINI_API_KEY}" \
		soobinrho/17647-bookstore-api-service-customers:latest
	docker ps
	echo 'Port 80: dev-bookstore-bff-desktop'
	echo 'Port 3000: dev-bookstore-api-service-customers'

test-mobile-books: ensure-env-file-exists
	docker run --rm --detach --name dev-bookstore-bff-mobile \
		-p 80:80 \
		--add-host host.docker.internal:host-gateway \
		--env API_SERVICES_LOAD_BALANCER_URL='http://host.docker.internal:3000' \
		soobinrho/17647-bookstore-bff-mobile:latest
	docker run --rm --detach --name dev-bookstore-api-service-books \
		-p 3000:3000 \
		--add-host host.docker.internal:host-gateway \
		--env DB_USER="${DB_USER}" \
		--env DB_PASS="${DB_PASS}" \
		--env DB_URL='host.docker.internal' \
		--env GEMINI_API_KEY="${GEMINI_API_KEY}" \
		soobinrho/17647-bookstore-api-service-books:latest
	docker ps
	echo 'Port 80: dev-bookstore-bff-mobile'
	echo 'Port 3000: dev-bookstore-api-service-books'

test-mobile-customers: ensure-env-file-exists
	docker run --rm --detach --name dev-bookstore-bff-mobile \
		-p 80:80 \
		--add-host host.docker.internal:host-gateway \
		--env API_SERVICES_LOAD_BALANCER_URL='http://host.docker.internal:3000' \
		soobinrho/17647-bookstore-bff-mobile:latest
	docker run --rm --detach --name dev-bookstore-api-service-customers \
		-p 3000:3000 \
		--add-host host.docker.internal:host-gateway \
		--env DB_USER="${DB_USER}" \
		--env DB_PASS="${DB_PASS}" \
		--env DB_URL='host.docker.internal' \
		--env GEMINI_API_KEY="${GEMINI_API_KEY}" \
		soobinrho/17647-bookstore-api-service-customers:latest
	docker ps
	echo 'Port 80: dev-bookstore-bff-mobile'
	echo 'Port 3000: dev-bookstore-api-service-customers'

test-create-db: ensure-env-file-exists
	docker run --rm --detach --name dev-bookstore-main-db \
		-p 3306:3306 \
		--add-host host.docker.internal:host-gateway \
		--env MARIADB_RANDOM_ROOT_PASSWORD='True' \
		--env MARIADB_USER="${DB_USER}" \
		--env MARIADB_PASSWORD="${DB_PASS}" \
		--env MARIADB_DATABASE='bookstore' \
		mariadb:latest

cleanup: test-cleanup

test-cleanup:
	bash -c '{ docker ps -aq --filter "name=dev-bookstore-api-service" && docker ps -aq --filter "name=dev-bookstore-bff"; }' \
		| sort | uniq -u \
		| xargs docker stop | xargs docker rm

test-cleanup-including-db:
	bash -c '{ docker ps -aq --filter "name=dev-bookstore-api-service" && docker ps -aq --filter "name=dev-bookstore-bff" && docker ps -aq --filter "name=dev-bookstore-main-db"; }' \
		| sort | uniq -u \
		| xargs docker stop | xargs docker rm

ensure-env-file-exists:
	test -s ./.env || { echo '[ERROR] .env file not found.'; exit 1; }

.SILENT: prod-deploy-ec2-bookstore-a prod-deploy-ec2-bookstore-b prod-deploy-ec2-bookstore-c prod-deploy-ec2-bookstore-d test-desktop-books test-desktop-customers test-mobile-books test-mobile-customers test-create-db cleanup test-cleanup test-cleanup-including-db ensure-env-file-exists
