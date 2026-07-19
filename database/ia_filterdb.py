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
    import re

    query = query.strip()
    season = None
    episode = None

    # Combined patterns: S01E08 / S01 E08 / Season 1 Episode 8
    combined = re.search(
        r'\b(?:s|season)\s*(\d{1,2})\s*(?:e|ep|episode)\s*(\d{1,3})\b',
        query, re.IGNORECASE
    )
    if combined:
        season = int(combined.group(1))
        episode = int(combined.group(2))
        # strip the S/E token from query
        query = re.sub(
            r'\b(?:s|season)\s*\d{1,2}\s*(?:e|ep|episode)\s*\d{1,3}\b',
            '', query, flags=re.IGNORECASE
        )
    else:
        # Season only: S01 / Season 1
        season_match = re.search(r'\b(?:s|season)\s*(\d{1,2})\b', query, re.IGNORECASE)
        if season_match:
            season = int(season_match.group(1))
            query = re.sub(r'\b(?:s|season)\s*\d{1,2}\b', '', query, flags=re.IGNORECASE)

        # Episode only: E08 / Ep 8 / Episode 8
        episode_match = re.search(r'\b(?:e|ep|episode)\s*(\d{1,3})\b', query, re.IGNORECASE)
        if episode_match:
            episode = int(episode_match.group(1))
            query = re.sub(r'\b(?:e|ep|episode)\s*\d{1,3}\b', '', query, flags=re.IGNORECASE)

    # Normalize remaining query
    query = re.sub(r'\s+', ' ', query).strip()

    # Build regex conditions for the remaining title words
    file_name_conds = []
    caption_conds = []
    if query:
        for word in query.split():
            safe = re.escape(word)
            file_name_conds.append({'file_name': {'$regex': safe, '$options': 'i'}})
            caption_conds.append({'caption': {'$regex': safe, '$options': 'i'}})

    # Season / Episode regex — must match BOTH when both given
    se_patterns = []
    if season is not None and episode is not None:
        s, e = f'{season:02d}', f'{episode:02d}'
        # matches S01E08, S01 E08, S1E8, Season 1 Episode 8, 1x08
        se_patterns.append(
            rf'(?:s(?:eason)?\s*0*{season}\s*[\s._-]*e(?:p|pisode)?\s*0*{episode}\b'
            rf'|\b0*{season}x0*{episode}\b)'
        )
    elif season is not None:
        se_patterns.append(rf'\bs(?:eason)?\s*0*{season}\b')
    elif episode is not None:
        se_patterns.append(rf'\be(?:p|pisode)?\s*0*{episode}\b')

    for pat in se_patterns:
        file_name_conds.append({'file_name': {'$regex': pat, '$options': 'i'}})
        caption_conds.append({'caption': {'$regex': pat, '$options': 'i'}})

    if not file_name_conds:
        filter_query = {}
    elif query and se_patterns:
        # match title words in either field, AND S/E in either field
        filter_query = {
            '$and': [
                {'$or': [
                    {'$and': [c for c in file_name_conds if 'file_name' in c and '$regex' in c['file_name'] and c['file_name']['$regex'] not in [p for p in se_patterns]]},
                ]},
            ]
        }
        # simpler: require every condition to match in either file_name or caption
        filter_query = {
            '$and': [
                {'$or': [fn, cap]}
                for fn, cap in zip(file_name_conds, caption_conds)
            ]
        }
    else:
        filter_query = {
            '$or': [
                {'$and': file_name_conds},
                {'$and': caption_conds},
            ]
        }

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
