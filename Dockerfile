FROM python:3.10

ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY requirements.txt /app/
RUN pip install -r requirements.txt

COPY . /app/
RUN python manage.py makemigrations
RUN python manage.py migrate
RUN python manage.py test
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]