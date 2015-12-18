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

worker-fe1-debug:
	cd nucleus_service; celery -A nucleus -l debug -c 2 -B -Q comet-fe1 worker

worker-fe1:
	cd nucleus_service; celery -A nucleus --detach -c 2 -B -Q comet-fe1 worker

worker-update-debug:
	cd nucleus_service; celery -A nucleus -l debug -Q update worker

worker-update:
	cd nucleus_service; celery -A nucleus --detach -Q update worker

worker-result:
	cd nucleus_service; celery -A nucleus -c 2 -B -l debug -Q result worker
