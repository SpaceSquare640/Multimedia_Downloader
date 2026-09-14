"""
Error classification for the engine.

Behaviour used to branch on substrings of exception messages, scattered across
modules: ``"403" in str(e)`` decided whether to retry, and a second, nested
check decided whether to warn about a stale downloader. That is fragile in a
way that fails silently -- yt-dlp rewording a message would not raise anything,
it would just quietly stop retrying, and the only symptom would be a lower
success rate nobody could trace.

Classifying in one place does not remove the string matching (an exception from
a third-party library is often only distinguishable by its text), but it does
put every such rule behind one tested function instead of scattering them, so
the fragile part is small, visible, and has tests pinned to it.

Deliberately stdlib-only and free of yt-dlp/ffmpeg imports: classification is
by exception *type* first and message second, so this module never needs to
know which library raised.
"""

from __future__ import annotations

from enum import Enum


class ErrorKind(str, Enum):
    """
    What kind of failure this is, in terms of what the caller should do.

    The point is the *decision*, not the taxonomy -- each member exists because
    some code branches on it. Resist adding members with no consumer; a value
    nothing reads is noise that still has to be kept correct.

    Subclasses ``str`` so it serialises as a plain string if it ever crosses
    the IPC boundary, without committing to that now.
    """

    #: Worth retrying as-is: a stale signature/token, a 5xx, a blip.
    TRANSIENT = "transient"

    #: Looked transient but survived every retry. For a 403 that almost always
    #: means the bundled downloader has fallen behind the site, so the useful
    #: advice is "update", not "try again".
    STALE_TOOL = "stale_tool"

    #: ffmpeg is not installed or not where we expected it.
    NO_FFMPEG = "no_ffmpeg"

    #: Not recognised. Never retried, never given specific advice.
    UNKNOWN = "unknown"


#: Substrings marking a failure worth retrying unchanged. These are matched
#: against third-party error text, so they are the fragile part of this module
#: -- which is exactly why they live here and nowhere else.
#:
#: Not included, deliberately: rate limits (429) and timeouts. Retrying a rate
#: limit after 2s tends to deepen the hole rather than help, and a timeout has
#: usually already cost the user a long wait. Both would need their own backoff
#: to be worth adding.
_TRANSIENT_MARKERS = ("403", "Forbidden", "HTTP Error 5")


def classify(exc: BaseException) -> ErrorKind:
    """
    Classify an exception by what the caller should do about it.

    Type is checked before message: ``FileNotFoundError`` from launching ffmpeg
    is unambiguous, and reading its text would only make the rule worse.
    """
    if isinstance(exc, FileNotFoundError):
        return ErrorKind.NO_FFMPEG

    message = str(exc)
    if any(marker in message for marker in _TRANSIENT_MARKERS):
        return ErrorKind.TRANSIENT

    return ErrorKind.UNKNOWN


def is_stale_tool(exc: BaseException) -> bool:
    """
    Whether a failure that has exhausted its retries points at an outdated
    bundled downloader rather than bad luck.

    Separate from :func:`classify` because it is not a property of the
    exception alone -- the same 403 is TRANSIENT on the first attempt and
    STALE_TOOL once retrying has failed to help. Only the retry loop knows
    which situation it is in.
    """
    return classify(exc) is ErrorKind.TRANSIENT and "403" in str(exc)
