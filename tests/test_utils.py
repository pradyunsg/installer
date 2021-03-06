"""Tests for installer.utils
"""

import hashlib
import textwrap
from email.message import Message
from io import BytesIO

import pytest

from installer.utils import (
    WheelFilename,
    copyfileobj_with_hashing,
    parse_metadata_file,
    parse_wheel_filename,
)


class TestParseMetadata:
    def test_basics(self):
        result = parse_metadata_file(
            textwrap.dedent(
                """\
            Name: package
            Version: 1.0.0
            Multi-Use-Field: 1
            Multi-Use-Field: 2
            Multi-Use-Field: 3
            """
            )
        )
        assert isinstance(result, Message)
        assert result.get("Name") == "package"
        assert result.get("version") == "1.0.0"
        assert result.get_all("MULTI-USE-FIELD") == ["1", "2", "3"]


class TestParseWheelFilename:
    @pytest.mark.parametrize(
        "string, expected",
        [
            # Crafted package name w/ a "complex" version and build tag
            (
                "package-1!1.0+abc.7-753-py3-none-any.whl",
                WheelFilename("package", "1!1.0+abc.7", "753", "py3-none-any"),
            ),
            # Crafted package name w/ a "complex" version and no build tag
            (
                "package-1!1.0+abc.7-py3-none-any.whl",
                WheelFilename("package", "1!1.0+abc.7", None, "py3-none-any"),
            ),
            # Use real tensorflow wheel names
            (
                "tensorflow-2.3.0-cp38-cp38-macosx_10_11_x86_64.whl",
                WheelFilename(
                    "tensorflow", "2.3.0", None, "cp38-cp38-macosx_10_11_x86_64"
                ),
            ),
            (
                "tensorflow-2.3.0-cp38-cp38-manylinux2010_x86_64.whl",
                WheelFilename(
                    "tensorflow", "2.3.0", None, "cp38-cp38-manylinux2010_x86_64"
                ),
            ),
            (
                "tensorflow-2.3.0-cp38-cp38-win_amd64.whl",
                WheelFilename("tensorflow", "2.3.0", None, "cp38-cp38-win_amd64"),
            ),
        ],
    )
    def test_valid_cases(self, string, expected):
        got = parse_wheel_filename(string)
        assert expected == got, (expected, got)

    @pytest.mark.parametrize(
        "string",
        [
            # Not ".whl"
            "pip-20.0.0-py2.py3-none-any.zip",
            # No tag
            "pip-20.0.0.whl",
            # Empty tag
            "pip-20.0.0---.whl",
        ],
    )
    def test_invalid_cases(self, string):
        with pytest.raises(ValueError):
            parse_wheel_filename(string)


class TestCopyFileObjWithHashing(object):
    def test_basic_functionality(self):
        data = b"input data is this"
        hash_ = hashlib.sha256(data).hexdigest()
        size = len(data)

        with BytesIO(data) as source:
            with BytesIO() as dest:
                result = copyfileobj_with_hashing(source, dest, hash_algorithm="sha256")
                written_data = dest.getvalue()

        assert result == (hash_, size)
        assert written_data == data
