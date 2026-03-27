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
