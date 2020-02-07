.PHONY: format help

# Help system from https://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
.DEFAULT_GOAL := help

help:
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Build the required containers
	cp Docker/Dockerfile-* .
	docker build -t xmrauctions -f Dockerfile-xmrauctions .
	rm -f Dockerfile-*

up: ## Run dev service containers
	cp Docker/docker-compose.yaml .
	docker-compose up -d
	rm -f docker-compose.yaml

down: ## Stop dev service containers
	cp Docker/docker-compose.yaml .
	docker-compose down
	rm -f docker-compose.yaml

dev: ## Start development web service
	./manage.py runserver

shell: ## Enter Django shell
	./manage.py shell

clean:
	rm -f *compose.yaml Dockerfile*

logs:
	cp Docker/docker-compose.yaml .
	docker-compose logs -f
	rm -f docker-compose.yaml

### Deploy

deploy-up: ## Run the containers
	cp Docker/docker-compose* .
	docker-compose -f docker-compose.yaml -f docker-compose.deploy.yaml up -d
	rm -f docker-compose*

deploy-down: ## Stop the containers
	cp Docker/docker-compose* .
	docker-compose -f docker-compose.yaml -f docker-compose.deploy.yaml down
	rm -f docker-compose*

deploy-ps: ## Show the containers
	cp Docker/docker-compose* .
	docker-compose -f docker-compose.yaml -f docker-compose.deploy.yaml ps
	rm -f docker-compose*

deploy-logs: ## Show container logs
	cp Docker/docker-compose* .
	docker-compose -f docker-compose.yaml -f docker-compose.deploy.yaml logs -f
	rm -f docker-compose*

deploy-static: ## Collect static
	docker run --rm --env-file=.env xmrauctions ./manage.py collectstatic --no-input

deploy-migrations: ## Run migrations
	docker run --rm --env-file=.env --net=xmrauctions_default xmrauctions ./manage.py migrate

deploy-manage: ## Run management commands
	@docker run --rm -it --env-file=.env --net=xmrauctions_default xmrauctions ./manage.py $(CMD)

deploy-createadmin: ## Create admin user in Django backend
	docker run --rm -it --env-file=.env --net=xmrauctions_default xmrauctions ./manage.py createsuperuser
