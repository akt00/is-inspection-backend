FROM python:3
WORKDIR /app
COPY . /app
RUN pip install Flask Flask-BasicAuth gunicorn opencv-python
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "flaskr:create_app()"]
