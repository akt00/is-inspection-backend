select_all_request = "select * from request"

insert_request_and_get_id = "INSERT INTO request (client_ip) VALUES (%s) RETURNING id;"

insert_inference = """
INSERT INTO inference (model, inference_time, prediction) VALUES (%s, %s, %s);
"""

insert_image = """
INSERT INTO image (storage_path, bit_depth, height, width, annotation, request_id, inference_id)
VALUES (%s, %s, %s, %s, %s, %s, %s);
"""
