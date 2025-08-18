
clean:
	find . -type d -name "__pycache__" -exec rm -r {} +;
	rm -rf .mypy_cache .pytest_cache
