FROM python:3.10

# Define build arguments for the database credentials
ARG DB_NAME
ARG DB_USER
ARG DB_PASSWORD
ARG DB_HOST

ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY requirements.txt /app/
RUN pip install -r requirements.txt

COPY . /app/

# Set the environment variables for the database credentials
ENV DB_NAME=$DB_NAME
ENV DB_USER=$DB_USER
ENV DB_PASSWORD=$DB_PASSWORD
ENV DB_HOST=$DB_HOST

# Run migrations and tests during build time
RUN python manage.py makemigrations
RUN python manage.py migrate
RUN python manage.py test

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]