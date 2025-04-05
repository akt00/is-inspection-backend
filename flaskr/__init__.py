import io
import logging
import json
import os

import cv2
from flask import Flask, request, make_response, jsonify, abort
import numpy as np
import psycopg2 as pg

if __name__ == "__main__":
    from auth import requires_auth
else:
    from .auth import requires_auth


def create_app():
    app = Flask(__name__)
    conn = pg.connect(
        "dbname=test user=postgres password=postgres host=10.93.80.3 port=5432"
    )
    logging.info("DB connection success")
    assert conn is not None
    # 1GB
    MAX_FILE_SIZE = 1024 * 1024 * 1024

    @app.route("/", methods=["GET"])
    def index():
        text = ""
        with open("/mnt/my-volume/default.tfstate") as f:
            while line := f.readline():
                text += line

        with open("/mnt/my-volume/sample-logfile.txt", "a") as f:
            f.write("DB connection success!\n")

        logging.info("DB request received")
        print("DB request received")
        cur = None  # Initialize cur to None
        try:
            cur = conn.cursor()
            cur.execute("select * from request")
            # Be careful calling fetchone() twice like this.
            # The first call gets a row, the second will likely get None
            # unless you expected multiple rows.
            logging.info(f"Fetched row 1: {cur.fetchone()}")
            # print(f'Fetched row 2: {cur.fetchone()}') # This will likely print None

            logging.info("Executing insert...")
            cur.execute("insert into request (client_ip) values ('10.1.1.2')")

            # --- THIS IS THE MISSING STEP ---
            conn.commit()
            # --------------------------------

            logging.info("DB operation success (committed)")
            print("db operation success (committed)")
            return (
                text
                + "Request logged successfully!"  # Flask routes need to return something
            )

        except Exception as e:
            logging.error(f"Database error: {e}")
            print(f"Database error: {e}")
            if conn:
                conn.rollback()  # Roll back changes if something went wrong
            return "Internal Server Error", 500  # Return an error response

        finally:
            if cur:
                cur.close()
                logging.info("Cursor closed")
                print("Cursor closed")
        # Note: Closing the main connection 'conn' here would prevent subsequent requests
        # from using it. Managing connection scope is important (see below).

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
        finally:
            pass

        return make_response(jsonify({"predictions": [1, 2, 3]}), 200)

    @requires_auth
    @app.route("/api/v1/upload", methods=["POST"])
    def upload():
        if (
            "image8" not in request.files
            or "image16" not in request.files
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
            stream8 = io.BytesIO(data8)
            image_array = np.frombuffer(stream8.read(), np.uint8)
            image8 = cv2.imdecode(image_array, cv2.IMREAD_UNCHANGED)
            stream16 = io.BytesIO(data16)
            image_array = np.frombuffer(stream16.read(), np.uint16)
            image16 = cv2.imdecode(image_array, cv2.IMREAD_UNCHANGED)
            json_data = json.load(json_file)

            print(image8.shape)
            print(image16.shape)
            print(json_data)
            # cv2.imwrite("cat-png.png", png_img)
            # cv2.imwrite("cat-tiff.tiff", tiff_img.astype(np.uint8))
        except (IOError, OSError) as e:
            abort(400, description=f"Error opening or processing TIFF image: {e}")
        except Exception as e:
            abort(500, description=f"An unexpected error occurred: {e}")
        finally:
            pass

        return make_response(jsonify({"message": "success!"}), 200)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
