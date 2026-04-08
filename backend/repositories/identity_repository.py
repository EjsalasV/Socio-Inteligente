from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from backend.repositories.supabase_memory import store as supabase_store

ROOT = Path(__file__).resolve().parents[2]
DATA_SECURITY = ROOT / "data" / "security"
USERS_FILE = DATA_SECURITY / "users.yaml"
USER_CLIENTES_FILE = DATA_SECURITY / "user_clientes.yaml"
USER_PREFERENCES_FILE = DATA_SECURITY / "user_preferences.yaml"
PREFERENCES_VERSION = "v1.2.1"

VALID_LEARNING_ROLES = {"junior", "semi", "senior", "socio"}
VALID_SYSTEM_ROLES = {"admin", "socio", "manager", "senior", "semi", "junior", "auditor"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slug(raw: str) -> str:
    out = "".join(ch if ch.isalnum() else "_" for ch in str(raw or "").strip().lower())
    while "__" in out:
        out = out.replace("__", "_")
    return out.strip("_")


def _stable_unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        key = str(item or "").strip()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(key)
    return out


def _hash_password(password: str, *, iterations: int = 200_000) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), iterations).hex()
    return f"pbkdf2_sha256${iterations}${salt}${digest}"


def verify_password(password: str, password_hash: str) -> bool:
    raw = str(password_hash or "").strip()
    if not raw:
        return False
    if raw.startswith("pbkdf2_sha256$"):
        try:
            _algo, iterations_s, salt, expected = raw.split("$", 3)
            iterations = int(iterations_s)
            digest = hashlib.pbkdf2_hmac(
                "sha256",
                str(password or "").encode("utf-8"),
                bytes.fromhex(salt),
                iterations,
            ).hex()
            return hmac.compare_digest(digest, expected)
        except Exception:
            return False
    # Legacy/plain fallback (keeps compatibility if old data was stored un-hashed).
    return hmac.compare_digest(str(password or ""), raw)


def _normalize_learning_role(value: Any) -> str:
    role = str(value or "").strip().lower()
    return role if role in VALID_LEARNING_ROLES else "semi"


def _normalize_onboarding_ui(raw: Any) -> dict[str, Any]:
    data = raw if isinstance(raw, dict) else {}
    visited = data.get("visited_modules_ui") if isinstance(data.get("visited_modules_ui"), list) else []
    return {
        "welcome_seen": bool(data.get("welcome_seen", False)),
        "dismissed": bool(data.get("dismissed", False)),
        "visited_modules_ui": _stable_unique([str(x).strip() for x in visited if str(x).strip()]),
    }


def default_user_preferences() -> dict[str, Any]:
    return {
        "learning_role": "semi",
        "tour_completed_modules": [],
        "tour_welcome_seen": False,
        "onboarding_ui": {
            "welcome_seen": False,
            "dismissed": False,
            "visited_modules_ui": [],
        },
        "preferences_version": PREFERENCES_VERSION,
    }


def _normalize_preferences(raw: Any) -> dict[str, Any]:
    data = raw if isinstance(raw, dict) else {}
    defaults = default_user_preferences()
    modules = data.get("tour_completed_modules") if isinstance(data.get("tour_completed_modules"), list) else []
    out = {
        "learning_role": _normalize_learning_role(data.get("learning_role")),
        "tour_completed_modules": _stable_unique([str(x).strip() for x in modules if str(x).strip()]),
        "tour_welcome_seen": bool(data.get("tour_welcome_seen", defaults["tour_welcome_seen"])),
        "onboarding_ui": _normalize_onboarding_ui(data.get("onboarding_ui")),
        "preferences_version": str(data.get("preferences_version") or defaults["preferences_version"]),
    }
    return out


def _merge_preferences(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    merged = _normalize_preferences(base)
    if "learning_role" in patch:
        merged["learning_role"] = _normalize_learning_role(patch.get("learning_role"))
    if "tour_completed_modules" in patch:
        raw_modules = patch.get("tour_completed_modules")
        modules = raw_modules if isinstance(raw_modules, list) else []
        merged["tour_completed_modules"] = _stable_unique([str(x).strip() for x in modules if str(x).strip()])
    if "tour_welcome_seen" in patch:
        merged["tour_welcome_seen"] = bool(patch.get("tour_welcome_seen"))
    if "onboarding_ui" in patch:
        merged["onboarding_ui"] = _normalize_onboarding_ui(
            {
                **(merged.get("onboarding_ui") if isinstance(merged.get("onboarding_ui"), dict) else {}),
                **(patch.get("onboarding_ui") if isinstance(patch.get("onboarding_ui"), dict) else {}),
            }
        )
    if "preferences_version" in patch:
        merged["preferences_version"] = str(patch.get("preferences_version") or PREFERENCES_VERSION)
    return _normalize_preferences(merged)


class IdentityRepository:
    def __init__(self) -> None:
        self.security_dir = DATA_SECURITY
        self.users_file = USERS_FILE
        self.user_clientes_file = USER_CLIENTES_FILE
        self.user_preferences_file = USER_PREFERENCES_FILE

    def _read_yaml(self, path: Path, default: Any) -> Any:
        if not path.exists():
            return default
        try:
            loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception:
            return default
        return loaded if loaded is not None else default

    def _write_yaml(self, path: Path, payload: Any) -> None:
        self.security_dir.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")

    def _local_users(self) -> list[dict[str, Any]]:
        data = self._read_yaml(self.users_file, [])
        if not isinstance(data, list):
            return []
        out: list[dict[str, Any]] = []
        for row in data:
            if not isinstance(row, dict):
                continue
            user_id = str(row.get("user_id") or "").strip()
            username = str(row.get("username") or "").strip()
            if not user_id or not username:
                continue
            out.append(
                {
                    "user_id": user_id,
                    "username": username,
                    "display_name": str(row.get("display_name") or username).strip(),
                    "password_hash": str(row.get("password_hash") or "").strip(),
                    "role": str(row.get("role") or "auditor").strip().lower(),
                    "active": bool(row.get("active", True)),
                    "created_at": str(row.get("created_at") or _now_iso()),
                    "updated_at": str(row.get("updated_at") or _now_iso()),
                }
            )
        return out

    def _save_local_users(self, users: list[dict[str, Any]]) -> None:
        self._write_yaml(self.users_file, users)

    def _local_assignments(self) -> list[dict[str, str]]:
        data = self._read_yaml(self.user_clientes_file, [])
        if not isinstance(data, list):
            return []
        out: list[dict[str, str]] = []
        for row in data:
            if not isinstance(row, dict):
                continue
            user_id = str(row.get("user_id") or "").strip()
            cliente_id = str(row.get("cliente_id") or "").strip()
            if not user_id or not cliente_id:
                continue
            out.append({"user_id": user_id, "cliente_id": cliente_id})
        return out

    def _save_local_assignments(self, rows: list[dict[str, str]]) -> None:
        self._write_yaml(self.user_clientes_file, rows)

    def _local_preferences(self) -> dict[str, Any]:
        data = self._read_yaml(self.user_preferences_file, {})
        return data if isinstance(data, dict) else {}

    def _save_local_preferences(self, payload: dict[str, Any]) -> None:
        self._write_yaml(self.user_preferences_file, payload)

    def _supa_fetch_user_by_username(self, username: str) -> dict[str, Any] | None:
        if not supabase_store.is_configured():
            return None
        rows = supabase_store.fetch_rows(
            "users",
            filters={"username": username},
            select="user_id,username,display_name,password_hash,role,active,created_at,updated_at",
        )
        if not rows:
            return None
        row = rows[0] if isinstance(rows[0], dict) else {}
        return row if row else None

    def _supa_fetch_user_by_id(self, user_id: str) -> dict[str, Any] | None:
        if not supabase_store.is_configured():
            return None
        rows = supabase_store.fetch_rows(
            "users",
            filters={"user_id": user_id},
            select="user_id,username,display_name,password_hash,role,active,created_at,updated_at",
        )
        if not rows:
            return None
        row = rows[0] if isinstance(rows[0], dict) else {}
        return row if row else None

    def _supa_list_users(self) -> list[dict[str, Any]]:
        if not supabase_store.is_configured():
            return []
        rows = supabase_store.fetch_rows(
            "users",
            select="user_id,username,display_name,role,active,created_at,updated_at",
        )
        return [r for r in rows if isinstance(r, dict)]

    def _supa_get_assignments(self, user_id: str) -> list[str]:
        if not supabase_store.is_configured():
            return []
        rows = supabase_store.fetch_rows("user_clientes", filters={"user_id": user_id}, select="cliente_id")
        out: list[str] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            cid = str(row.get("cliente_id") or "").strip()
            if cid:
                out.append(cid)
        return _stable_unique(out)

    def _supa_set_assignments(self, user_id: str, cliente_ids: list[str]) -> None:
        if not supabase_store.is_configured():
            return
        supabase_store.delete_where("user_clientes", {"user_id": user_id})
        for cid in cliente_ids:
            supabase_store.upsert_row(
                "user_clientes",
                {"user_id": user_id, "cliente_id": cid},
                on_conflict="user_id,cliente_id",
            )

    def _supa_get_preferences(self, user_id: str) -> dict[str, Any] | None:
        if not supabase_store.is_configured():
            return None
        payload = supabase_store.fetch_single_json(
            "user_preferences",
            {"user_id": user_id},
            "preferences_json",
        )
        return payload if isinstance(payload, dict) else None

    def _supa_upsert_user(self, payload: dict[str, Any]) -> None:
        if not supabase_store.is_configured():
            return
        supabase_store.upsert_row("users", payload, on_conflict="user_id")

    def _supa_upsert_preferences(self, user_id: str, prefs: dict[str, Any]) -> None:
        if not supabase_store.is_configured():
            return
        supabase_store.upsert_row(
            "user_preferences",
            {
                "user_id": user_id,
                "preferences_json": prefs,
                "schema_version": PREFERENCES_VERSION,
                "updated_at": _now_iso(),
            },
            on_conflict="user_id",
        )

    def get_user_by_username(self, username: str) -> dict[str, Any] | None:
        uname = str(username or "").strip()
        if not uname:
            return None
        row = self._supa_fetch_user_by_username(uname)
        if isinstance(row, dict) and row:
            return row
        for user in self._local_users():
            if str(user.get("username") or "").strip() == uname:
                return user
        return None

    def get_user_by_id(self, user_id: str) -> dict[str, Any] | None:
        uid = str(user_id or "").strip()
        if not uid:
            return None
        row = self._supa_fetch_user_by_id(uid)
        if isinstance(row, dict) and row:
            return row
        for user in self._local_users():
            if str(user.get("user_id") or "").strip() == uid:
                return user
        return None

    def list_users(self) -> list[dict[str, Any]]:
        remote = self._supa_list_users()
        if remote:
            return remote
        local = self._local_users()
        return [
            {
                "user_id": str(row.get("user_id") or "").strip(),
                "username": str(row.get("username") or "").strip(),
                "display_name": str(row.get("display_name") or row.get("username") or "").strip(),
                "role": str(row.get("role") or "auditor").strip().lower(),
                "active": bool(row.get("active", True)),
                "created_at": str(row.get("created_at") or ""),
                "updated_at": str(row.get("updated_at") or ""),
            }
            for row in local
        ]

    def get_user_clientes(self, user_id: str) -> list[str]:
        uid = str(user_id or "").strip()
        if not uid:
            return []
        remote = self._supa_get_assignments(uid)
        if remote:
            return remote
        local = self._local_assignments()
        out = [row["cliente_id"] for row in local if row.get("user_id") == uid]
        return _stable_unique(out)

    def set_user_clientes(self, user_id: str, cliente_ids: list[str]) -> list[str]:
        uid = str(user_id or "").strip()
        cleaned = _stable_unique([str(cid or "").strip() for cid in cliente_ids if str(cid or "").strip()])
        self._supa_set_assignments(uid, cleaned)

        rows = [row for row in self._local_assignments() if str(row.get("user_id") or "") != uid]
        rows.extend([{"user_id": uid, "cliente_id": cid} for cid in cleaned])
        self._save_local_assignments(rows)
        return cleaned

    def list_members_by_cliente(self, cliente_id: str) -> list[dict[str, Any]]:
        cid = str(cliente_id or "").strip()
        if not cid:
            return []
        users = {str(u.get("user_id") or ""): u for u in self.list_users()}

        member_ids: list[str] = []
        if supabase_store.is_configured():
            rows = supabase_store.fetch_rows("user_clientes", filters={"cliente_id": cid}, select="user_id")
            member_ids.extend([str(r.get("user_id") or "").strip() for r in rows if isinstance(r, dict)])
        if not member_ids:
            member_ids.extend(
                [str(row.get("user_id") or "").strip() for row in self._local_assignments() if row.get("cliente_id") == cid]
            )

        out: list[dict[str, Any]] = []
        for uid in _stable_unique(member_ids):
            if not uid:
                continue
            user = users.get(uid) or self.get_user_by_id(uid)
            if not isinstance(user, dict):
                continue
            out.append(
                {
                    "user_id": uid,
                    "username": str(user.get("username") or "").strip(),
                    "display_name": str(user.get("display_name") or user.get("username") or "").strip(),
                    "role": str(user.get("role") or "auditor").strip().lower(),
                    "active": bool(user.get("active", True)),
                }
            )
        return out

    def create_user(
        self,
        *,
        username: str,
        password: str,
        role: str,
        display_name: str = "",
        active: bool = True,
        user_id: str = "",
    ) -> dict[str, Any]:
        uname = str(username or "").strip()
        if not uname:
            raise ValueError("username es obligatorio")
        pass_raw = str(password or "")
        if not pass_raw.strip():
            raise ValueError("password es obligatorio")
        if self.get_user_by_username(uname):
            raise ValueError("username ya existe")
        role_n = str(role or "auditor").strip().lower()
        if role_n not in VALID_SYSTEM_ROLES:
            role_n = "auditor"
        uid = str(user_id or "").strip() or _slug(uname) or f"user_{secrets.token_hex(4)}"
        if self.get_user_by_id(uid):
            uid = f"{uid}_{secrets.token_hex(2)}"
        now = _now_iso()
        payload = {
            "user_id": uid,
            "username": uname,
            "display_name": str(display_name or uname).strip(),
            "password_hash": _hash_password(pass_raw),
            "role": role_n,
            "active": bool(active),
            "created_at": now,
            "updated_at": now,
        }
        self._supa_upsert_user(payload)
        users = self._local_users()
        users.append(payload)
        self._save_local_users(users)
        return payload

    def update_user(self, user_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        uid = str(user_id or "").strip()
        existing = self.get_user_by_id(uid)
        if not existing:
            raise ValueError("user_id no encontrado")
        updated = dict(existing)
        if "display_name" in patch:
            updated["display_name"] = str(patch.get("display_name") or updated.get("username") or "").strip()
        if "role" in patch:
            role_n = str(patch.get("role") or "").strip().lower()
            if role_n in VALID_SYSTEM_ROLES:
                updated["role"] = role_n
        if "active" in patch:
            updated["active"] = bool(patch.get("active"))
        if "password" in patch and str(patch.get("password") or "").strip():
            updated["password_hash"] = _hash_password(str(patch.get("password")))
        updated["updated_at"] = _now_iso()

        self._supa_upsert_user(updated)
        users = self._local_users()
        next_users: list[dict[str, Any]] = []
        found = False
        for row in users:
            if str(row.get("user_id") or "") == uid:
                next_users.append(updated)
                found = True
            else:
                next_users.append(row)
        if not found:
            next_users.append(updated)
        self._save_local_users(next_users)
        return updated

    def authenticate(self, username: str, password: str) -> dict[str, Any] | None:
        user = self.get_user_by_username(username)
        if not isinstance(user, dict):
            return None
        if not bool(user.get("active", True)):
            return None
        if verify_password(str(password or ""), str(user.get("password_hash") or "")):
            return user
        return None

    def ensure_legacy_admin(self) -> dict[str, Any]:
        admin_user = (
            os.getenv("ADMIN_USERNAME")
            or os.getenv("SOCIO_ADMIN_USER")
            or "joaosalas123@gmail.com"
        ).strip()
        admin_pass = (
            os.getenv("ADMIN_PASSWORD")
            or os.getenv("SOCIO_ADMIN_PASSWORD")
            or "1234"
        ).strip()

        current = self.get_user_by_username(admin_user)
        if isinstance(current, dict):
            return current

        created = self.create_user(
            username=admin_user,
            password=admin_pass,
            role="admin",
            display_name=admin_user,
            active=True,
            user_id="admin_legacy",
        )

        raw_allowed = str(os.getenv("ALLOWED_CLIENTES", "*") or "*").strip()
        if raw_allowed == "*":
            self.set_user_clientes(created["user_id"], ["*"])
        else:
            allowed = [x.strip() for x in raw_allowed.split(",") if x.strip()]
            self.set_user_clientes(created["user_id"], allowed)
        return created

    def get_preferences(self, user_id: str) -> dict[str, Any]:
        uid = str(user_id or "").strip()
        if not uid:
            return default_user_preferences()
        remote = self._supa_get_preferences(uid)
        if isinstance(remote, dict) and remote:
            return _normalize_preferences(remote)

        local = self._local_preferences()
        value = local.get(uid) if isinstance(local.get(uid), dict) else {}
        return _normalize_preferences(value)

    def patch_preferences(self, user_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        uid = str(user_id or "").strip()
        if not uid:
            raise ValueError("user_id es obligatorio para preferencias")
        current = self.get_preferences(uid)
        merged = _merge_preferences(current, patch if isinstance(patch, dict) else {})
        merged["preferences_version"] = PREFERENCES_VERSION
        self._supa_upsert_preferences(uid, merged)

        local = self._local_preferences()
        local[uid] = merged
        self._save_local_preferences(local)
        return merged


store = IdentityRepository()
