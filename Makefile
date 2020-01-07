.PHONY: format help

# Help system from https://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
.DEFAULT_GOAL := help

help:
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Build the required containers
	docker build -t xmrauctions -f Dockerfile-xmrauctions .

up: ## Run dev service containers
	docker-compose up -d

dev: ## Start development web service
	./manage.py runserver

shell: ## Enter Django shell
	./manage.py shell

createsuperuser: ## Create admin user in Django backend
	docker run --rm -it --env-file=.env --net=xmrauctions_default xmrauctions ./manage.py createsuperuser

### Deploy

deploy-up: ## Run the containers
	docker-compose -f docker-compose.yaml -f docker-compose.deploy.yaml up -d

deploy-down: ## Stop the containers
	docker-compose -f docker-compose.yaml -f docker-compose.deploy.yaml down

deploy-ps: ## Show the containers
	docker-compose -f docker-compose.yaml -f docker-compose.deploy.yaml ps

deploy-logs: ## Show container logs
	docker-compose -f docker-compose.yaml -f docker-compose.deploy.yaml logs -f

deploy-static: ## Collect static
	docker run --rm --env-file=.env xmrauctions ./manage.py collectstatic --no-input

deploy-migrations: ## Run migrations
	docker run --rm --env-file=.env --net=xmrauctions_default xmrauctions ./manage.py migrate
