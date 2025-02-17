FROM python:3
WORKDIR /app
COPY . /app
# Install system dependencies for OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/* # Clean up to reduce image size
# ... (rest of your Dockerfile)
RUN pip install Flask Flask-BasicAuth gunicorn opencv-python
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "flaskr:create_app()"]
