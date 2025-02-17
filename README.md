# is-inspection-backend
curl -X POST -H "Content-Type: multipart/form-data" -u admin:admin -F "image_png=@image.png;type=image/png" -F "image_tiff=@image.tiff;type=image/tiff" -F "metadata=@image.json;type=application/json" 127.0.0.1:5000/api/v1/upload

curl -X POST -H "Content-Type: multipart/form-data" -u admin:admin -F "image=@image.tiff;type=image/tiff" 127.0.0.1:5000/api/v1/inference

gunicorn --bind 0.0.0.0:8080 'flaskr:create_app()'