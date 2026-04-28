#!make
include .env
export
GIT_HASH := $(shell git rev-parse --short HEAD)

all:	build push

ensure-env-file-exists:
	test -s ./.env || { echo '[ERROR] .env file not found.'; exit 1; }

build:
	cd ./api-service-books-commands/ && \
		docker build -t soobinrho/17647-bookstore-api-service-books-commands:latest \
		-t soobinrho/17647-bookstore-api-service-books-commands:$(GIT_HASH) .
	cd ./api-service-books-queries/ && \
		docker build -t soobinrho/17647-bookstore-api-service-books-queries:latest \
		-t soobinrho/17647-bookstore-api-service-books-queries:$(GIT_HASH) .
	cd ./api-service-customers/ && \
		docker build -t soobinrho/17647-bookstore-api-service-customers:latest \
		-t soobinrho/17647-bookstore-api-service-customers:$(GIT_HASH) .
	cd ./bff-desktop/ && \
		docker build -t soobinrho/17647-bookstore-bff-desktop:latest \
		-t soobinrho/17647-bookstore-bff-desktop:$(GIT_HASH) .
	cd ./bff-mobile/ && \
		docker build -t soobinrho/17647-bookstore-bff-mobile:latest \
		-t soobinrho/17647-bookstore-bff-mobile:$(GIT_HASH) .
	cd ./crm-service-customers/ && \
		docker build -t soobinrho/17647-bookstore-crm-service-customers:latest \
		-t soobinrho/17647-bookstore-crm-service-customers:$(GIT_HASH) .
	cd ./cronjob-sync-data/ && \
		docker build -t soobinrho/17647-bookstore-cronjob-sync-data:latest \
		-t soobinrho/17647-bookstore-cronjob-sync-data:$(GIT_HASH) .

push:
	cd ./api-service-books-commands/ && \
		docker push soobinrho/17647-bookstore-api-service-books-commands:latest && \
		docker push soobinrho/17647-bookstore-api-service-books-commands:$(GIT_HASH)
	cd ./api-service-books-queries/ && \
		docker push soobinrho/17647-bookstore-api-service-books-queries:latest && \
		docker push soobinrho/17647-bookstore-api-service-books-queries:$(GIT_HASH)
	cd ./api-service-customers/ && \
		docker push soobinrho/17647-bookstore-api-service-customers:latest && \
		docker push soobinrho/17647-bookstore-api-service-customers:$(GIT_HASH)
	cd ./bff-desktop && \
		docker push soobinrho/17647-bookstore-bff-desktop:latest && \
		docker push soobinrho/17647-bookstore-bff-desktop:$(GIT_HASH)
	cd ./bff-mobile && \
		docker push soobinrho/17647-bookstore-bff-mobile:latest && \
 		docker push soobinrho/17647-bookstore-bff-mobile:$(GIT_HASH)
	cd ./crm-service-customers/ && \
		docker push soobinrho/17647-bookstore-crm-service-customers:latest && \
 		docker push soobinrho/17647-bookstore-crm-service-customers:$(GIT_HASH)
	cd ./cronjob-sync-data/ && \
		docker push soobinrho/17647-bookstore-cronjob-sync-data:latest && \
		docker push soobinrho/17647-bookstore-cronjob-sync-data:$(GIT_HASH)

# =====
# Tests
# =====
test-create-db: ensure-env-file-exists
	docker run --detach --name dev-db-books-commands \
		-p 3306:3306 \
		--add-host host.docker.internal:host-gateway \
		--env MARIADB_RANDOM_ROOT_PASSWORD='True' \
		--env MARIADB_USER=${DB_BOOKS_COMMANDS_USER} \
		--env MARIADB_PASSWORD=${DB_BOOKS_COMMANDS_PASS} \
		--env MARIADB_DATABASE=${DB_BOOKS_COMMANDS_DATABASE} \
		mariadb:latest
	docker run --detach --name dev-db-books-queries \
		-p 27017:27017 \
		--add-host host.docker.internal:host-gateway \
		--env MONGO_INITDB_ROOT_USERNAME=${DB_BOOKS_QUERIES_USER} \
		--env MONGO_INITDB_ROOT_PASSWORD=${DB_BOOKS_QUERIES_PASS} \
		mongo:latest
	docker run --detach --name dev-db-customers \
		-p 3307:3306 \
		--add-host host.docker.internal:host-gateway \
		--env MARIADB_RANDOM_ROOT_PASSWORD='True' \
		--env MARIADB_USER=${DB_CUSTOMERS_USER} \
		--env MARIADB_PASSWORD=${DB_CUSTOMERS_PASS} \
		--env MARIADB_DATABASE=${DB_CUSTOMERS_DATABASE} \
		mariadb:latest

test: ensure-env-file-exists
	docker run --detach --name dev-bookstore-bff-desktop \
		-p 80:80 \
		--add-host host.docker.internal:host-gateway \
		--env IS_DEV='1' \
		soobinrho/17647-bookstore-bff-desktop:latest
	docker run --detach --name dev-bookstore-bff-mobile \
		-p 81:80 \
		--add-host host.docker.internal:host-gateway \
		--env IS_DEV='1' \
		soobinrho/17647-bookstore-bff-mobile:latest
	docker run --detach --name dev-bookstore-api-service-books-commands \
		-p 3000:3000 \
		--add-host host.docker.internal:host-gateway \
		--env IS_DEV='1' \
		--env DB_URL='host.docker.internal' \
		--env DB_PORT='3306' \
		--env DB_USER=${DB_BOOKS_COMMANDS_USER} \
		--env DB_PASS=${DB_BOOKS_COMMANDS_PASS} \
		--env DB_DATABASE=${DB_BOOKS_COMMANDS_DATABASE} \
		--env GEMINI_API_KEY=${GEMINI_API_KEY} \
		soobinrho/17647-bookstore-api-service-books-commands:latest
	docker run --detach --name dev-bookstore-api-service-books-queries \
		-p 3001:3000 \
		--add-host host.docker.internal:host-gateway \
		--env IS_DEV='1' \
		--env DB_URL='host.docker.internal' \
		--env DB_PORT='27017' \
		--env DB_USER=${DB_BOOKS_QUERIES_USER} \
		--env DB_PASS=${DB_BOOKS_QUERIES_PASS} \
		--env DB_DATABASE=${DB_BOOKS_QUERIES_DATABASE} \
		--env DB_COLLECTION=${DB_BOOKS_QUERIES_COLLECTION} \
		--env API_RELATED_BOOKS_URL=${API_RELATED_BOOKS_URL_DEV} \
		--env DB_BOOKS_COMMANDS_URL='host.docker.internal' \
		--env DB_BOOKS_COMMANDS_PORT='3306' \
		--env DB_BOOKS_COMMANDS_USER=${DB_BOOKS_COMMANDS_USER} \
		--env DB_BOOKS_COMMANDS_PASS=${DB_BOOKS_COMMANDS_PASS} \
		--env DB_BOOKS_COMMANDS_DATABASE=${DB_BOOKS_COMMANDS_DATABASE} \
		soobinrho/17647-bookstore-api-service-books-queries:latest
	docker run --detach --name dev-bookstore-api-service-customers \
		-p 3003:3000 \
		--add-host host.docker.internal:host-gateway \
		--env IS_DEV='1' \
		--env DB_URL='host.docker.internal' \
		--env DB_PORT='3307' \
		--env DB_USER=${DB_CUSTOMERS_USER} \
		--env DB_PASS=${DB_CUSTOMERS_PASS} \
		--env DB_DATABASE=${DB_CUSTOMERS_DATABASE} \
		--env KAFKA_TOPIC=${KAFKA_TOPIC} \
		--env KAFKA_BROKER_0_URL=${KAFKA_BROKER_0_URL} \
		--env KAFKA_BROKER_1_URL=${KAFKA_BROKER_1_URL} \
		--env KAFKA_BROKER_2_URL=${KAFKA_BROKER_2_URL} \
		soobinrho/17647-bookstore-api-service-customers:latest
	docker run --detach --name dev-bookstore-crm-service-customers \
		--env KAFKA_TOPIC=${KAFKA_TOPIC} \
		--env KAFKA_BROKER_0_URL=${KAFKA_BROKER_0_URL} \
		--env KAFKA_BROKER_1_URL=${KAFKA_BROKER_1_URL} \
		--env KAFKA_BROKER_2_URL=${KAFKA_BROKER_2_URL} \
		--env SMTP_SERVER_URL=${SMTP_SERVER_URL} \
		--env SMTP_SERVER_PORT=${SMTP_SERVER_PORT} \
		--env SMTP_SERVER_ID=${SMTP_SERVER_ID} \
		--env SMTP_SERVER_PASS=${SMTP_SERVER_PASS} \
		soobinrho/17647-bookstore-crm-service-customers:latest
	docker run --detach --name dev-bookstore-cronjob-sync-data \
		--add-host host.docker.internal:host-gateway \
		--env IS_DEV='1' \
		--env DB_BOOKS_COMMANDS_URL='host.docker.internal' \
		--env DB_BOOKS_COMMANDS_PORT='3306' \
		--env DB_BOOKS_COMMANDS_USER=${DB_BOOKS_COMMANDS_USER} \
		--env DB_BOOKS_COMMANDS_PASS=${DB_BOOKS_COMMANDS_PASS} \
		--env DB_BOOKS_COMMANDS_DATABASE=${DB_BOOKS_COMMANDS_DATABASE} \
		--env DB_BOOKS_QUERIES_URL='host.docker.internal' \
		--env DB_BOOKS_QUERIES_PORT='27017' \
		--env DB_BOOKS_QUERIES_USER=${DB_BOOKS_QUERIES_USER} \
		--env DB_BOOKS_QUERIES_PASS=${DB_BOOKS_QUERIES_PASS} \
		--env DB_BOOKS_QUERIES_DATABASE=${DB_BOOKS_QUERIES_DATABASE} \
		--env DB_BOOKS_QUERIES_COLLECTION=${DB_BOOKS_QUERIES_COLLECTION} \
		--env SYNC_DATA_PERIOD_SECONDS=${SYNC_DATA_PERIOD_SECONDS} \
		soobinrho/17647-bookstore-cronjob-sync-data:latest

cleanup:
	# `-` is there to suppress any error in case there's no container running.
	-bash -c '{ docker ps -aq --filter "name=dev-bookstore-"; }' \
		| sort | uniq -u \
		| xargs docker stop | xargs docker rm

cleanup-including-db:
	-bash -c '{ docker ps -aq --filter "name=dev-bookstore-" && docker ps -aq --filter "name=dev-db-"; }' \
		| sort | uniq -u \
		| xargs docker stop | xargs docker rm

# =======================
# Tests for related books
# =======================
test-related-books-no-delay: ensure-env-file-exists cleanup cleanup-only-related-books
	docker run --detach --name dev-bookstore-related-books-no-delay \
		-p 8080:8080 \
		--add-host host.docker.internal:host-gateway \
		--env IS_DEV='1' \
		pmerson/book-recommendations-ms \
		--delay=0
	docker run --detach --name dev-bookstore-bff-desktop \
		-p 80:80 \
		--add-host host.docker.internal:host-gateway \
		--env IS_DEV='1' \
		soobinrho/17647-bookstore-bff-desktop:latest
	docker run --detach --name dev-bookstore-api-service-books-commands \
		-p 3000:3000 \
		--add-host host.docker.internal:host-gateway \
		--env IS_DEV='1' \
		--env DB_URL='host.docker.internal' \
		--env DB_PORT='3306' \
		--env DB_USER=${DB_BOOKS_COMMANDS_USER} \
		--env DB_PASS=${DB_BOOKS_COMMANDS_PASS} \
		--env DB_DATABASE=${DB_BOOKS_COMMANDS_DATABASE} \
		--env GEMINI_API_KEY=${GEMINI_API_KEY} \
		soobinrho/17647-bookstore-api-service-books-commands:latest
	docker run --detach --name dev-bookstore-api-service-books-queries \
		-p 3001:3000 \
		--add-host host.docker.internal:host-gateway \
		--env IS_DEV='1' \
		--env DB_URL='host.docker.internal' \
		--env DB_PORT='27017' \
		--env DB_USER=${DB_BOOKS_QUERIES_USER} \
		--env DB_PASS=${DB_BOOKS_QUERIES_PASS} \
		--env DB_DATABASE=${DB_BOOKS_QUERIES_DATABASE} \
		--env DB_COLLECTION=${DB_BOOKS_QUERIES_COLLECTION} \
		--env API_RELATED_BOOKS_URL=${API_RELATED_BOOKS_URL_DEV} \
		--env DB_BOOKS_COMMANDS_URL='host.docker.internal' \
		--env DB_BOOKS_COMMANDS_PORT='3306' \
		--env DB_BOOKS_COMMANDS_USER=${DB_BOOKS_COMMANDS_USER} \
		--env DB_BOOKS_COMMANDS_PASS=${DB_BOOKS_COMMANDS_PASS} \
		--env DB_BOOKS_COMMANDS_DATABASE=${DB_BOOKS_COMMANDS_DATABASE} \
		soobinrho/17647-bookstore-api-service-books-queries:latest

test-related-books-delayed: ensure-env-file-exists cleanup cleanup-only-related-books
	docker run --detach --name dev-bookstore-related-books-delayed \
		-p 8080:8080 \
		--add-host host.docker.internal:host-gateway \
		--env IS_DEV='1' \
		pmerson/book-recommendations-ms \
		--delay=5000
	docker run --detach --name dev-bookstore-bff-desktop \
		-p 80:80 \
		--add-host host.docker.internal:host-gateway \
		--env IS_DEV='1' \
		soobinrho/17647-bookstore-bff-desktop:latest
	docker run --detach --name dev-bookstore-api-service-books-commands \
		-p 3000:3000 \
		--add-host host.docker.internal:host-gateway \
		--env IS_DEV='1' \
		--env DB_URL='host.docker.internal' \
		--env DB_PORT='3306' \
		--env DB_USER=${DB_BOOKS_COMMANDS_USER} \
		--env DB_PASS=${DB_BOOKS_COMMANDS_PASS} \
		--env DB_DATABASE=${DB_BOOKS_COMMANDS_DATABASE} \
		--env GEMINI_API_KEY=${GEMINI_API_KEY} \
		soobinrho/17647-bookstore-api-service-books-commands:latest
	docker run --detach --name dev-bookstore-api-service-books-queries \
		-p 3001:3000 \
		--add-host host.docker.internal:host-gateway \
		--env IS_DEV='1' \
		--env DB_URL='host.docker.internal' \
		--env DB_PORT='27017' \
		--env DB_USER=${DB_BOOKS_QUERIES_USER} \
		--env DB_PASS=${DB_BOOKS_QUERIES_PASS} \
		--env DB_DATABASE=${DB_BOOKS_QUERIES_DATABASE} \
		--env DB_COLLECTION=${DB_BOOKS_QUERIES_COLLECTION} \
		--env API_RELATED_BOOKS_URL=${API_RELATED_BOOKS_URL_DEV} \
		--env DB_BOOKS_COMMANDS_URL='host.docker.internal' \
		--env DB_BOOKS_COMMANDS_PORT='3306' \
		--env DB_BOOKS_COMMANDS_USER=${DB_BOOKS_COMMANDS_USER} \
		--env DB_BOOKS_COMMANDS_PASS=${DB_BOOKS_COMMANDS_PASS} \
		--env DB_BOOKS_COMMANDS_DATABASE=${DB_BOOKS_COMMANDS_DATABASE} \
		soobinrho/17647-bookstore-api-service-books-queries:latest

cleanup-only-related-books:
	-bash -c '{ docker ps -aq --filter "name=dev-bookstore-related-books"; }' \
		| sort | uniq -u \
		| xargs docker stop | xargs docker rm

# ==========================
# Deployment with Kubernetes
# ==========================
prod-deploy-k8s-bookstore: ensure-env-file-exists
	cd ./k8s/ && \
		kubectl delete namespace bookstore-ns && \
		kubectl apply -f bookstore-ns.yaml && \
		kubectl config set-context --current --namespace=bookstore-ns
	cd ./k8s/ && \
		./generate_dot_env_specific_to_each_service.sh && \
		kubectl create secret generic secrets-api-service-books-commands --from-env-file=./.env.api-service-books-commands && \
		kubectl create secret generic secrets-api-service-books-queries --from-env-file=./.env.api-service-books-queries && \
		kubectl create secret generic secrets-api-service-customers --from-env-file=./.env.api-service-customers && \
		kubectl create secret generic secrets-crm-service-customers --from-env-file=./.env.crm-service-customers && \
		kubectl create secret generic secrets-cronjob-sync-data --from-env-file=./.env.cronjob-sync-data
	cd ./k8s/ && \
		kubectl apply -f service-bookstore-api-service-books-commands.yaml && \
		kubectl apply -f service-bookstore-api-service-books-queries.yaml && \
		kubectl apply -f service-bookstore-api-service-customers.yaml && \
		kubectl apply -f service-bookstore-crm-service-customers.yaml && \
		echo '[INFO] Waiting for services to get registered before deployments...' && \
		echo '[INFO] This is so that the hostname and port of the services get populated as env variables properly.' && \
		sleep 5
	cd ./k8s/ && \
		kubectl apply -f lb-bookstore-bff-desktop.yaml && \
		kubectl apply -f lb-bookstore-bff-mobile.yaml
	cd ./k8s/ && \
		kubectl apply -f deploy-bookstore-api-service-books-commands.yaml && \
		kubectl apply -f deploy-bookstore-api-service-books-queries.yaml && \
		kubectl apply -f deploy-bookstore-api-service-customers.yaml && \
		kubectl apply -f deploy-bookstore-bff-desktop.yaml && \
		kubectl apply -f deploy-bookstore-bff-mobile.yaml && \
		kubectl apply -f deploy-bookstore-crm-service-customers.yaml && \
		kubectl apply -f cronjob-sync-data.yaml

# ====
# Misc
# ====
.SILENT: ensure-env-file-exists \
	test-create-db \
	test \
	cleanup \
	cleanup-including-db \
	test-related-books-no-delay \
	test-related-books-delayed \
	cleanup-only-related-books \
	prod-deploy-k8s-bookstore
