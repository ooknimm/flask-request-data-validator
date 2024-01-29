import io
from typing import Annotated, List, Optional

import pytest
from flask import Flask, jsonify
from werkzeug.datastructures import FileStorage, MultiDict

from flask_parameter_validator import File, parameter_validator
from tests.conftest import match_pydantic_error_url

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


@app.post("/files")
@parameter_validator
def post_files(
    files: List[FileStorage] = File(),
):
    file_contents = [file.stream.read().decode("utf-8") for file in files]
    result = {"files": file_contents}
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
        (
            "/file",
            {},
            422,
            {
                "detail": [
                    {
                        "type": "missing",
                        "loc": ["body", "file1"],
                        "msg": "Field required",
                        "input": None,
                        "url": match_pydantic_error_url("missing"),
                    }
                ]
            },
        ),
        (
            "/files",
            MultiDict(
                [
                    ("files", (io.BytesIO(b"foo"), "file1")),
                    ("files", (io.BytesIO(b"bar"), "file2")),
                ]
            ),
            200,
            {"files": ["foo", "bar"]},
        ),
        (
            "/files",
            MultiDict(
                [
                    ("files", (io.BytesIO(b"foo"), "file1")),
                ]
            ),
            200,
            {"files": ["foo"]},
        ),
        (
            "/files",
            {"files": (io.BytesIO(b"foo"), "file1")},
            200,
            {"files": ["foo"]},
        ),
        (
            "/files",
            {},
            422,
            {
                "detail": [
                    {
                        "type": "missing",
                        "loc": ["body", "files"],
                        "msg": "Field required",
                        "input": None,
                        "url": match_pydantic_error_url("missing"),
                    }
                ]
            },
        ),
    ],
)
def test_sned_file(path, files, expected_status, expected_response):
    response = client.post(path, data=files, content_type="multipart/form-data")
    assert response.status_code == expected_status
    assert response.json == expected_response
