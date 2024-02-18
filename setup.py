from pathlib import Path
from typing import Generator

from setuptools import setup


def get_install_requires() -> Generator[str, None, None]:
    current_folder = Path(__file__).resolve().parent
    with open(current_folder / "requirements" / "requirements.txt", "r") as f:
        for line in f:
            if line.startswith("#"):
                continue
            yield line.strip()


setup(
    name="flask_request_data_validator",
    version="0.0.1",
    description="Flask request data vaildation like fastapi",
    long_description="Flask request data vaildation like fastapi",
    url="https://github.com/ooknimm/flask-request-data-validator.git",
    author="minkoo.kim",
    author_email="ooknimm@gmail.com",
    license="MIT",
    keywords="flask request data validator",
    packages=["flask_request_data_validator"],
    install_requires=list(get_install_requires()),
    classifiers=[
        "Framework :: Flask",
        "Framework :: Pydantic :: 2",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
