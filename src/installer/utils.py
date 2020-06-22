"""Utilities related to handling / interacting with wheel files."""

from email.parser import FeedParser

from installer._compat.typing import TYPE_CHECKING

if TYPE_CHECKING:
    from email.message import Message
    from installer._compat.typing import Text


def parse_metadata_file(contents):
    # type: (Text) -> Message
    """Parse :pep:`376` ``PKG-INFO``-style metadata files.

    ``METADATA`` and ``WHEEL`` files in a wheel, use the same syntax (as per :pep:`427`)
    and can also be parsed using this function.

    :param contents: The entire contents of the file.
    """
    feed_parser = FeedParser()
    feed_parser.feed(contents)
    return feed_parser.close()
