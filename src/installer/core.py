"""Core wheel installation logic."""

import posixpath
from io import BytesIO

from installer._compat.typing import TYPE_CHECKING, cast
from installer.destinations import WheelDestination
from installer.exceptions import InvalidWheelSource
from installer.records import Record
from installer.sources import WheelSource
from installer.utils import SCHEME_NAMES, parse_metadata_file

if TYPE_CHECKING:
    from typing import Dict

    from installer._compat.typing import Binary, FSPath
    from installer.utils import Scheme


__all__ = ["install"]


def _process_WHEEL_file(source):
    # type: (WheelSource) -> Scheme
    """Process the WHEEL file, from ``source``.

    Returns the scheme that the archive root should go in.
    """
    stream = source.read_dist_info(u"WHEEL")
    metadata = parse_metadata_file(stream)

    # Ensure compatibility with this wheel version.
    if metadata["Wheel-Version"] != "1.0":
        raise InvalidWheelSource(
            source,
            "Incompatible Wheel-Version: only support version 1.0",
        )

    # Determine where archive root should go.
    if metadata["Root-Is-Purelib"]:
        return cast("Scheme", "purelib")
    else:
        return cast("Scheme", "platlib")


def _determine_scheme(path, source, root_scheme):
    # type: (FSPath, WheelSource, Scheme) -> Scheme
    """Determine which scheme to place given path in, from source."""
    data_dir = source.data_dir

    # If it's in not `{distribution}-{version}.data`, then it's in root_scheme.
    if posixpath.commonprefix([data_dir, path]) != data_dir:
        return root_scheme

    # Figure out which scheme this goes to.
    left, right = posixpath.split(path)
    while left != data_dir:
        left, right = posixpath.split(left)

    scheme_name = right
    if scheme_name not in SCHEME_NAMES:
        msg_fmt = u"{path} is not contained in a valid .data subdirectory."
        raise InvalidWheelSource(source, msg_fmt.format(path=path))

    return cast("Scheme", scheme_name)


def install(source, destination, additional_metadata):
    # type: (WheelSource, WheelDestination, Dict[str, Binary]) -> None
    """Install wheel described by ``source`` into ``destination``.

    :param source: wheel to install.
    :param destination: where to write the wheel.

    """
    root_scheme = _process_WHEEL_file(source)

    # RECORD handling
    record_file_path = "/".join([source.dist_info_dir, "RECORD"])
    written_records = []

    # Write all the files from the wheel.
    for record_elements, stream in source.get_contents():
        source_record = Record.from_elements(*record_elements)
        path = source_record.path
        # Skip the RECORD, which is written at the end, based on this info.
        if path == record_file_path:
            continue
        scheme = _determine_scheme(
            path=path,
            source=source,
            root_scheme=root_scheme,
        )
        record = destination.write_file(
            scheme=scheme,
            path=path,
            stream=stream,
        )
        written_records.append(record)

    # Write all the installation-specific metadata
    for filename, contents in additional_metadata.items():
        path = posixpath.join(source.dist_info_dir, filename)

        with BytesIO(contents) as other_stream:
            record = destination.write_file(
                scheme=root_scheme,
                path=path,
                stream=other_stream,
            )
        written_records.append(record)

    destination.finalize_installation(scheme=root_scheme, records=written_records)
