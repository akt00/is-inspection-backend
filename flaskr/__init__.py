import io
import json

import cv2
from flask import Flask, request, make_response, jsonify, abort
import numpy as np

from auth import requires_auth


def create_app():
    app = Flask(__name__)
    # 1GB
    MAX_FILE_SIZE = 1024 * 1024 * 1024

    @app.route("/", methods=["GET"])
    def index():
        return "Hello, World!"

    @requires_auth
    @app.route("/api/v1/inference", methods=["POST"])
    def inference():
        if "image" not in request.files:
            abort(400, description="No 'image' file part in the request.")

        file = request.files["image"]

        if file.filename == "":
            abort(400, description="No selected file.")

        if not file.filename.lower().endswith((".tiff", ".tif")):
            abort(
                400,
                description=f"Uploaded file is not a TIFF image (filename extension). {file.filename}",
            )

        if file.content_type != "image/tiff":
            abort(
                400,
                description=f"Uploaded file is not a TIFF image (Content-Type mismatch). {file.content_type}",
            )

        file_content = file.read()

        if len(file_content) > MAX_FILE_SIZE:
            abort(413, description="File too large.")

        try:
            image_stream = io.BytesIO(file_content)
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
            "image_png" not in request.files
            or "image_tiff" not in request.files
            or "metadata" not in request.files
        ):
            abort(
                400,
                description=f"Files missing. Those must be present. {request.files}",
            )

        png_file = request.files["image_png"]

        if png_file.filename == "":
            abort(400, description="No selected file.")

        if not png_file.filename.lower().endswith((".png")):
            abort(
                400,
                description=f"Uploaded file is not a PNG image (filename extension). {png_file.filename}",
            )

        if png_file.content_type != "image/png":
            abort(
                400,
                description=f"Uploaded file is not a PNG image (Content-Type mismatch). {png_file.content_type}",
            )

        png_data = png_file.read()

        if len(png_data) > MAX_FILE_SIZE:
            abort(413, description="File too large.")

        tiff_file = request.files["image_tiff"]

        if tiff_file.filename == "":
            abort(400, description="No selected file.")

        if not tiff_file.filename.lower().endswith((".tif", ".tiff")):
            abort(
                400,
                description=f"Uploaded file is not a TIFF image (filename extension). {tiff_file.filename}",
            )

        if tiff_file.content_type != "image/tiff":
            abort(
                400,
                description=f"Uploaded file is not a TIFF image (Content-Type mismatch). {tiff_file.content_type}",
            )

        tiff_data = tiff_file.read()

        if len(tiff_data) > MAX_FILE_SIZE:
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
            png_stream = io.BytesIO(png_data)
            image_array = np.frombuffer(png_stream.read(), np.uint8)
            png_img = cv2.imdecode(image_array, cv2.IMREAD_UNCHANGED)
            tiff_stream = io.BytesIO(tiff_data)
            image_array = np.frombuffer(tiff_stream.read(), np.uint16)
            tiff_img = cv2.imdecode(image_array, cv2.IMREAD_UNCHANGED)
            json_data = json.load(json_file)

            print(png_img.shape)
            print(tiff_img.shape)
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
