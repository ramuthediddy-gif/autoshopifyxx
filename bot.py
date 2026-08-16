import asyncio
import concurrent.futures
import datetime
import html as _html
import importlib.util
import json
import os
import random
import re
import sys
import time
import logging
import httpx
from io import BytesIO

# ── Logging ───────────────────────────────────────────────────────────────────
from logging.handlers import RotatingFileHandler

_LOG_DIR  = os.path.dirname(os.path.abspath(__file__))
_LOG_FMT  = logging.Formatter(
    "%(asctime)s │ %(levelname)s │ %(name)s │ %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

_root = logging.getLogger()
_root.setLevel(logging.INFO)

_console = logging.StreamHandler()
_console.setFormatter(_LOG_FMT)
_root.addHandler(_console)

_file_all = RotatingFileHandler(
    os.path.join(_LOG_DIR, "bot.log"),
    maxBytes=10 * 1024 * 1024,
    backupCount=5,
    encoding="utf-8",
)
_file_all.setFormatter(_LOG_FMT)
_root.addHandler(_file_all)

_file_err = RotatingFileHandler(
    os.path.join(_LOG_DIR, "bot_error.log"),
    maxBytes=5 * 1024 * 1024,
    backupCount=3,
    encoding="utf-8",
)
_file_err.setLevel(logging.WARNING)
_file_err.setFormatter(_LOG_FMT)
_root.addHandler(_file_err)

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

log = logging.getLogger("bot")

from auth import user_auth, OWNER_ID, APPROVED_GROUP_ID, MONITOR_GROUP_ID

# ══════════════════════════════════════════════════════════════════════════════
#  MATHEMATICAL ITALIC FONT CONVERTER
# ══════════════════════════════════════════════════════════════════════════════

_ITALIC_MAP = {}
# Uppercase A-Z → 𝐴-𝑍 (U+1D434 to U+1D44D)
for i, c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
    _ITALIC_MAP[c] = chr(0x1D434 + i)
# Lowercase a-z → 𝑎-𝑧 (U+1D44E to U+1D467)
for i, c in enumerate("abcdefghijklmnopqrstuvwxyz"):
    _ITALIC_MAP[c] = chr(0x1D44E + i)
# Digits 0-9 → normal (no italic digits in this range, keep as is)


def it(text: str) -> str:
    """Convert ASCII letters to Mathematical Italic Unicode."""
    return "".join(_ITALIC_MAP.get(c, c) for c in text)


def bold(text: str) -> str:
    """Keep bold for numbers/ASCII if needed, but we mainly use italic."""
    return text


# ══════════════════════════════════════════════════════════════════════════════
#  PREMIUM EMOJI IDS (from @K11R7A)
# ══════════════════════════════════════════════════════════════════════════════

E = {
    # Status
    "charged": "5323373120260695190",
    "approved": "5325881737643847450",
    "declined": "5323395299471813204",
    "dead": "5323688589903554436",
    "error": "5323745386551077258",
    "loading": "5325975385110766586",
    "stop": "5325764789979344884",
    "live": "5323439958541756290",
    "ccn": "5323500663609519497",
    "3ds": "5323393718923848521",

    # Card/Gate/Site
    "card": "5472250091332993630",
    "gate": "5323337128434755671",
    "site": "5134452506935427991",
    "amount": "5039789890133296083",
    "code": "5323323569223001338",
    "bin": "5332455502917949981",
    "type": "5350396951407895212",
    "bank": "5332455502917949981",
    "country": "5285452600601237916",

    # Progress
    "total": "5472250091332993630",
    "checked": "5325957011240675544",
    "progress_charged": "5323600886671370439",
    "progress_approved": "5325881737643847450",
    "progress_declined": "5325786604118239576",
    "errors": "5335027110291464473",
    "time": "5323552181742233895",
    "elapsed": "5323552181742233895",

    # Welcome/Profile
    "bot_name": "5334915003055108323",
    "welcome": "5323257405251806081",
    "role": "5980995951160987855",
    "limit": "5226656353744862682",
    "access": "5215327832040811010",
    "commands": "5334915003055108323",
    "user": "5321304384838057247",

    # Admin/Maintenance
    "maintenance": "5325955727045452836",
    "session_paused": "6114014038960638990",
    "broadcast": "5195033767969839232",
    "key": "5323323569223001338",

    # General
    "star": "5325957011240675544",
    "bolt": "5323441728068282028",
    "rocket": "5195033767969839232",
    "gem": "5323373120260695190",
    "check": "5325881737643847450",
    "cross": "5323395299471813204",
    "warn": "5323745386551077258",
    "link": "5042101437237036298",
    "globe": "5134452506935427991",
    "hourglass": "5215327832040811010",
    "refresh": "5852670420074893746",
    "gift": "5323323569223001338",
    "dice": "5361696340348779794",
    "plus": "5253652327734192243",
    "prev": "4902349923049014048",
    "next": "4902715076873553054",
    "visa": "5298970748172385213",
    "master": "5355269226732995665",
    "amex": "4983234121556820510",
    "file": "5323323569223001338",
    "proxy": "5323337128434755671",
    "shield": "5325955727045452836",
    "crown": "5980995951160987855",
    "skull": "5334891359260139551",
    "fire": "5325879152073534208",
    "smile": "5325854365817268139",
    "cat": "5323816425310153032",
    "moon": "5325975385110766586",
    "heart": "5325778409320638497",
    "candle": "5325720723614885288",
    "cookie": "5326028234683344250",
    "plane": "5323344378339550016",
    "test_tube": "5325773869540205894",
    "watch": "5323552181742233895",
    "thumbs_up": "5323345563750527116",
    "thumbs_down": "5323603562435995538",
    "arrow_right": "5325526651222652842",
    "tongue": "5325827582401211584",
    "minus": "5325756947369060958",
    "coin": "5325606739477817150",
    "salute": "5323763635867114693",
    "lips": "5325647447177848062",
    "peach": "5325784113037209438",
    "tea": "5323570302209255107",
    "drink": "5325731611356981418",
    "ring": "5325577731268698044",
    "dark_moon": "5323707002428353300",
    "bandage": "5323558735862327633",
    "eye": "5323723018361399476",
    "sparkle": "5325851329275390707",
    "rose": "5326036047228856322",
    "swan": "5323654002531919683",
    "plead": "5323512942921017209",
    "pray": "5323715991794903532",
    "letter": "5325656943350537751",
    "tulip": "5323323861280779494",
    "high_heel": "5325631031812845280",
    "apple": "5323522443388673731",
    "rabbit": "5323569773928279281",
    "birthday": "5334736014588009766",
    "map": "5334731260059218242",
    "game": "5335027110291464473",
    "pin": "5334731260059218242",
    "ghost": "5323688589903554436",
    "bat": "5323816425310153032",
    "blood": "5325814212168019691",
    "kiss": "5323500629249779697",
    "music": "5323450648715356960",
    "diamond": "5323600886671370439",
    "crown2": "5325577731268698044",
    "potion": "5325773869540205894",
    "wizard": "5335021367920188925",
    "alien": "5335027110291464473",
    "frog": "5323569773928279281",
    "web": "5325955727045452836",
    "lock": "5323393718923848521",
    "unlock": "5323465535072004671",
    "bell": "5323393718923848521",
    "no_bell": "5323465535072004671",
    "ticket": "5323323569223001338",
    "medal": "5325577731268698044",
    "trophy": "5325577731268698044",
    "crown3": "5980995951160987855",
    "star2": "5323734219636108448",
    "star3": "5323806963497197379",
    "fire2": "5323355802952560649",
    "poop": "5323688589903554436",
    "clown": "5325853974975244331",
    "robot": "5335027110291464473",
    "pumpkin": "5323688589903554436",
    "christmas": "5325815096931280384",
    "santa": "5325815096931280384",
    "gift2": "5334592816083396790",
    "crystal": "5334720269237907292",
    "lollipop": "5332432043806582477",
    "numbers": "5334727459013159723",
    "abc": "5334682469230737214",
    "abcd": "5334738793431850273",
    "abcd2": "5334682469230737214",
    "ok": "5325881737643847450",
    "ng": "5323395299471813204",
    "new": "5323439958541756290",
    "free": "5323257405251806081",
    "cool": "5323428168856527967",
    "back": "5325526651222652842",
    "soon": "5323745386551077258",
    "top": "5325957011240675544",
    "100": "5325881737643847450",
}


def pe(emoji_id: str) -> str:
    """Wrap a custom emoji ID into Telegram premium emoji HTML."""
    return f'<tg-emoji emoji-id="{emoji_id}">⚡</tg-emoji>'


# ══════════════════════════════════════════════════════════════════════════════
#  CONFIG
# ══════════════════════════════════════════════════════════════════════════════

TOKEN = "8327063101:AAGXjgMkaw3NaOw66IJV9aRuHmFS7gKua-Y"

BOT_NAME = "hchk.cards"
POWERED_BY = "@racisthenry"
CHANNEL_LINK = "https://t.me/+ODR6vIC6G-03MTkx"
GROUP_LINK = "https://t.me/+rxioFiLN2ZBmZTcx"

join_channel_id = -100161
join_chat_id = -1002500064

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROXY_FILE = os.path.join(BASE_DIR, "proxy.json")
SITES_FILE = os.path.join(BASE_DIR, "sites.txt")
SITES_JSON = os.path.join(BASE_DIR, "sites.json")
STSITE_FILE = os.path.join(BASE_DIR, "stsite.json")
RZSITE_FILE = os.path.join(BASE_DIR, "rzsite.json")
SKKEYS_FILE = os.path.join(BASE_DIR, "skkeys.json")
BANNED_FILE = os.path.join(BASE_DIR, "banned.json")
USERS_FILE = os.path.join(BASE_DIR, "users.json")
KEYS_FILE = os.path.join(BASE_DIR, "keys.json")
CREDITS_FILE = os.path.join(BASE_DIR, "credits.json")
FREEPROXY_DATA_FILE = os.path.join(BASE_DIR, "freeproxy_data.json")

MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB

LIMITS = {
    "free": 300,
    "premium": 8000,
    "admin": 15000,
    "owner": 30000,
}

# ── Thread pool ──────────────────────────────────────────────────────────────
CHECKER_POOL = concurrent.futures.ThreadPoolExecutor(max_workers=500)

# ── Per-user concurrency ─────────────────────────────────────────────────────
_USER_SEM_LIMIT = 100
_user_semaphores: dict[int, asyncio.Semaphore] = {}

# ── Antispam cooldown ────────────────────────────────────────────────────────
_ANTISPAM_COOLDOWN = 20
_user_last_cmd: dict[int, float] = {}

# ── File check active users ──────────────────────────────────────────────────
_RAN_ACTIVE_USERS: set[int] = set()
_RAN_STOP_FLAGS: dict[str, bool] = {}
_RAN_GLOBAL_LIMIT = 600
_ran_global_sem = asyncio.Semaphore(_RAN_GLOBAL_LIMIT)
_ran_user_sems: dict[int, asyncio.Semaphore] = {}

# ── Maintenance mode ─────────────────────────────────────────────────────────
_MAINTENANCE_MODE: bool = False
_MAINTENANCE_REASON: str = ""
_active_sessions: dict[str, dict] = {}  # session_id -> {user_id, total, checked, msg_id}

# ══════════════════════════════════════════════════════════════════════════════
#  IMPORT GATE MODULES
# ══════════════════════════════════════════════════════════════════════════════

from helpers import (
    parse_proxy_format, test_proxy, bin_lookup,
    extract_cc, close_session, proxy_dict_to_url,
)
import checker_bridge
import auth
import hit
import st
import rz
import chk
import vbv
import b3auth

try:
    import sk as skcvv
    _SK_AVAILABLE = True
except ImportError:
    skcvv = None
    _SK_AVAILABLE = False

try:
    import dork as _dork_mod
    _DORK_AVAILABLE = True
except ImportError:
    _dork_mod = None
    _DORK_AVAILABLE = False

try:
    import webshare as _webshare_mod
    _WEBSHARE_AVAILABLE = True
except ImportError:
    _webshare_mod = None
    _WEBSHARE_AVAILABLE = False

try:
    import gate as _gate_mod
    _GATE_AVAILABLE = True
except ImportError:
    _gate_mod = None
    _GATE_AVAILABLE = False

# Load stripe1$ gate
try:
    st1_gate = _load_gate_file("stripe1$.py")
except Exception:
    st1_gate = None


def _load_gate_file(filename: str):
    path = os.path.join(BASE_DIR, filename)
    if not os.path.isfile(path):
        return None
    mod_name = "gate_" + re.sub(r"[^a-zA-Z0-9_]", "_", filename)
    spec = importlib.util.spec_from_file_location(mod_name, path)
    if not spec or not spec.loader:
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ══════════════════════════════════════════════════════════════════════════════
#  AUTH & CREDITS SYSTEM
# ══════════════════════════════════════════════════════════════════════════════


# ══════════════════════════════════════════════════════════════════════════════
#  PROXY STORAGE
# ══════════════════════════════════════════════════════════════════════════════

_proxy_cache: dict | None = None
_proxy_cache_mtime: float = 0.0


def _load_proxies() -> dict:
    global _proxy_cache, _proxy_cache_mtime
    try:
        mt = os.path.getmtime(PROXY_FILE)
    except OSError:
        return {}
    if _proxy_cache is not None and mt == _proxy_cache_mtime:
        return _proxy_cache
    try:
        with open(PROXY_FILE, "r", encoding="utf-8") as f:
            _proxy_cache = json.load(f)
            _proxy_cache_mtime = mt
            return _proxy_cache
    except Exception:
        return {}


def _save_proxies(data: dict):
    global _proxy_cache, _proxy_cache_mtime
    with open(PROXY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    _proxy_cache = data
    try:
        _proxy_cache_mtime = os.path.getmtime(PROXY_FILE)
    except OSError:
        _proxy_cache_mtime = 0.0


MAX_PROXIES_PER_USER = 30


def get_user_proxies(user_id: int) -> list:
    data = _load_proxies()
    proxies = data.get(str(user_id), [])
    if isinstance(proxies, dict):
        proxies = [proxies] if proxies else []
    if isinstance(proxies, str):
        proxies = [proxies] if proxies.strip() else []
    out = []
    for p in proxies:
        if isinstance(p, dict):
            out.append(p)
        elif isinstance(p, str) and p.strip():
            parsed = parse_proxy_format(p.strip())
            if parsed:
                out.append(parsed)
    return out


def get_user_proxy(user_id: int) -> dict | None:
    proxies = get_user_proxies(user_id)
    return random.choice(proxies) if proxies else None


def add_user_proxies(user_id: int, new_proxies: list[dict]):
    data = _load_proxies()
    existing = data.get(str(user_id), [])
    if isinstance(existing, dict):
        existing = [existing] if existing else []
    if isinstance(existing, str):
        existing = [existing] if existing.strip() else []
    existing.extend(new_proxies)
    data[str(user_id)] = existing[:MAX_PROXIES_PER_USER]
    _save_proxies(data)


def del_user_proxy(user_id: int):
    data = _load_proxies()
    data.pop(str(user_id), None)
    _save_proxies(data)


# ══════════════════════════════════════════════════════════════════════════════
#  SITES LOADER
# ══════════════════════════════════════════════════════════════════════════════

_sites_cache: list[str] | None = None
_sites_cache_mtime: float = 0.0


def _load_sites() -> list[str]:
    global _sites_cache, _sites_cache_mtime
    src = SITES_JSON if os.path.isfile(SITES_JSON) else SITES_FILE
    try:
        mt = os.path.getmtime(src)
    except OSError:
        return []
    if _sites_cache is not None and mt == _sites_cache_mtime:
        return _sites_cache
    urls = []
    if src == SITES_JSON:
        try:
            with open(SITES_JSON, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                for entry in data:
                    site = (entry.get("Site") or "").strip().rstrip("/")
                    if site:
                        if not site.startswith("http"):
                            site = "https://" + site
                        urls.append(site)
        except Exception:
            src = SITES_FILE
    if src == SITES_FILE:
        try:
            with open(SITES_FILE, "r", encoding="utf-8") as f:
                urls = [l.strip().rstrip("/") for l in f if l.strip()]
        except Exception:
            pass
    seen = set()
    deduped = [u for u in urls if not (u in seen or seen.add(u))]
    _sites_cache = deduped
    _sites_cache_mtime = mt
    return _sites_cache


def get_random_site() -> str | None:
    sites = _load_sites()
    return random.choice(sites) if sites else None


# ══════════════════════════════════════════════════════════════════════════════
#  SITE STORAGE (ST + RZ)
# ══════════════════════════════════════════════════════════════════════════════

STSITE_MAX = 25
RZSITE_MAX = 25


def _load_json_file(path: str) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_json_file(path: str, data: dict):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_user_stsites(user_id: int) -> list[str]:
    data = _load_json_file(STSITE_FILE)
    val = data.get(str(user_id), [])
    if isinstance(val, str):
        return [val] if val else []
    return val if isinstance(val, list) else []


def add_user_stsite(user_id: int, url: str) -> str:
    url = url.strip().replace("https://", "").replace("http://", "").strip("/")
    data = _load_json_file(STSITE_FILE)
    sites = get_user_stsites(user_id)
    if url in sites:
        return "duplicate"
    if len(sites) >= STSITE_MAX:
        return "limit"
    sites.append(url)
    data[str(user_id)] = sites
    _save_json_file(STSITE_FILE, data)
    return "added"


def del_user_stsite(user_id: int, index: int | None = None):
    data = _load_json_file(STSITE_FILE)
    key = str(user_id)
    sites = get_user_stsites(user_id)
    if index is None:
        data.pop(key, None)
    else:
        if 1 <= index <= len(sites):
            sites.pop(index - 1)
            if sites:
                data[key] = sites
            else:
                data.pop(key, None)
    _save_json_file(STSITE_FILE, data)


def get_user_rzsites(user_id: int) -> list[str]:
    data = _load_json_file(RZSITE_FILE)
    val = data.get(str(user_id), [])
    if isinstance(val, str):
        return [val] if val else []
    return val if isinstance(val, list) else []


def add_user_rzsite(user_id: int, url: str) -> str:
    url = url.strip().replace("https://", "").replace("http://", "").strip("/")
    data = _load_json_file(RZSITE_FILE)
    sites = get_user_rzsites(user_id)
    if url in sites:
        return "duplicate"
    if len(sites) >= RZSITE_MAX:
        return "limit"
    sites.append(url)
    data[str(user_id)] = sites
    _save_json_file(RZSITE_FILE, data)
    return "added"


def del_user_rzsite(user_id: int, index: int | None = None):
    data = _load_json_file(RZSITE_FILE)
    key = str(user_id)
    sites = get_user_rzsites(user_id)
    if index is None:
        data.pop(key, None)
    else:
        if 1 <= index <= len(sites):
            sites.pop(index - 1)
            if sites:
                data[key] = sites
            else:
                data.pop(key, None)
    _save_json_file(RZSITE_FILE, data)


# ══════════════════════════════════════════════════════════════════════════════
#  SK KEYS STORAGE
# ══════════════════════════════════════════════════════════════════════════════

_sk_cache: dict | None = None
_sk_mtime: float = 0.0


def _load_skkeys() -> dict:
    global _sk_cache, _sk_mtime
    try:
        mt = os.path.getmtime(SKKEYS_FILE)
    except OSError:
        return {}
    if _sk_cache is not None and mt == _sk_mtime:
        return _sk_cache
    try:
        with open(SKKEYS_FILE, "r", encoding="utf-8") as f:
            _sk_cache = json.load(f)
            _sk_mtime = mt
            return _sk_cache
    except Exception:
        return {}


def _save_skkeys(data: dict):
    global _sk_cache, _sk_mtime
    with open(SKKEYS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    _sk_cache = data
    try:
        _sk_mtime = os.path.getmtime(SKKEYS_FILE)
    except OSError:
        _sk_mtime = 0.0


def get_user_sk(user_id: int) -> tuple[str, str] | None:
    entry = _load_skkeys().get(str(user_id))
    if not isinstance(entry, dict):
        return None
    sk = (entry.get("sk") or "").strip()
    pk = (entry.get("pk") or "").strip()
    if sk.startswith("sk_") and pk.startswith("pk_"):
        return sk, pk
    return None


def set_user_sk(user_id: int, sk: str, pk: str):
    data = _load_skkeys()
    data[str(user_id)] = {"sk": sk.strip(), "pk": pk.strip()}
    _save_skkeys(data)


def del_user_sk(user_id: int):
    data = _load_skkeys()
    if str(user_id) in data:
        del data[str(user_id)]
        _save_skkeys(data)


# ══════════════════════════════════════════════════════════════════════════════
#  TELEGRAM BOT SETUP
# ══════════════════════════════════════════════════════════════════════════════

from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.filters import Command, CommandStart
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode, ChatMemberStatus
from aiogram.exceptions import (
    TelegramRetryAfter,
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramNotFound,
)

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher()
router = Router()
dp.include_router(router)


# ══════════════════════════════════════════════════════════════════════════════
#  SAFE EDIT HELPER
# ══════════════════════════════════════════════════════════════════════════════

async def safe_edit(msg: types.Message, text: str, **kwargs) -> bool:
    for attempt in range(2):
        try:
            await msg.edit_text(text, **kwargs)
            return True
        except TelegramRetryAfter as e:
            wait = min(e.retry_after + 1, 15)
            await asyncio.sleep(wait)
        except TelegramBadRequest as e:
            emsg = str(e).lower()
            if "message is not modified" in emsg:
                return True
            if any(x in emsg for x in ("message can't be edited", "message to edit not found", "chat not found", "message_id_invalid")):
                return False
            return False
        except TelegramForbiddenError:
            return False
        except TelegramNotFound:
            return False
        except Exception as e:
            log.error("safe_edit unexpected: %s", e)
            return False
    return False


# ══════════════════════════════════════════════════════════════════════════════
#  JOIN CHECK
# ══════════════════════════════════════════════════════════════════════════════

_join_cache: dict[int, tuple[bool, float]] = {}
_JOIN_CACHE_TTL_OK = 300
_JOIN_CACHE_TTL_NO = 30


async def check_user_joined(user_id: int, force: bool = False) -> bool:
    now = time.time()
    if not force:
        cached = _join_cache.get(user_id)
        if cached:
            ttl = _JOIN_CACHE_TTL_OK if cached[0] else _JOIN_CACHE_TTL_NO
            if now - cached[1] < ttl:
                return cached[0]
    try:
        ch_member = await bot.get_chat_member(join_channel_id, user_id)
        gr_member = await bot.get_chat_member(join_chat_id, user_id)
        valid = {ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR}
        result = ch_member.status in valid and gr_member.status in valid
    except Exception:
        result = False
    _join_cache[user_id] = (result, now)
    return result


def join_keyboard() -> dict:
    return {
        "inline_keyboard": [
            [
                {"text": it("Join Channel"), "url": CHANNEL_LINK},
                {"text": it("Join Group"), "url": GROUP_LINK},
            ],
            [
                {"text": it("Verify Joined"), "callback_data": "verify_join"},
            ],
        ]
    }


# ══════════════════════════════════════════════════════════════════════════════
#  OUTPUT FORMATTERS (ELVE GOLD STYLE)
# ══════════════════════════════════════════════════════════════════════════════

def format_single_result(
    cc_str: str,
    gate_name: str,
    site: str,
    amount: str,
    code: str,
    status: str,
    bin_info: dict,
    user_id: int,
    username: str,
) -> str:
    """ELVE GOLD style single check output."""
    # Determine status header
    if status == "charged":
        header = f"{pe(E['charged'])} {it('Order Placed!')}"
    elif status in ("live", "approved"):
        if "insufficient" in code.lower():
            header = f"{pe(E['approved'])} {it('Insufficient Funds')}"
        elif "cvc" in code.lower() or "cvv" in code.lower():
            header = f"{pe(E['ccn'])} {it('Incorrect CVC')}"
        elif "3ds" in code.lower() or "otp" in code.lower():
            header = f"{pe(E['3ds'])} {it('3DS / OTP Required')}"
        else:
            header = f"{pe(E['live'])} {it('Live Card')}"
    elif status == "declined":
        header = f"{pe(E['declined'])} {it('Card Declined')}"
    elif status == "dead":
        header = f"{pe(E['dead'])} {it('Dead Card')}"
    else:
        header = f"{pe(E['error'])} {it('Unknown Response')}"

    # Mask site
    if site and len(site) > 20:
        parsed = site.replace("https://", "").replace("http://", "")
        if len(parsed) > 20:
            site_display = parsed[:8] + "*******************" + parsed[-15:]
        else:
            site_display = parsed
    else:
        site_display = site or "-"

    lines = [
        header,
        "━━━━━━━━━━━━━━━━━━━━",
        f"{pe(E['card'])} {it('Card')} → {cc_str}",
        f"{pe(E['gate'])} {it('Gate')} → {gate_name.upper()}",
        f"{pe(E['site'])} {it('Site')} → {site_display}",
        f"{pe(E['amount'])} {it('Amount')} → {amount}",
        f"{pe(E['code'])} {it('Code')} → {code.upper()}",
        "━━━━━━━━━━━━━━━━━━━━",
        f"{pe(E['bin'])} {it('BIN')} → {bin_info.get('brand', '-')}",
        f"{pe(E['type'])} {it('Type')} → {bin_info.get('type', '-')} {bin_info.get('level', '')}",
        f"{pe(E['bank'])} {it('Bank')} → {bin_info.get('bank', '-')}",
        f"{pe(E['country'])} {it('Country')} → {bin_info.get('flag', '')} {bin_info.get('country', '-')}",
        "━━━━━━━━━━━━━━━━━━━━",
        f"{pe(E['user'])} {it('User')} → @{username}",
        f"{pe(E['broadcast'])} Powered by {POWERED_BY}",
    ]
    return "\n".join(lines)


def format_progress_status(
    total: int,
    checked: int,
    charged: int,
    approved: int,
    declined: int,
    errors: int,
    elapsed: str,
    last_cc: str = "",
    last_response: str = "",
) -> str:
    """ELVE GOLD style file check progress."""
    pct = (checked / total * 100) if total > 0 else 0
    bar_len = 20
    filled = int(bar_len * pct / 100)
    bar = "█" * filled + "░" * (bar_len - filled)

    lines = [
        f"{pe(E['loading'])} {it('Live Checking')} {pe(E['rocket'])}",
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬",
        f"{bar} {pct:.1f}%",
        "",
        f"{pe(E['total'])} {it('Total')} → {total}",
        f"{pe(E['checked'])} {it('Checked')} → {checked}",
        f"{pe(E['progress_charged'])} {it('Charged')} → {charged}",
        f"{pe(E['progress_approved'])} {it('Approved')} → {approved}",
        f"{pe(E['progress_declined'])} {it('Declined')} → {declined}",
        f"{pe(E['errors'])} {it('Errors')} → {errors}",
    ]
    if last_cc:
        lines.append("▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬")
        lines.append(f"{pe(E['card'])} {last_cc}")
        lines.append(f"{pe(E['code'])} {last_response[:60]}")
    lines.append("▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬")
    lines.append(f"{pe(E['elapsed'])} {it('Elapsed')} → {elapsed}")
    return "\n".join(lines)


def format_welcome_card(user_id: int, username: str, full_name: str, role: str, limit: int) -> str:
    """X D Bot style welcome card."""
    role_emoji = {"owner": pe(E["crown"]), "admin": pe(E["shield"]), "premium": pe(E["gem"]), "free": pe(E["star"])}.get(role, pe(E["star"]))
    access = "None" if role == "free" else role.title()

    lines = [
        f"{pe(E['bot_name'])} {it(BOT_NAME)}",
        "",
        f"{pe(E['welcome'])} {it(f'Welcome, @{username}')}",
        "",
        f"{role_emoji} {it('Role')} → {it(role.title())}",
        f"{pe(E['card'])} {it('CC Limit')} → {limit}",
        f"{pe(E['access'])} {it('Access')} → {it(access)}",
        "",
        f"{pe(E['commands'])} {it('Commands')}",
        f"{pe(E['star'])} /sc — {it('single card check')}",
        f"{pe(E['rocket'])} /msc — {it('mass check (inline)')}",
        f"{pe(E['file'])} /msctxt — {it('mass check (.txt file)')}",
        f"{pe(E['gate'])} /st — {it('woocommerce check')}",
        f"{pe(E['gate'])} /rz — {it('razorpay check')}",
        f"{pe(E['gate'])} /chk — {it('stripe auth check')}",
        f"{pe(E['gate'])} /vbv — {it('braintree vbv')}",
        f"{pe(E['gate'])} /br — {it('braintree auth')}",
        f"{pe(E['gate'])} /b3 — {it('b3 auth')}",
        f"{pe(E['gate'])} /st1 — {it('stripe $1')}",
        f"{pe(E['gate'])} /hit — {it('stripe checkout')}",
        f"{pe(E['gate'])} /skcvv — {it('stripe sk check')}",
        f"{pe(E['gate'])} /gate — {it('gateway lookup')}",
        f"{pe(E['bin'])} /bin — {it('bin lookup')}",
        f"{pe(E['dork'])} /dork — {it('url scraper')}",
        f"{pe(E['proxy'])} /proxy — {it('set proxy')}",
        f"{pe(E['key'])} /redeem — {it('redeem a key')}",
        f"{pe(E['user'])} /me — {it('your profile')}",
    ]
    return "\n".join(lines)


def format_profile(user_id: int, username: str, full_name: str, role: str, limit: int, proxy_count: int) -> str:
    """X D Bot style profile card."""
    role_emoji = {"owner": pe(E["crown"]), "admin": pe(E["shield"]), "premium": pe(E["gem"]), "free": pe(E["star"])}.get(role, pe(E["star"]))

    lines = [
        f"{pe(E['user'])} {it('User Profile')}",
        "",
        f"{pe(E['welcome'])} {it('Name')} → @{username}",
        f"{pe(E['code'])} {it('ID')} → {user_id}",
        "━━━━━━━━━━━━━━━━━━━━",
        f"{role_emoji} {it('Role')} → {it(role.title())}",
        f"{pe(E['card'])} {it('CC Limit')} → {limit}",
        f"{pe(E['limit'])} {it('Credits')} → {user_auth.get_credits(user_id)}",
        "━━━━━━━━━━━━━━━━━━━━",
        f"{pe(E['proxy'])} {it('Proxy')} → {proxy_count} proxies set",
    ]
    return "\n".join(lines)


def format_maintenance_pause(checked: int, total: int, reason: str) -> str:
    """ELVE GOLD style maintenance pause."""
    lines = [
        f"{pe(E['stop'])} {it('SESSION PAUSED')}",
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬",
        f"{pe(E['warn'])} {it('HEY! YOUR BATCH HAS BEEN')}",
        f"{pe(E['info'])} {it('STOPPED BY THE ADMINISTRATOR')}",
        "",
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬",
        f"{pe(E['shield'])} {it('REASON')} → {reason}",
        "",
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬",
        f"{pe(E['mail'])} {it('YOUR PROGRESS')} → {checked} / {total} {it('CARDS CHECKED')}",
        "",
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬",
        f"{pe(E['check'])} {it('NOTE: YOU CAN RE-UPLOAD YOUR')}",
        f"{pe(E['file'])} {it('CARDS AND CONTINUE CHECKING!')}",
    ]
    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════════════
#  MIDDLEWARE
# ══════════════════════════════════════════════════════════════════════════════

from aiogram import BaseMiddleware

class ThrottleMiddleware(BaseMiddleware):
    _RATE = 0.4
    _AUTO_BAN_WINDOW = 10.0
    _AUTO_BAN_LIMIT = 20
    _last: dict[int, float] = {}
    _window: dict[int, list[float]] = {}

    async def __call__(self, handler, event, data):
        user: types.User | None = data.get("event_from_user")
        if not user:
            return await handler(event, data)
        uid = user.id

        if user_auth.is_banned(uid):
            return

        now = time.monotonic()
        times = self._window.get(uid, [])
        times = [t for t in times if now - t < self._AUTO_BAN_WINDOW]
        times.append(now)
        self._window[uid] = times

        if len(times) >= self._AUTO_BAN_LIMIT:
            user_auth.ban_user(uid)
            log.warning("AUTO-BAN: user %s spam", uid)
            return

        last = self._last.get(uid, 0.0)
        diff = now - last
        if diff < self._RATE:
            await asyncio.sleep(self._RATE - diff)
        self._last[uid] = time.monotonic()

        return await handler(event, data)

dp.message.middleware(ThrottleMiddleware())
dp.callback_query.middleware(ThrottleMiddleware())


# ══════════════════════════════════════════════════════════════════════════════
#  GLOBAL ERROR HANDLER
# ══════════════════════════════════════════════════════════════════════════════

@dp.errors()
async def global_error_handler(event: types.ErrorEvent):
    exc = event.exception
    if isinstance(exc, TelegramRetryAfter):
        await asyncio.sleep(exc.retry_after + 1)
        return True
    if isinstance(exc, TelegramForbiddenError):
        return True
    log.error("Unhandled: %s", exc, exc_info=True)
    return True


# ══════════════════════════════════════════════════════════════════════════════
#  COMMAND HANDLERS
# ══════════════════════════════════════════════════════════════════════════════

# ── /start ───────────────────────────────────────────────────────────────────
@router.message(CommandStart())
async def cmd_start(message: types.Message):
    uid = message.from_user.id
    user_auth.save_user(uid, message.from_user.username, message.from_user.full_name)

    joined = await check_user_joined(uid)
    if not joined:
        await message.reply(
            f"{pe(E['warn'])} {it('Access Restricted')}\n\n"
            f"{pe(E['bolt'])} {it('You must join our channel and group to use this bot.')}\n\n"
            f"{pe(E['link'])} {it('Tap the buttons below to join, then tap Verify.')}",
            reply_markup=join_keyboard(),
        )
        return

    if user_auth.is_banned(uid):
        await message.reply(f"{pe(E['cross'])} {it('You are banned from this bot!')}")
        return

    role = user_auth.get_role(uid)
    limit = user_auth.get_limit(uid)
    text = format_welcome_card(uid, message.from_user.username or "Unknown", message.from_user.full_name or "", role, limit)
    await message.reply(text)


# ── /me ──────────────────────────────────────────────────────────────────────
@router.message(Command("me"))
async def cmd_me(message: types.Message):
    uid = message.from_user.id
    role = user_auth.get_role(uid)
    limit = user_auth.get_limit(uid)
    proxies = get_user_proxies(uid)
    text = format_profile(uid, message.from_user.username or "Unknown", message.from_user.full_name or "", role, limit, len(proxies))
    await message.reply(text)


# ── /cmds ────────────────────────────────────────────────────────────────────
@router.message(Command("cmds"))
async def cmd_cmds(message: types.Message):
    text = format_welcome_card(
        message.from_user.id,
        message.from_user.username or "Unknown",
        message.from_user.full_name or "",
        user_auth.get_role(message.from_user.id),
        user_auth.get_limit(message.from_user.id),
    )
    await message.reply(text)


# ── /proxy ───────────────────────────────────────────────────────────────────
@router.message(Command("proxy"))
async def cmd_proxy(message: types.Message):
    uid = message.from_user.id
    joined = await check_user_joined(uid)
    if not joined:
        await message.reply(it("Join channel and group first!"), reply_markup=join_keyboard())
        return

    raw_text = ""
    args = message.text.split(maxsplit=1)
    if len(args) >= 2:
        raw_text = args[1]
    if message.reply_to_message:
        reply_txt = message.reply_to_message.text or message.reply_to_message.caption or ""
        if reply_txt.strip():
            raw_text = raw_text + "\n" + reply_txt if raw_text else reply_txt
        if message.reply_to_message.document:
            doc = message.reply_to_message.document
            if doc.file_name and doc.file_name.lower().endswith(".txt"):
                try:
                    buf = BytesIO()
                    await bot.download(doc.file_id, destination=buf)
                    buf.seek(0)
                    file_text = buf.read().decode("utf-8", errors="ignore")
                    if file_text.strip():
                        raw_text = raw_text + "\n" + file_text if raw_text else file_text
                except Exception as e:
                    log.error("Proxy file download: %s", e)

    if not raw_text.strip():
        await message.reply(
            f"{pe(E['warn'])} {it('Usage:')}\n"
            f"/proxy host:port:user:pass\n"
            f"{it('Or reply to a .txt file with proxies')}"
        )
        return

    parsed_list = []
    for line in raw_text.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        parsed = parse_proxy_format(line)
        if parsed:
            parsed_list.append(parsed)

    if not parsed_list:
        await message.reply(f"{pe(E['cross'])} {it('No valid proxies found!')}")
        return

    need = MAX_PROXIES_PER_USER - len(get_user_proxies(uid))
    if need <= 0:
        await message.reply(f"{pe(E['warn'])} {it('Proxy list full!')} {MAX_PROXIES_PER_USER}/{MAX_PROXIES_PER_USER}")
        return

    status_msg = await message.reply(f"{pe(E['loading'])} {it('Testing proxies...')}")
    working = []
    dead = 0

    for p in parsed_list[:need]:
        try:
            success, _, _ = await test_proxy(p.get("proxy_url", ""))
            if success:
                working.append(p)
            else:
                dead += 1
        except Exception:
            dead += 1

    if working:
        add_user_proxies(uid, working)
        await safe_edit(status_msg, f"{pe(E['check'])} {it(f'Added {len(working)} working proxies!')}\n{pe(E['cross'])} {it(f'Dead: {dead}')}")
    else:
        await safe_edit(status_msg, f"{pe(E['cross'])} {it('All proxies dead!')}")


# ── /myproxy ─────────────────────────────────────────────────────────────────
@router.message(Command("myproxy"))
async def cmd_myproxy(message: types.Message):
    proxies = get_user_proxies(message.from_user.id)
    if not proxies:
        await message.reply(f"{pe(E['cross'])} {it('No proxies set!')}")
        return
    lines = [f"{pe(E['link'])} {it('Your Proxies')} [{len(proxies)}/{MAX_PROXIES_PER_USER}]\n"]
    for i, p in enumerate(proxies[:10], 1):
        ip = p.get('ip', '-')
        port = p.get('port', '-')
        ptype = p.get('type', 'http').upper()
        lines.append(f"{pe(E['bolt'])} {i}. {ip}:{port} ({ptype})")
    if len(proxies) > 10:
        lines.append(f"{pe(E['next'])} ... {len(proxies) - 10} more")
    await message.reply("\n".join(lines))


# ── /rmproxy ─────────────────────────────────────────────────────────────────
@router.message(Command("rmproxy"))
async def cmd_rmproxy(message: types.Message):
    del_user_proxy(message.from_user.id)
    await message.reply(f"{pe(E['check'])} {it('All proxies removed!')}")


# ── /bin ─────────────────────────────────────────────────────────────────────
@router.message(Command("bin"))
async def cmd_bin(message: types.Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply(f"{pe(E['warn'])} {it('Usage:')} /bin 438854")
        return
    bin_num = re.sub(r'\D', '', args[1].strip())[:6]
    if len(bin_num) < 6:
        await message.reply(f"{pe(E['cross'])} {it('BIN must be at least 6 digits!')}")
        return

    loading = await message.reply(f"{pe(E['loading'])} {it('Looking up BIN')} {bin_num}...")
    info = await bin_lookup(bin_num)

    text = (
        f"{pe(E['bank'])} {it('BIN Lookup Result')}\n\n"
        f"{pe(E['bin'])} {it('BIN:')} {bin_num}\n"
        f"{pe(E['card'])} {it('Brand:')} {info.get('brand', '-')}\n"
        f"{pe(E['type'])} {it('Type:')} {info.get('type', '-')}\n"
        f"{pe(E['bank'])} {it('Bank:')} {info.get('bank', '-')}\n"
        f"{pe(E['country'])} {it('Country:')} {info.get('flag', '')} {info.get('country', '-')}"
    )
    await safe_edit(loading, text)


# ── /redeem ──────────────────────────────────────────────────────────────────
@router.message(Command("redeem"))
async def cmd_redeem(message: types.Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply(f"{pe(E['warn'])} {it('Usage:')} /redeem Kamal-xxxxx")
        return
    key = args[1].strip()
    success, info = user_auth.redeem_key(message.from_user.id, key)
    if success:
        await message.reply(f"{pe(E['gem'])} {it('Key Redeemed!')}\n{pe(E['check'])} {info}")
    else:
        await message.reply(f"{pe(E['cross'])} {it('Redemption Failed!')}\n{pe(E['warn'])} {info}")


# ══════════════════════════════════════════════════════════════════════════════
#  ADMIN / OWNER COMMANDS
# ══════════════════════════════════════════════════════════════════════════════

@router.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if not user_auth.is_owner(message.from_user.id):
        await message.reply(f"{pe(E['cross'])} {it('Owner only!')}")
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].strip().isdigit():
        await message.reply(f"{pe(E['warn'])} {it('Usage:')} /admin user_id")
        return
    target = int(args[1].strip())
    if user_auth.add_admin(target):
        await message.reply(f"{pe(E['check'])} {it('Admin added!')} ID: {target}")
    else:
        await message.reply(f"{pe(E['warn'])} {it('Already admin')}")


@router.message(Command("unadmin"))
async def cmd_unadmin(message: types.Message):
    if not user_auth.is_owner(message.from_user.id):
        await message.reply(f"{pe(E['cross'])} {it('Owner only!')}")
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].strip().isdigit():
        await message.reply(f"{pe(E['warn'])} {it('Usage:')} /unadmin user_id")
        return
    target = int(args[1].strip())
    if user_auth.remove_admin(target):
        await message.reply(f"{pe(E['check'])} {it('Admin removed!')}")
    else:
        await message.reply(f"{pe(E['warn'])} {it('Not an admin')}")


@router.message(Command("auth"))
async def cmd_auth(message: types.Message):
    if not user_auth.is_admin(message.from_user.id):
        await message.reply(f"{pe(E['cross'])} {it('Admin only!')}")
        return
    args = message.text.split()
    if len(args) < 2 or not args[1].strip().isdigit():
        await message.reply(f"{pe(E['warn'])} {it('Usage:')} /auth user_id [days]")
        return
    target = int(args[1].strip())
    days = int(args[2]) if len(args) >= 3 and args[2].isdigit() else 0
    user_auth.auth_user(target, days)
    await message.reply(f"{pe(E['check'])} {it('Premium granted!')} ID: {target}\n{pe(E['gem'])} {'Lifetime' if days == 0 else f'{days} days'}")


@router.message(Command("unauth"))
async def cmd_unauth(message: types.Message):
    if not user_auth.is_admin(message.from_user.id):
        await message.reply(f"{pe(E['cross'])} {it('Admin only!')}")
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].strip().isdigit():
        await message.reply(f"{pe(E['warn'])} {it('Usage:')} /unauth user_id")
        return
    target = int(args[1].strip())
    if user_auth.unauth_user(target):
        await message.reply(f"{pe(E['check'])} {it('Premium removed!')}")
    else:
        await message.reply(f"{pe(E['warn'])} {it('No premium found')}")


@router.message(Command("ban"))
async def cmd_ban(message: types.Message):
    if not user_auth.is_admin(message.from_user.id):
        await message.reply(f"{pe(E['cross'])} {it('Admin only!')}")
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].strip().isdigit():
        await message.reply(f"{pe(E['warn'])} {it('Usage:')} /ban user_id")
        return
    target = int(args[1].strip())
    user_auth.ban_user(target)
    await message.reply(f"{pe(E['check'])} {it('User banned!')} ID: {target}")


@router.message(Command("unban"))
async def cmd_unban(message: types.Message):
    if not user_auth.is_admin(message.from_user.id):
        await message.reply(f"{pe(E['cross'])} {it('Admin only!')}")
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].strip().isdigit():
        await message.reply(f"{pe(E['warn'])} {it('Usage:')} /unban user_id")
        return
    target = int(args[1].strip())
    user_auth.unban_user(target)
    await message.reply(f"{pe(E['check'])} {it('User unbanned!')} ID: {target}")


@router.message(Command("key"))
async def cmd_key(message: types.Message):
    if not user_auth.is_admin(message.from_user.id):
        await message.reply(f"{pe(E['cross'])} {it('Admin only!')}")
        return
    args = message.text.split()
    if len(args) < 3 or not args[1].isdigit() or not args[2].isdigit():
        await message.reply(f"{pe(E['warn'])} {it('Usage:')} /key users days")
        return
    max_users = int(args[1])
    days = int(args[2])
    key = user_auth.generate_key("pkey", max_users, days)
    await message.reply(f"{pe(E['gem'])} {it('Key Generated!')}\n{pe(E['key'])} <code>{key}</code>\n{it(f'{max_users} users | {days} days')}")


@router.message(Command("ckey"))
async def cmd_ckey(message: types.Message):
    if not user_auth.is_admin(message.from_user.id):
        await message.reply(f"{pe(E['cross'])} {it('Admin only!')}")
        return
    args = message.text.split()
    if len(args) < 3 or not args[1].isdigit() or not args[2].isdigit():
        await message.reply(f"{pe(E['warn'])} {it('Usage:')} /ckey users credits")
        return
    max_users = int(args[1])
    credits = int(args[2])
    key = user_auth.generate_key("ckey", max_users, credits=credits)
    await message.reply(f"{pe(E['gem'])} {it('Credits Key Generated!')}\n{pe(E['key'])} <code>{key}</code>\n{it(f'{max_users} users | {credits} credits')}")


@router.message(Command("pkey"))
async def cmd_pkey(message: types.Message):
    if not user_auth.is_admin(message.from_user.id):
        await message.reply(f"{pe(E['cross'])} {it('Admin only!')}")
        return
    args = message.text.split()
    if len(args) < 4 or not args[1].isdigit() or not args[2].isdigit() or not args[3].isdigit():
        await message.reply(f"{pe(E['warn'])} {it('Usage:')} /pkey users days credits")
        return
    max_users = int(args[1])
    days = int(args[2])
    credits = int(args[3])
    key = user_auth.generate_key("pkey", max_users, days, credits)
    await message.reply(f"{pe(E['gem'])} {it('Premium+Credits Key Generated!')}\n{pe(E['key'])} <code>{key}</code>\n{it(f'{max_users} users | {days} days | {credits} credits')}")


@router.message(Command("broad"))
async def cmd_broad(message: types.Message):
    if not user_auth.is_admin(message.from_user.id):
        await message.reply(f"{pe(E['cross'])} {it('Admin only!')}")
        return

    broadcast_text = None
    if message.reply_to_message:
        broadcast_text = message.reply_to_message.text or message.reply_to_message.caption
    else:
        raw = message.text or ""
        cmd_end = len("/broad")
        remaining = raw[cmd_end:].lstrip("\n ")
        broadcast_text = remaining

    if not broadcast_text:
        await message.reply(f"{pe(E['warn'])} {it('Reply to a message or type text after /broad')}")
        return

    all_ids = user_auth.get_all_user_ids()
    status = await message.reply(f"{pe(E['rocket'])} {it('Broadcasting...')} 0/{len(all_ids)}")
    sent = 0
    failed = 0

    for uid in all_ids:
        try:
            await bot.send_message(uid, broadcast_text)
            sent += 1
        except Exception:
            failed += 1
        if (sent + failed) % 50 == 0:
            await safe_edit(status, f"{pe(E['rocket'])} {it('Broadcasting...')} {sent}/{len(all_ids)}")

    await safe_edit(status, f"{pe(E['check'])} {it('Broadcast done!')} Sent: {sent} | Failed: {failed}")


@router.message(Command("imaintain"))
async def cmd_imaintain(message: types.Message):
    if not user_auth.is_owner(message.from_user.id):
        await message.reply(f"{pe(E['cross'])} {it('Owner only!')}")
        return
    global _MAINTENANCE_MODE, _MAINTENANCE_REASON
    args = message.text.split(maxsplit=1)
    reason = args[1] if len(args) > 1 else "Server Maintenance"
    _MAINTENANCE_MODE = True
    _MAINTENANCE_REASON = reason

    # Stop all active sessions
    for sid, session in list(_active_sessions.items()):
        try:
            await bot.send_message(
                session["chat_id"],
                format_maintenance_pause(session["checked"], session["total"], reason),
            )
        except Exception:
            pass

    await message.reply(f"{pe(E['maintenance'])} {it('Maintenance mode ON')}\nReason: {reason}")


@router.message(Command("cmaintain"))
async def cmd_cmaintain(message: types.Message):
    if not user_auth.is_owner(message.from_user.id):
        await message.reply(f"{pe(E['cross'])} {it('Owner only!')}")
        return
    global _MAINTENANCE_MODE, _MAINTENANCE_REASON
    _MAINTENANCE_MODE = False
    _MAINTENANCE_REASON = ""
    await message.reply(f"{pe(E['check'])} {it('Maintenance mode OFF')}\nBot resumed normal operation.")


@router.message(Command("api"))
async def cmd_api(message: types.Message):
    if not user_auth.is_owner(message.from_user.id):
        await message.reply(f"{pe(E['cross'])} {it('Owner only!')}")
        return
    # Placeholder for node status
    await message.reply(f"{pe(E['check'])} {it('API Nodes Status')}\nAll nodes operational.")


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN ENTRY
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))

@router.message(CommandStart())
async def start(message: types.Message):
    await message.reply("👋 Welcome!")

@router.message(Command("help"))
async def help_cmd(message: types.Message):
    await message.reply("📖 Help menu")
