.PHONY: format help

# Help system from https://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
.DEFAULT_GOAL := help

help:
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Build all the required containers
	docker build -t monero -f Dockerfile-monero .
	docker build -t xmrauctions -f Dockerfile-xmrauctions .



### Stage

stage-up: ## Run the stage containers
	docker-compose -f docker-compose.yaml -f docker-compose.stage.yaml up -d

stage-ps: ## Show containers
	docker-compose -f docker-compose.yaml -f docker-compose.stage.yaml ps

stage-logs: ## Show logs
	docker-compose -f docker-compose.yaml -f docker-compose.stage.yaml logs -f

stage-static: ## Collect static
	docker run --rm --env-file=.env xmrauctions ./manage.py collectstatic --no-input
