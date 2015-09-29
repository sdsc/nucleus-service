db:
	cd nucleus_service; python manage.py syncdb

start:
	cd nucleus_service; python manage.py runserver

migrate:
	cd nucleus_service; manage.py makemigrations

view:
	open http://127.0.0.1:8000/docs
