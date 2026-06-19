up-backend:
	cd backend && .venv/bin/python manage.py runserver
up-frontend:
	cd frontend && npm run dev

refresh-db:
	cd backend && rm -f db.sqlite3 && .venv/bin/python manage.py migrate