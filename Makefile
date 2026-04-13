#!make
include .env
export
GIT_HASH := $(shell git rev-parse --short HEAD)

all:	build push

ensure-env-file-exists:
	test -s ./.env || { echo '[ERROR] .env file not found.'; exit 1; }

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
	cd ./crm-service-customers/ && \
		docker build -t soobinrho/17647-bookstore-crm-service-customers:latest \
		-t soobinrho/17647-bookstore-crm-service-customers:$(GIT_HASH) .

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
	cd ./crm-service-customers/ && \
		docker push soobinrho/17647-bookstore-crm-service-customers:latest && \
 		docker push soobinrho/17647-bookstore-crm-service-customers:$(GIT_HASH)

# =====
# Tests
# =====
test-desktop-books: ensure-env-file-exists
	docker run --detach --name dev-bookstore-bff-desktop \
		-p 80:80 \
		--add-host host.docker.internal:host-gateway \
		--env API_SERVICES_LOAD_BALANCER_URL='http://host.docker.internal:3000' \
		soobinrho/17647-bookstore-bff-desktop:latest
	docker run --detach --name dev-bookstore-api-service-books \
		-p 3000:3000 \
		--add-host host.docker.internal:host-gateway \
		--env IS_DEV='1' \
		--env DB_URL='host.docker.internal:3306' \
		--env DB_USER=${DB_BOOKS_USER} \
		--env DB_PASS=${DB_BOOKS_PASS} \
		--env DB_DATABASE=${DB_BOOKS_DATABASE} \
		--env GEMINI_API_KEY=${GEMINI_API_KEY} \
		soobinrho/17647-bookstore-api-service-books:latest
	docker ps
	echo '[INFO] Port 80: dev-bookstore-bff-desktop'
	echo '[INFO] Port 3000: dev-bookstore-api-service-books'

test-desktop-customers: ensure-env-file-exists
	docker run --detach --name dev-bookstore-bff-desktop \
		-p 80:80 \
		--add-host host.docker.internal:host-gateway \
		--env API_SERVICES_LOAD_BALANCER_URL='http://host.docker.internal:3000' \
		soobinrho/17647-bookstore-bff-desktop:latest
	docker run --detach --name dev-bookstore-api-service-customers \
		-p 3000:3000 \
		--add-host host.docker.internal:host-gateway \
		--env IS_DEV='1' \
		--env DB_URL='host.docker.internal:3307' \
		--env DB_USER=${DB_CUSTOMERS_USER} \
		--env DB_PASS=${DB_CUSTOMERS_PASS} \
		--env DB_DATABASE=${DB_CUSTOMERS_DATABASE} \
		--env KAFKA_TOPIC=${KAFKA_TOPIC} \
		--env KAFKA_BROKER_0_URL=${KAFKA_BROKER_0_URL} \
		--env KAFKA_BROKER_1_URL=${KAFKA_BROKER_0_URL} \
		--env KAFKA_BROKER_2_URL=${KAFKA_BROKER_0_URL} \
		soobinrho/17647-bookstore-api-service-customers:latest
	docker run --detach --name dev-bookstore-crm-service-customers \
		--env KAFKA_TOPIC=${KAFKA_TOPIC} \
		--env KAFKA_BROKER_0_URL=${KAFKA_BROKER_0_URL} \
		--env KAFKA_BROKER_1_URL=${KAFKA_BROKER_0_URL} \
		--env KAFKA_BROKER_2_URL=${KAFKA_BROKER_0_URL} \
		--env SMTP_SERVER_URL=${SMTP_SERVER_URL} \
		--env SMTP_SERVER_PORT=${SMTP_SERVER_PORT} \
		--env SMTP_SERVER_ID=${SMTP_SERVER_ID} \
		--env SMTP_SERVER_PASS=${SMTP_SERVER_PASS} \
		soobinrho/17647-bookstore-crm-service-customers:latest
	docker ps
	echo '[INFO] Port 80: dev-bookstore-bff-desktop'
	echo '[INFO] Port 3000: dev-bookstore-api-service-customers'
	echo '[INFO] Port N/A: dev-bookstore-crm-service-customers'

test-mobile-books: ensure-env-file-exists
	docker run --detach --name dev-bookstore-bff-mobile \
		-p 80:80 \
		--add-host host.docker.internal:host-gateway \
		--env API_SERVICES_LOAD_BALANCER_URL='http://host.docker.internal:3000' \
		soobinrho/17647-bookstore-bff-mobile:latest
	docker run --detach --name dev-bookstore-api-service-books \
		-p 3000:3000 \
		--add-host host.docker.internal:host-gateway \
		--env IS_DEV='1' \
		--env DB_URL='host.docker.internal:3306' \
		--env DB_USER=${DB_BOOKS_USER} \
		--env DB_PASS=${DB_BOOKS_PASS} \
		--env DB_DATABASE=${DB_BOOKS_DATABASE} \
		--env GEMINI_API_KEY=${GEMINI_API_KEY} \
		soobinrho/17647-bookstore-api-service-books:latest
	docker ps
	echo '[INFO] Port 80: dev-bookstore-bff-mobile'
	echo '[INFO] Port 3000: dev-bookstore-api-service-books'

test-mobile-customers: ensure-env-file-exists
	docker run --detach --name dev-bookstore-bff-mobile \
		-p 80:80 \
		--add-host host.docker.internal:host-gateway \
		--env API_SERVICES_LOAD_BALANCER_URL='http://host.docker.internal:3000' \
		soobinrho/17647-bookstore-bff-mobile:latest
	docker run --detach --name dev-bookstore-api-service-customers \
		-p 3000:3000 \
		--add-host host.docker.internal:host-gateway \
		--env IS_DEV='1' \
		--env DB_URL='host.docker.internal:3307' \
		--env DB_USER=${DB_CUSTOMERS_USER} \
		--env DB_PASS=${DB_CUSTOMERS_PASS} \
		--env DB_DATABASE=${DB_CUSTOMERS_DATABASE} \
		--env KAFKA_TOPIC=${KAFKA_TOPIC} \
		--env KAFKA_BROKER_0_URL=${KAFKA_BROKER_0_URL} \
		--env KAFKA_BROKER_1_URL=${KAFKA_BROKER_0_URL} \
		--env KAFKA_BROKER_2_URL=${KAFKA_BROKER_0_URL} \
		soobinrho/17647-bookstore-api-service-customers:latest
	docker run --detach --name dev-bookstore-crm-service-customers \
		--env KAFKA_TOPIC=${KAFKA_TOPIC} \
		--env KAFKA_BROKER_0_URL=${KAFKA_BROKER_0_URL} \
		--env KAFKA_BROKER_1_URL=${KAFKA_BROKER_0_URL} \
		--env KAFKA_BROKER_2_URL=${KAFKA_BROKER_0_URL} \
		--env SMTP_SERVER_URL=${SMTP_SERVER_URL} \
		--env SMTP_SERVER_PORT=${SMTP_SERVER_PORT} \
		--env SMTP_SERVER_ID=${SMTP_SERVER_ID} \
		--env SMTP_SERVER_PASS=${SMTP_SERVER_PASS} \
		soobinrho/17647-bookstore-crm-service-customers:latest
	docker ps
	echo '[INFO] Port 80: dev-bookstore-bff-mobile'
	echo '[INFO] Port 3000: dev-bookstore-api-service-customers'
	echo '[INFO] Port N/A: dev-bookstore-crm-service-customers'

test-create-db: ensure-env-file-exists
	docker run --detach --name dev-db-books \
		-p 3306:3306 \
		--add-host host.docker.internal:host-gateway \
		--env MARIADB_RANDOM_ROOT_PASSWORD='True' \
		--env MARIADB_USER=${DB_BOOKS_USER} \
		--env MARIADB_PASSWORD=${DB_BOOKS_PASS} \
		--env MARIADB_DATABASE=${DB_BOOKS_DATABASE} \
		mariadb:latest
	docker run --detach --name dev-db-customers \
		-p 3307:3306 \
		--add-host host.docker.internal:host-gateway \
		--env MARIADB_RANDOM_ROOT_PASSWORD='True' \
		--env MARIADB_USER=${DB_CUSTOMERS_USER} \
		--env MARIADB_PASSWORD=${DB_CUSTOMERS_PASS} \
		--env MARIADB_DATABASE=${DB_CUSTOMERS_DATABASE} \
		mariadb:latest

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
		pmerson/book-recommendations-ms \
		--delay=0
	echo '[INFO] Port 8080: dev-bookstore-related-books-no-delay'
	docker run --detach --name dev-bookstore-bff-desktop \
		-p 80:80 \
		--add-host host.docker.internal:host-gateway \
		--env IS_DEV='1' \
		--env API_SERVICES_LOAD_BALANCER_URL='http://host.docker.internal:3000' \
		soobinrho/17647-bookstore-bff-desktop:latest
	docker run --detach --name dev-bookstore-api-service-books \
		-p 3000:3000 \
		--add-host host.docker.internal:host-gateway \
		--env IS_DEV='1' \
		--env DB_URL='host.docker.internal:3306' \
		--env DB_USER=${DB_BOOKS_USER} \
		--env DB_PASS=${DB_BOOKS_PASS} \
		--env DB_DATABASE=${DB_BOOKS_DATABASE} \
		--env GEMINI_API_KEY=${GEMINI_API_KEY} \
		--env API_RELATED_BOOKS_URL=${API_RELATED_BOOKS_URL_DEV} \
		soobinrho/17647-bookstore-api-service-books:latest
	docker ps
	echo '[INFO] Port 80: dev-bookstore-bff-desktop'
	echo '[INFO] Port 3000: dev-bookstore-api-service-books'

test-related-books-delayed: ensure-env-file-exists cleanup cleanup-only-related-books
	docker run --detach --name dev-bookstore-related-books-delayed \
		-p 8080:8080 \
		--add-host host.docker.internal:host-gateway \
		pmerson/book-recommendations-ms \
		--delay=5000
	echo '[INFO] Port 8080: dev-bookstore-related-books-delayed'
	docker run --detach --name dev-bookstore-bff-desktop \
		-p 80:80 \
		--add-host host.docker.internal:host-gateway \
		--env IS_DEV='1' \
		--env API_SERVICES_LOAD_BALANCER_URL='http://host.docker.internal:3000' \
		soobinrho/17647-bookstore-bff-desktop:latest
	docker run --detach --name dev-bookstore-api-service-books \
		-p 3000:3000 \
		--add-host host.docker.internal:host-gateway \
		--env IS_DEV='1' \
		--env DB_URL='host.docker.internal:3306' \
		--env DB_USER=${DB_BOOKS_USER} \
		--env DB_PASS=${DB_BOOKS_PASS} \
		--env DB_DATABASE=${DB_BOOKS_DATABASE} \
		--env GEMINI_API_KEY=${GEMINI_API_KEY} \
		--env API_RELATED_BOOKS_URL=${API_RELATED_BOOKS_URL_DEV} \
		soobinrho/17647-bookstore-api-service-books:latest
	docker ps
	echo '[INFO] Port 80: dev-bookstore-bff-desktop'
	echo '[INFO] Port 3000: dev-bookstore-api-service-books'

cleanup-only-related-books:
	-bash -c '{ docker ps -aq --filter "name=dev-bookstore-related-books"; }' \
		| sort | uniq -u \
		| xargs docker stop | xargs docker rm

# =============================
# Deployment without Kubernetes
# =============================
prod-deploy-ec2-bookstore-a: ensure-env-file-exists
	docker pull soobinrho/17647-bookstore-bff-desktop:latest
	docker run --detach --name bookstore-bff-desktop \
		-p 80:80 \
		--env API_SERVICES_LOAD_BALANCER_URL=${API_SERVICES_LOAD_BALANCER_URL} \
		soobinrho/17647-bookstore-bff-desktop:latest
	docker pull soobinrho/17647-bookstore-api-service-customers:latest
	docker run --detach --name bookstore-api-service-customers \
		-p 3000:3000 \
		--env DB_URL=${DB_URL} \
		--env DB_USER=${DB_CUSTOMERS_USER} \
		--env DB_PASS=${DB_CUSTOMERS_PASS} \
		--env DB_DATABASE=${DB_CUSTOMERS_DATABASE} \
		--env KAFKA_TOPIC=${KAFKA_TOPIC} \
		--env KAFKA_BROKER_0_URL=${KAFKA_BROKER_0_URL} \
		--env KAFKA_BROKER_1_URL=${KAFKA_BROKER_0_URL} \
		--env KAFKA_BROKER_2_URL=${KAFKA_BROKER_0_URL} \
		soobinrho/17647-bookstore-api-service-customers:latest

prod-deploy-ec2-bookstore-b: ensure-env-file-exists
	docker pull soobinrho/17647-bookstore-bff-desktop:latest
	docker run --detach --name bookstore-bff-desktop \
		-p 80:80 \
		--env API_SERVICES_LOAD_BALANCER_URL=${API_SERVICES_LOAD_BALANCER_URL} \
		soobinrho/17647-bookstore-bff-desktop:latest
	docker pull soobinrho/17647-bookstore-api-service-books:latest
	docker run --detach --name bookstore-api-service-books \
		-p 3000:3000 \
		--env DB_URL=${DB_URL} \
		--env DB_USER=${DB_BOOKS_USER} \
		--env DB_PASS=${DB_BOOKS_PASS} \
		--env DB_DATABASE=${DB_BOOKS_DATABASE} \
		--env GEMINI_API_KEY=${GEMINI_API_KEY} \
		soobinrho/17647-bookstore-api-service-books:latest

prod-deploy-ec2-bookstore-c: ensure-env-file-exists
	docker pull soobinrho/17647-bookstore-bff-mobile:latest
	docker run --detach --name bookstore-bff-mobile \
		-p 80:80 \
		--env API_SERVICES_LOAD_BALANCER_URL=${API_SERVICES_LOAD_BALANCER_URL} \
		soobinrho/17647-bookstore-bff-mobile:latest
	docker pull soobinrho/17647-bookstore-api-service-books:latest
	docker run --detach --name bookstore-api-service-books \
		-p 3000:3000 \
		--env DB_URL=${DB_URL} \
		--env DB_USER=${DB_BOOKS_USER} \
		--env DB_PASS=${DB_BOOKS_PASS} \
		--env DB_DATABASE=${DB_BOOKS_DATABASE} \
		--env GEMINI_API_KEY=${GEMINI_API_KEY} \
		soobinrho/17647-bookstore-api-service-books:latest

prod-deploy-ec2-bookstore-d: ensure-env-file-exists
	docker pull soobinrho/17647-bookstore-bff-mobile:latest
	docker run --detach --name bookstore-bff-mobile \
		-p 80:80 \
		--env API_SERVICES_LOAD_BALANCER_URL=${API_SERVICES_LOAD_BALANCER_URL} \
		soobinrho/17647-bookstore-bff-mobile:latest
	docker pull soobinrho/17647-bookstore-api-service-customers:latest
	docker run --detach --name bookstore-api-service-customers \
		-p 3000:3000 \
		--env DB_URL=${DB_URL} \
		--env DB_USER=${DB_CUSTOMERS_USER} \
		--env DB_PASS=${DB_CUSTOMERS_PASS} \
		--env DB_DATABASE=${DB_CUSTOMERS_DATABASE} \
		--env KAFKA_TOPIC=${KAFKA_TOPIC} \
		--env KAFKA_BROKER_0_URL=${KAFKA_BROKER_0_URL} \
		--env KAFKA_BROKER_1_URL=${KAFKA_BROKER_0_URL} \
		--env KAFKA_BROKER_2_URL=${KAFKA_BROKER_0_URL} \
		soobinrho/17647-bookstore-api-service-customers:latest

prod-cleanup:
	docker ps --filter 'name=bookstore-' -aq | xargs docker stop | xargs docker rm

# ==========================
# Deployment with Kubernetes
# ==========================
prod-deploy-k8s-bookstore: ensure-env-file-exists
	cd ./k8s/ && \
	  kubectl create secret generic prod-secrets --from-env-file=../.env
	cd ./k8s/ && \
		kubectl apply -f bookstore-ns.yaml
	cd ./k8s/ && \
		kubectl apply -f service-bookstore-api-service-books.yaml && \
		kubectl apply -f service-bookstore-api-service-customers.yaml && \
		kubectl apply -f service-bookstore-crm-service-customers.yaml
	cd ./k8s/ && \
		kubectl apply -f lb-bookstore-bff-desktop.yaml && \
		kubectl apply -f lb-bookstore-bff-mobile.yaml
	cd ./k8s/ && \
		kubectl apply -f deploy-bookstore-api-service-books.yaml && \
		kubectl apply -f deploy-bookstore-api-service-customers.yaml && \
		kubectl apply -f deploy-bookstore-bff-desktop.yaml && \
		kubectl apply -f deploy-bookstore-bff-mobile.yaml && \
		kubectl apply -f deploy-bookstore-crm-service-customers.yaml


# ====
# Misc
# ====
.SILENT: ensure-env-file-exists \
  prod-deploy-ec2-bookstore-a \
	prod-deploy-ec2-bookstore-b \
	prod-deploy-ec2-bookstore-c \
	prod-deploy-ec2-bookstore-d \
	test-desktop-books \
	test-desktop-customers \
	test-mobile-books \
	test-mobile-customers \
	test-create-db \
	cleanup \
	cleanup-including-db \
	test-related-books-no-delay \
	test-related-books-delayed \
	cleanup-only-related-books \
	prod-deploy-k8s-bookstore
