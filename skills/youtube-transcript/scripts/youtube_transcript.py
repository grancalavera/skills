"""Fetch a verbatim YouTube transcript and basic metadata as JSON.

Zero external dependencies — uses only Python stdlib (urllib, json, re, xml.etree, html).
Uses YouTube's InnerTube API to fetch captions URLs and video metadata.

This script ALWAYS prints a JSON object to stdout:
- On success: { "video_id", "title", "channel", "published_date", "language", "is_english", "transcript" }
- On failure: { "error": "<description>" }

Exit codes:
- 0: success (JSON with transcript)
- 1: failure (JSON with error)
"""

import html as html_module
import json
import re
import sys
import traceback
import urllib.request
import xml.etree.ElementTree as ET
from http.cookiejar import CookieJar

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)

INNERTUBE_CONTEXT = {"client": {"clientName": "ANDROID", "clientVersion": "20.10.38"}}


def _error_exit(message: str) -> None:
    """Print a JSON error to stdout and exit with code 1."""
    print(json.dumps({"error": message}), flush=True)
    sys.exit(1)


def extract_video_id(url: str) -> str:
    """Extract video ID from various YouTube URL formats."""
    patterns = [
        r"(?:youtu\.be/)([a-zA-Z0-9_-]{11})",
        r"(?:youtube\.com/watch\?.*v=)([a-zA-Z0-9_-]{11})",
        r"(?:youtube\.com/embed/)([a-zA-Z0-9_-]{11})",
        r"(?:youtube\.com/v/)([a-zA-Z0-9_-]{11})",
        r"(?:youtube\.com/shorts/)([a-zA-Z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    raise ValueError(f"Could not extract video ID from URL: {url}")


def _build_opener() -> urllib.request.OpenerDirector:
    """Build a URL opener with cookie support."""
    cookie_jar = CookieJar()
    return urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(cookie_jar)
    )


def _fetch_url(opener: urllib.request.OpenerDirector, url: str) -> str:
    """Fetch a URL and return its body as a string."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with opener.open(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def _fetch_watch_page(opener: urllib.request.OpenerDirector, video_id: str) -> str:
    """Fetch the YouTube watch page HTML."""
    url = f"https://www.youtube.com/watch?v={video_id}"
    html = _fetch_url(opener, url)

    # Handle EU consent page
    if 'action="https://consent.youtube.com/s"' in html:
        html = _fetch_url(opener, url + "&has_verified=1")

    return html


def _extract_innertube_api_key(html: str, video_id: str) -> str:
    """Extract the InnerTube API key from the watch page HTML."""
    match = re.search(r'"INNERTUBE_API_KEY":\s*"([a-zA-Z0-9_-]+)"', html)
    if match:
        return match.group(1)

    if 'class="g-recaptcha"' in html:
        raise RuntimeError("YouTube is blocking requests from this IP address (CAPTCHA required).")

    raise RuntimeError("Could not extract InnerTube API key from YouTube page.")


def _extract_metadata_from_html(html: str) -> dict:
    """Extract video metadata from the watch page HTML.

    The InnerTube Android client response lacks microformat data,
    so we extract metadata from ytInitialPlayerResponse in the HTML.
    """
    title = ""
    channel = ""
    published_date = ""

    match = re.search(r'var\s+ytInitialPlayerResponse\s*=\s*(\{.+?\})\s*;', html)
    if match:
        try:
            pr = json.loads(match.group(1))
            vd = pr.get("videoDetails", {})
            mf = pr.get("microformat", {}).get("playerMicroformatRenderer", {})

            title = vd.get("title", "") or mf.get("title", {}).get("simpleText", "")
            channel = vd.get("author", "") or mf.get("ownerChannelName", "")
            published_date = mf.get("publishDate", "") or mf.get("uploadDate", "")
            if published_date and "T" in published_date:
                published_date = published_date.split("T")[0]
        except (json.JSONDecodeError, KeyError):
            pass

    return {"title": title, "channel": channel, "published_date": published_date}


def _fetch_innertube_player(
    opener: urllib.request.OpenerDirector, video_id: str, api_key: str
) -> dict:
    """Call the InnerTube player API to get video data including captions."""
    url = f"https://www.youtube.com/youtubei/v1/player?key={api_key}"
    payload = json.dumps({
        "context": INNERTUBE_CONTEXT,
        "videoId": video_id,
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "User-Agent": USER_AGENT,
            "Content-Type": "application/json",
        },
    )
    with opener.open(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _get_caption_tracks(player_data: dict, video_id: str) -> list[dict]:
    """Extract caption tracks from InnerTube player response."""
    playability = player_data.get("playabilityStatus", {})
    status = playability.get("status")

    if status and status != "OK":
        reason = playability.get("reason", "Unknown reason")
        raise RuntimeError(f"Video '{video_id}' is not available: {reason}")

    captions = player_data.get("captions", {}).get(
        "playerCaptionsTracklistRenderer", {}
    )
    tracks = captions.get("captionTracks")

    if not tracks:
        raise RuntimeError(
            f"No captions available for video '{video_id}'. "
            "The video may not have subtitles, or subtitles may be disabled."
        )

    return tracks


def _select_caption_track(tracks: list[dict]) -> tuple[dict, str, bool]:
    """Select the best caption track.

    Priority:
    1. Manually uploaded English transcript
    2. Auto-generated English transcript
    3. Whatever is first available
    """
    manual_en = [
        t for t in tracks
        if t.get("languageCode", "").startswith("en")
        and t.get("kind") != "asr"
    ]
    if manual_en:
        return manual_en[0], "en", True

    auto_en = [
        t for t in tracks
        if t.get("languageCode", "").startswith("en")
        and t.get("kind") == "asr"
    ]
    if auto_en:
        return auto_en[0], "en", True

    # Fallback to first available
    track = tracks[0]
    lang = track.get("languageCode", "unknown")
    return track, lang, False


def _fetch_transcript_xml(
    opener: urllib.request.OpenerDirector, track: dict
) -> list[dict]:
    """Fetch and parse the transcript XML from a caption track URL."""
    base_url = track["baseUrl"]
    xml_text = _fetch_url(opener, base_url)

    if not xml_text.strip():
        raise RuntimeError("Transcript response was empty.")

    root = ET.fromstring(xml_text)

    entries = []

    # Format 1: simple <text start="..." dur="...">content</text>
    text_elems = list(root.iter("text"))
    if text_elems:
        for elem in text_elems:
            start = float(elem.get("start", 0))
            text = elem.text or ""
            text = html_module.unescape(text)
            entries.append({"start": start, "text": text})
        return entries

    # Format 2: <body> containing <p t="ms" d="ms"> with <s> word segments
    for p_elem in root.iter("p"):
        t_ms = p_elem.get("t")
        if t_ms is None:
            continue
        start = int(t_ms) / 1000.0

        # Collect text from <s> children, or direct text
        s_elems = list(p_elem.iter("s"))
        if s_elems:
            words = []
            for s in s_elems:
                text = s.text or ""
                words.append(text)
            line = "".join(words).strip()
        else:
            line = (p_elem.text or "").strip()

        if line:
            entries.append({"start": start, "text": html_module.unescape(line)})

    return entries


def format_timestamp(seconds: float) -> str:
    """Format seconds into M:SS or H:MM:SS."""
    total = int(seconds)
    h, remainder = divmod(total, 3600)
    m, s = divmod(remainder, 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def format_transcript(entries: list[dict]) -> str:
    """Format transcript entries into timestamped text."""
    lines = []
    for entry in entries:
        ts = format_timestamp(entry["start"])
        lines.append(f"{ts}\n\n{entry['text']}")
    return "\n\n".join(lines)


def main() -> None:
    if len(sys.argv) != 2:
        _error_exit(
            "Usage: python3 scripts/youtube_transcript.py <youtube_url>. "
            "Exactly one argument (a YouTube video URL) is required."
        )

    # Strip backslash escapes that shells sometimes add (e.g. \? \=)
    url = sys.argv[1].replace("\\", "")

    try:
        video_id = extract_video_id(url)
    except ValueError as e:
        _error_exit(str(e))

    opener = _build_opener()

    try:
        html = _fetch_watch_page(opener, video_id)
    except Exception as e:
        _error_exit(f"Failed to access YouTube for video '{video_id}': {e}")

    try:
        api_key = _extract_innertube_api_key(html, video_id)
    except Exception as e:
        _error_exit(str(e))

    try:
        player_data = _fetch_innertube_player(opener, video_id, api_key)
    except Exception as e:
        _error_exit(f"Failed to fetch video data for '{video_id}': {e}")

    try:
        tracks = _get_caption_tracks(player_data, video_id)
    except Exception as e:
        _error_exit(str(e))

    track, language, is_english = _select_caption_track(tracks)

    try:
        entries = _fetch_transcript_xml(opener, track)
    except Exception as e:
        _error_exit(f"Failed to fetch transcript for video '{video_id}': {e}")

    if not entries:
        _error_exit(
            f"Transcript for video '{video_id}' is empty. "
            "The video may have captions disabled or the captions contain no text."
        )

    metadata = _extract_metadata_from_html(html)

    result = {
        "video_id": video_id,
        "title": metadata["title"],
        "channel": metadata["channel"],
        "published_date": metadata["published_date"],
        "language": language,
        "is_english": is_english,
        "transcript": format_transcript(entries),
    }

    print(json.dumps(result, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        _error_exit(f"Unexpected error: {traceback.format_exc()}")
