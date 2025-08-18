run:
	uvicorn app.main:app --host 0.0.0.0 --port 8000

docker-build:
	docker-compose build

docker-up:
	docker-compose up --build

docker-stop:
	docker-compose down

docker-logs:
	docker-compose logs -f

clean:
	find . -type d -name "__pycache__" -exec rm -r {} +;
	rm -rf .mypy_cache .pytest_cache
