# is-inspection-backend
curl -X POST -H "Content-Type: multipart/form-data" -u admin:admin -F "image8=@image8.png;type=image/png" -F "image16=@image16.png;type=image/png" -F "metadata=@image.json;type=application/json" https://mock-api-525898554966.us-central1.run.app/api/v1/upload

curl -X POST -H "Content-Type: multipart/form-data" -u admin:admin -F "image=@image8.png;type=image/png" https://mock-api-525898554966.us-central1.run.app/api/v1/inference

gunicorn --bind 0.0.0.0:8080 'flaskr:create_app()'
.