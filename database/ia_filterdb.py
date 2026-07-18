import logging
from struct import pack
import re
import base64
from pyrogram.file_id import FileId
from pymongo.errors import DuplicateKeyError
from umongo import Instance, Document, fields
from motor.motor_asyncio import AsyncIOMotorClient
from marshmallow.exceptions import ValidationError
from info import DATABASE_URI, DATABASE_NAME, COLLECTION_NAME, USE_CAPTION_FILTER, MAX_B_TN
from utils import get_settings, save_group_settings

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


client = AsyncIOMotorClient(DATABASE_URI)
db = client[DATABASE_NAME]
instance = Instance.from_db(db)

@instance.register
class Media(Document):
    file_id = fields.StrField(attribute='_id')
    file_ref = fields.StrField(allow_none=True)
    file_name = fields.StrField(required=True)
    file_size = fields.IntField(required=True)
    file_type = fields.StrField(allow_none=True)
    mime_type = fields.StrField(allow_none=True)
    caption = fields.StrField(allow_none=True)

    class Meta:
        indexes = ('$file_name', )
        collection_name = COLLECTION_NAME


async def save_file(media):
    """Save file in database"""

    # TODO: Find better way to get same file_id for same media to avoid duplicates
    file_id, file_ref = unpack_new_file_id(media.file_id)
    file_name = re.sub(r"(_|\-|\.|\+)", " ", str(media.file_name))
    try:
        file = Media(
            file_id=file_id,
            file_ref=file_ref,
            file_name=file_name,
            file_size=media.file_size,
            file_type=media.file_type,
            mime_type=media.mime_type,
            caption=media.caption.html if media.caption else None,
        )
    except ValidationError:
        logger.exception('Error occurred while saving file in database')
        return False, 2
    else:
        try:
            await file.commit()
        except DuplicateKeyError:      
            logger.warning(
                f'{getattr(media, "file_name", "NO_FILE")} is already saved in database'
            )

            return False, 0
        else:
            logger.info(f'{getattr(media, "file_name", "NO_FILE")} is saved to database')
            return True, 1



STOP_WORDS = {"the", "a", "an", "and", "or", "of", "to", "in", "for", "with", "by", "at", "on"}
CONSONANTS = set("bcdgjkptz")

def normalize_query(query: str) -> str:
    query = query.lower()
    query = re.sub(r"[^a-zA-Z0-9\s]", " ", query)
    query = re.sub(r"\s+", " ", query).strip()
    return query

def word_to_regex(word: str) -> str:
    if len(word) < 3:
        return re.escape(word)
    
    chars_regex = []
    for c in word:
        escaped = re.escape(c)
        if c in CONSONANTS:
            chars_regex.append(escaped + r'[h]?')
        elif c == 's':
            chars_regex.append(escaped + r'[h]?')
        elif c == 'h':
            chars_regex.append(escaped)
        else:
            chars_regex.append(escaped)
            
    return r'[\s\.\+\-_]*'.join(chars_regex)

def _make_filter(query: str, file_type=None):
    query = query.lower()

    # Clean request keywords/noise
    query = re.sub(
        r"\b(pl(i|e)*?(s|z+|ease|se|ese|(e+)s(e)?)|((send|snd|giv(e)?|gib)(\sme)?)|movie(s)?|new|latest|bro|bruh|broh|helo|that|find|dubbed|link|venum|iruka|pannunga|pannungga|anuppunga|anupunga|anuppungga|anupungga|film(s)?|undo|kitti|kitty|tharu|kittumo|kittum|any(one)|with\ssubtitle(s)?|download)\b",
        "",
        query,
        flags=re.IGNORECASE
    )
    removes = {"in", "upload", "series", "full", "horror", "thriller", "mystery", "print", "file"}
    words = query.split()
    words = [w for w in words if w not in removes]
    query = " ".join(words)

    # Parse season before cleaning the query
    season_match = re.search(
        r'\b(?:season\s*0?(\d+)|s\s*0?(\d+))(?:\s*(?:episode|ep|e)\s*0?\d+)?\b',
        query,
        re.IGNORECASE
    )

    season_regex = None

    if season_match:
        season_num = int(season_match.group(1) or season_match.group(2))

        # Remove season/episode text from the query
        query = re.sub(
            r'\b(?:season\s*0?\d+|s\s*0?\d+)(?:\s*(?:episode|ep|e)\s*0?\d+)?\b',
            '',
            query,
            flags=re.IGNORECASE
        ).strip()

        season_regex = re.compile(
            rf'\b(?:season\s*0?{season_num}|s\s*0?{season_num})(?:\s*(?:episode|ep|e)\s*0?\d+)?\b',
            re.IGNORECASE
        )

    # Normalize remaining query
    query = re.sub(r"[^a-zA-Z0-9\s]", " ", query)
    query = re.sub(r"\s+", " ", query).strip()

    words = query.split(" ") if query else []
    if len(words) > 1 or (words and season_regex):
        words = [w for w in words if w not in STOP_WORDS]

    regexes = [re.compile(word_to_regex(w), re.IGNORECASE) for w in words if w]
    if season_regex:
        regexes.append(season_regex)

    if not regexes:
        filter_query = {'file_name': re.compile('.', re.IGNORECASE)}
    else:
        file_name_conds = [{'file_name': regex} for regex in regexes]
        if USE_CAPTION_FILTER:
            caption_conds = [{'caption': regex} for regex in regexes]
            filter_query = {
                '$or': [
                    {'$and': file_name_conds},
                    {'$and': caption_conds}
                ]
            }
        else:
            filter_query = {'$and': file_name_conds}

    if file_type:
        filter_query['file_type'] = file_type

    return filter_query

async def get_search_results(chat_id, query, file_type=None, max_results=10, offset=0, filter=False):
    """For given query return (results, next_offset)"""
    if chat_id is not None:
        settings = await get_settings(int(chat_id))
        try:
            if settings['max_btn']:
                max_results = 10
            else:
                max_results = int(MAX_B_TN)
        except KeyError:
            await save_group_settings(int(chat_id), 'max_btn', False)
            settings = await get_settings(int(chat_id))
            if settings['max_btn']:
                max_results = 10
            else:
                max_results = int(MAX_B_TN)
    
    filter_query = _make_filter(query, file_type)

    total_results = await Media.count_documents(filter_query)
    next_offset = offset + max_results

    if next_offset > total_results:
        next_offset = ''

    cursor = Media.find(filter_query)
    # Sort by recent
    cursor.sort('$natural', -1)
    # Slice files according to offset and max results
    cursor.skip(offset).limit(max_results)
    # Get list of files
    files = await cursor.to_list(length=max_results)

    return files, next_offset, total_results

async def get_bad_files(query, file_type=None, filter=False):
    """For given query return (results, next_offset)"""
    filter_query = _make_filter(query, file_type)

    total_results = await Media.count_documents(filter_query)

    cursor = Media.find(filter_query)
    # Sort by recent
    cursor.sort('$natural', -1)
    # Get list of files
    files = await cursor.to_list(length=total_results)

    return files, total_results

async def get_file_details(query):
    filter = {'file_id': query}
    cursor = Media.find(filter)
    filedetails = await cursor.to_list(length=1)
    return filedetails


def encode_file_id(s: bytes) -> str:
    r = b""
    n = 0

    for i in s + bytes([22]) + bytes([4]):
        if i == 0:
            n += 1
        else:
            if n:
                r += b"\x00" + bytes([n])
                n = 0

            r += bytes([i])

    return base64.urlsafe_b64encode(r).decode().rstrip("=")


def encode_file_ref(file_ref: bytes) -> str:
    return base64.urlsafe_b64encode(file_ref).decode().rstrip("=")


def unpack_new_file_id(new_file_id):
    """Return file_id, file_ref"""
    decoded = FileId.decode(new_file_id)
    file_id = encode_file_id(
        pack(
            "<iiqq",
            int(decoded.file_type),
            decoded.dc_id,
            decoded.media_id,
            decoded.access_hash
        )
    )
    file_ref = encode_file_ref(decoded.file_reference)
    return file_id, file_ref
