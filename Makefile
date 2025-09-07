run:
	uvicorn app.main:app --host 0.0.0.0 --port 8000

docker-build:
	docker compose build

docker-up:
	docker compose up -d

docker-stop:
	docker compose down

docker-logs:
	docker compose logs -f

clean:
	find . -type d -name "__pycache__" -exec rm -r {} +;
	rm -rf .mypy_cache .pytest_cache

# Raspberry Pi deployment settings
PI_USER        		= jpraetor
PI_HOST        		= 192.168.0.25
PI_REMOTE_PATH	= /home/jpraetor/projects/recipes-app/

## Copy the local recipes.db to the Raspberry Pi
copy-db:
	scp recipes.db $(PI_USER)@$(PI_HOST):$(PI_REMOTE_PATH)
	@echo "✅ Copied recipes.db to $(PI_USER)@$(PI_HOST):$(PI_REMOTE_PATH)"

## Copy the local .env file to the Raspberry Pi
copy-env:
	scp .env $(PI_USER)@$(PI_HOST):$(PI_REMOTE_PATH)
	@echo "✅ Copied .env to $(PI_USER)@$(PI_HOST):$(PI_REMOTE_PATH)"

## Update code on Raspberry Pi and rebuild/restart Docker
pi-update:
	ssh $(PI_USER)@$(PI_HOST) 'set -e; cd $(PI_REMOTE_PATH) && git pull --rebase && docker compose up -d --build'
	@echo "✅ Pulled latest code and restarted containers on $(PI_HOST)"

## Same as pi-update, but when already on the Pi
pi-update-local:
	set -e; git pull --rebase && docker compose up -d --build
	@echo "✅ Pulled latest code and restarted containers locally"
