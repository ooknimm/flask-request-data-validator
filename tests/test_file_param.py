import io
from typing import Annotated, Optional

import pytest
from flask import Flask, jsonify
from werkzeug.datastructures import FileStorage

from flask_parameter_validator import File, parameter_validator

app = Flask(__name__)
client = app.test_client()


@app.post("/file")
@parameter_validator
def post_file(
    file1: Annotated[FileStorage, File()],
    file2: Annotated[Optional[FileStorage], File()] = None,
):
    file1_content = file1.stream.read().decode("utf-8")
    result = {"file1": file1_content}
    if file2:
        file2_content = file2.stream.read().decode("utf-8")
        result.update({"file2": file2_content})
    return jsonify(result)


@pytest.mark.parametrize(
    "path,files,expected_status,expected_response",
    [
        (
            "/file",
            {
                "file1": (io.BytesIO(b"foo"), "file1"),
                "file2": (io.BytesIO(b"bar"), "file2"),
            },
            200,
            {"file1": "foo", "file2": "bar"},
        ),
        ("/file", {"file1": (io.BytesIO(b"foo"), "file1")}, 200, {"file1": "foo"}),
    ],
)
def test_sned_file(path, files, expected_status, expected_response):
    response = client.post(path, data=files, content_type="multipart/form-data")
    assert response.status_code == expected_status
    assert response.json == expected_response
