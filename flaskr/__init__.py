import io
import json
import logging
import os
from pathlib import Path
import uuid

import cv2
from flask import Flask, request, make_response, jsonify, abort
import google.cloud.logging
from google.cloud.logging_v2.handlers import CloudLoggingHandler
from jsonschema import validate, ValidationError
import numpy as np
import psycopg2 as pg2

if __name__ == "__main__":
    from auth import requires_auth
    from queries import (
        select_all_request,
        insert_request_and_get_id,
        insert_inference,
        insert_image,
    )
    from schemas import prediction_schema, annotation_schema
else:
    from .auth import requires_auth
    from .queries import (
        select_all_request,
        insert_request_and_get_id,
        insert_inference,
        insert_image,
    )
    from .schemas import prediction_schema, annotation_schema


def create_app():
    DB_HOST = (
        os.getenv("DB_HOST") if os.getenv("DB_HOST") is not None else "10.93.80.10"
    )
    DB_PORT = os.getenv("DB_PORT") if os.getenv("DB_PORT") is not None else "5432"
    DB_NAME = os.getenv("DB_NAME") if os.getenv("DB_NAME") is not None else "test"
    DB_USER = os.getenv("DB_USER") if os.getenv("DB_USER") is not None else "postgres"
    DB_PASSWD = (
        os.getenv("DB_PASSWD") if os.getenv("DB_PASSWD") is not None else "postgres"
    )

    """
    GCS_PATH_EMBEDDINGS = (
        os.getenv("GCS_PATH_8BIT")
        if os.getenv("GCS_PATH_8BIT") is not None
        else "cis-seizo-embeddings"
    )
    GCS_PATH_16BIT = (
        os.getenv("GCS_PATH_16BIT")
        if os.getenv("GCS_PATH_16BIT") is not None
        else "cis-seizo-16bit"
    )
    """
    GCS_PATH_8BIT = (
        os.getenv("GCS_PATH_8BIT")
        if os.getenv("GCS_PATH_8BIT") is not None
        else "cis-seizo-8bit"
    )
    # app
    app = Flask(__name__)
    # 1GB
    MAX_FILE_SIZE = 1024 * 1024 * 1024
    # logger
    logging_client = google.cloud.logging.Client()
    handler = CloudLoggingHandler(logging_client)
    logger = logging.getLogger("cloudLogger")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    # returns db connector
    def get_db_connector():
        try:
            connector = pg2.connect(
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWD,
                host=DB_HOST,
                port=DB_PORT,
                sslmode="require",
            )

            return connector

        except Exception as e:
            logger.error(f"Failed to create DB connection pool: {e}")

    @app.route("/", methods=["GET"])
    def index():
        text = ""
        path = Path("/gcs") / "default"

        with open(os.path.join(path / "logfile"), "a") as f:
            f.write("Cloud storage write success!\n")
            logger.info("Cloud storage write success!")

        with open(path / "logfile", "r") as f:
            while line := f.readline():
                text += line

        client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)

        try:
            with get_db_connector() as conn:
                with conn.cursor() as cur:
                    cur = conn.cursor()
                    cur.execute(select_all_request)
                    logger.info(f"Fetched row 1: {cur.fetchone()}")
                    logger.info("Executing insert...")
                    cur.execute(insert_request_and_get_id, (client_ip,))
                    request_id = cur.fetchone()[0]
                    logger.info(f"Returned ID: {request_id} Client IP: {client_ip}")

                logger.info("DB operation success (committed)")

            return text + "\nRequest logged successfully!"

        except Exception as e:
            logger.error(f"Database error: {e}")
            return "Internal Server Error", 500

    @requires_auth
    @app.route("/api/v1/inference", methods=["POST"])
    def inference():
        if "image" not in request.files:
            abort(400, description="No 'image' file part in the request.")

        file = request.files["image"]

        if file.filename == "":
            abort(400, description="No selected file.")

        if not file.filename.lower().endswith((".tiff", ".tif", "png")):
            abort(
                400,
                description=f"Uploaded file is not an image (filename extension). {file.filename}",
            )

        if file.content_type != "image/tiff" and file.content_type != "image/png":
            abort(
                400,
                description=f"Uploaded file is not an image (Content-Type mismatch). {file.content_type}",
            )

        file_content = file.read()

        if len(file_content) > MAX_FILE_SIZE:
            abort(413, description="File too large.")

        try:
            image_stream = io.BytesIO(file_content)

            try:
                image_array = np.frombuffer(image_stream.read(), np.uint8)
            except Exception:
                image_array = np.frombuffer(image_stream.read(), np.uint16)

            img = cv2.imdecode(image_array, cv2.IMREAD_UNCHANGED)

            width, height, _ = img.shape
            print(width, height)
            # cv2.imwrite("cat.tiff", img.astype(np.uint8))
        except (IOError, OSError) as e:
            abort(400, description=f"Error opening or processing TIFF image: {e}")
        except Exception as e:
            abort(500, description=f"An unexpected error occurred: {e}")

        return make_response(jsonify({"predictions": [1, 2, 3]}), 200)

    @requires_auth
    @app.route("/api/v1/upload", methods=["POST"])
    def upload():
        if (
            "image8" not in request.files
            # or "image16" not in request.files
            or "metadata" not in request.files
        ):
            abort(
                400,
                description=f"Files missing. Those must be present. {request.files}",
            )

        file8 = request.files["image8"]

        if file8.filename == "":
            abort(400, description="No selected file.")

        if not file8.filename.lower().endswith((".tif", ".tiff", ".png")):
            abort(
                400,
                description=f"Uploaded file is not an image (filename extension). {file8.filename}",
            )

        if file8.content_type != "image/tiff" and file8.content_type != "image/png":
            abort(
                400,
                description=f"Uploaded file is not an image (Content-Type mismatch). {file8.content_type}",
            )

        data8 = file8.read()
        if len(data8) > MAX_FILE_SIZE:
            abort(413, description="File too large.")

        """
        file16 = request.files["image16"]

        if file16.filename == "":
            abort(400, description="No selected file.")

        if not file16.filename.lower().endswith((".tif", ".tiff", "png")):
            abort(
                400,
                description=f"Uploaded file is not an image (filename extension). {file16.filename}",
            )

        if file16.content_type != "image/tiff" and file16.content_type != "image/png":
            abort(
                400,
                description=f"Uploaded file is not an image (Content-Type mismatch). {file16.content_type}",
            )

        data16 = file16.read()

        if len(data16) > MAX_FILE_SIZE:
            abort(413, description="File too large.")
        """

        json_file = request.files["metadata"]

        if json_file.filename == "":
            abort(400, description="No selected file.")

        if not json_file.filename.lower().endswith((".json")):
            abort(
                400,
                description=f"Uploaded file is not a JSON (filename extension). {json_file.filename}",
            )

        if json_file.content_type != "application/json":
            abort(
                400,
                description=f"Uploaded file is not a JSON (Content-Type mismatch). {json_file.content_type}",
            )

        try:
            image_array = np.frombuffer(data8, np.uint8)
            image8 = cv2.imdecode(image_array, cv2.IMREAD_UNCHANGED)
            """
            image_array = np.frombuffer(data16, np.uint16)
            image16 = cv2.imdecode(image_array, cv2.IMREAD_UNCHANGED)
            """
            json_data = json.load(json_file)
            logger.info(f"image shape: {image8.shape} data: {json_data}")
            # schema validation
            validate(instance=json_data, schema=annotation_schema)

            unique_id = uuid.uuid1()
            filename = str(unique_id) + ".png"
            """
            path_16bit = Path("/gcs") / GCS_PATH_16BIT / filename
            h16, w16, _ = image16.shape
            """
            path_8bit = Path("/gcs") / GCS_PATH_8BIT / filename
            h8, w8, _ = image8.shape

            # cv2.imwrite(path_16bit, image16.astype(np.uint16))
            cv2.imwrite(path_8bit, image8.astype(np.uint8))
            # transaction
            client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)

            with get_db_connector() as conn:
                with conn.cursor() as cur:
                    cur = conn.cursor()
                    cur.execute(insert_request_and_get_id, (client_ip,))
                    request_id = cur.fetchone()[0]
                    """
                    storage_path16 = "gs://" + GCS_PATH_16BIT + "/" + filename
                    cur.execute(
                        insert_image,
                        (
                            storage_path16,
                            16,
                            h16,
                            w16,
                            json.dumps(json_data),
                            request_id,
                            None,
                        ),
                    )
                    """
                    storage_path8 = "gs://" + GCS_PATH_8BIT + "/" + filename
                    cur.execute(
                        insert_image,
                        (
                            storage_path8,
                            8,
                            h8,
                            w8,
                            json.dumps(json_data),
                            request_id,
                            None,
                        ),
                    )
                logger.info("Upload success (committed)")

        except (IOError, OSError) as e:
            logger.error(f"Error opening or processing TIFF image: {e}")
            abort(400, description=f"Error opening or processing TIFF image: {e}")
        except ValidationError as e:
            logger.error(f"The JSON data does not conform to the schema: {e}")
            abort(400, f"The JSON data does not conform to the schema: {e}")
        except Exception as e:
            logger.error(f"Error: {e}")
            return "Internal Server Error", 500

        return make_response(jsonify({"message": "success!"}), 200)

    return app


"""
curl -u admin:admin -X POST https://mock-api-525898554966.us-central1.run.app/api/v1/inference \
  -F "image=@image8.png;type=image/png"
"""

"""
curl -u admin:admin -X POST https://mock-api-525898554966.us-central1.run.app/api/v1/upload \
  -F "image8=@image8.png;type=image/png" \
  -F "image16=@image16.png;type=image/png" \
  -F "metadata=@image.json;type=application/json"
"""
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
