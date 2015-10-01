db:
	cd nucleus_service; python manage.py syncdb

start: migrate
	cd nucleus_service; python manage.py runserver

migrate:
	cd nucleus_service; python manage.py migrate

view:
	open http://127.0.0.1:8000/docs

version:
	python -c "import django; print(django.get_version())"
