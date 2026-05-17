up:
	docker compose up --build -d

down:
	docker compose down

test:
	python -m pytest -q

lint:
	python -m ruff check .
