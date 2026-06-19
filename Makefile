.PHONY: up dev refresh-db

up:
	.venv/bin/python manage.py runserver & npm run dev && wait

dev:
	.venv/bin/python manage.py runserver & npm run dev && wait

refresh-db:
	rm -f db.sqlite3 && .venv/bin/python manage.py migrate