up-backend:
	cd backend && .venv/bin/python manage.py runserver
up-frontend:
	cd frontend && npm run serve