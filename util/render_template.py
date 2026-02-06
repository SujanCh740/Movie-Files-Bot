#Thanks @DeletedFromEarth for helping in this journey 

import jinja2
from info import *
from lazybot import LazyPrincessBot
from util.human_readable import humanbytes
from util.file_properties import get_file_ids
from server.exceptions import InvalidHash
import urllib.parse
import logging
import aiohttp
import mimetypes


async def render_page(id, secure_hash, src=None):
    file = await LazyPrincessBot.get_messages(int(LOG_CHANNEL), int(id))
    file_data = await get_file_ids(LazyPrincessBot, int(LOG_CHANNEL), int(id))
    if file_data.unique_id[:6] != secure_hash:
        logging.debug(f"link hash: {secure_hash} - {file_data.unique_id[:6]}")
        logging.debug(f"Invalid hash for message with - ID {id}")
        raise InvalidHash

    src = urllib.parse.urljoin(
        URL,
        f"{id}/{urllib.parse.quote_plus(file_data.file_name)}?hash={secure_hash}",
    )

    mime_type = (file_data.mime_type or "").strip()
    file_name_for_mime = file_data.file_name or ""
    guessed_mime = mimetypes.guess_type(file_name_for_mime)[0]

    # Improve compatibility for common stream formats where Telegram mime can be empty/generic
    if not mime_type or mime_type == "application/octet-stream":
        mime_type = guessed_mime or "application/octet-stream"

    # Explicit normalization for requested formats
    lower_name = file_name_for_mime.lower()
    if lower_name.endswith(".mkv"):
        mime_type = "video/x-matroska"
    elif lower_name.endswith(".mp4"):
        mime_type = "video/mp4"
    tag = mime_type.split("/")[0].strip()
    file_size = humanbytes(file_data.file_size)
    if tag in ["video", "audio"]:
        template_file = "template/req.html"
    else:
        template_file = "template/dl.html"
        async with aiohttp.ClientSession() as s:
            async with s.get(src) as u:
                file_size = humanbytes(int(u.headers.get("Content-Length")))

    with open(template_file) as f:
        template = jinja2.Template(f.read())

    file_name = file_data.file_name.replace("_", " ")

    return template.render(
        file_name=file_name,
        file_url=src,
        file_size=file_size,
        file_unique_id=file_data.unique_id,
        mime_type=mime_type,
        media_tag=tag,
    )
