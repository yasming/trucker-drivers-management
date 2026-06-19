up:
	.venv/bin/python manage.py runserver & npm run dev && wait

down:
	lsof -ti:8000 | xargs kill -9 2>/dev/null || true
	lsof -ti:5173 | xargs kill -9 2>/dev/null || true

tests:
	.venv/bin/python manage.py test
