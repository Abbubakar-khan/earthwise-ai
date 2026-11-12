"""Validated multi-format uploads backed by persistent PostgreSQL storage.

Uploaded files are parsed in memory. Records are stored as JSONB and scoped to a
high-entropy workspace recovery key (only its SHA-256 hash is stored).
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import secrets
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

MAX_UPLOAD_BYTES = 15 * 1024 * 1024
MAX_ROWS = 100_000
MAX_COLUMNS = 100
SUPPORTED_FORMATS = {".csv", ".xlsx", ".xls", ".xlsm", ".json"}


class UploadValidationError(ValueError):
    """The uploaded file is not a supported, safe tabular dataset."""


class DatasetStorageError(RuntimeError):
    """Persistent dataset storage is unavailable or rejected the operation."""


def create_workspace_token() -> str:
    """Create a high-entropy bearer key for a private user workspace."""
    return "ew1_" + secrets.token_urlsafe(32)


def validate_workspace_token(token: str) -> bool:
    return isinstance(token, str) and token.startswith("ew1_") and 40 <= len(token) <= 100


def _workspace_hash(token: str) -> str:
    if not validate_workspace_token(token):
        raise ValueError("Invalid workspace recovery key.")
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def database_url() -> str:
    value = os.getenv("EARTHWISE_DATABASE_URL", "") or os.getenv("DATABASE_URL", "")
    if value:
        return value.strip()
    try:
        return str(st.secrets.get("EARTHWISE_DATABASE_URL", "") or "").strip()
    except Exception:
        return ""


def database_configured() -> bool:
    return bool(database_url())


def _connect():
    url = database_url()
    if not url:
        raise DatasetStorageError(
            "Persistent storage is not configured. Add EARTHWISE_DATABASE_URL in Streamlit app Secrets."
        )
    try:
        import psycopg
        return psycopg.connect(url, connect_timeout=10)
    except ImportError as exc:
        raise DatasetStorageError(
            "PostgreSQL support is not installed. Install the project requirements and restart the app."
        ) from exc
    except Exception as exc:
        raise DatasetStorageError(
            "Could not connect to persistent storage. Check the PostgreSQL connection string and database availability."
        ) from exc


def _ensure_table(connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS earthwise_user_datasets (
            id UUID PRIMARY KEY,
            workspace_hash CHAR(64) NOT NULL,
            filename TEXT NOT NULL,
            file_format TEXT NOT NULL,
            row_count INTEGER NOT NULL,
            column_names JSONB NOT NULL,
            records JSONB NOT NULL,
            uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS earthwise_user_datasets_workspace_idx
        ON earthwise_user_datasets (workspace_hash, uploaded_at DESC)
        """
    )


def parse_uploaded_file(filename: str, content: bytes) -> pd.DataFrame:
    """Parse CSV, Excel, or JSON bytes into a validated tabular DataFrame."""
    suffix = Path(filename or "").suffix.lower()
    if suffix not in SUPPORTED_FORMATS:
        raise UploadValidationError(
            "Unsupported file type. Upload CSV, XLSX, XLS, XLSM, or JSON."
        )
    if not isinstance(content, (bytes, bytearray)) or not content:
        raise UploadValidationError("The uploaded file is empty.")
    if len(content) > MAX_UPLOAD_BYTES:
        raise UploadValidationError("File exceeds the 15 MB upload limit.")

    try:
        if suffix == ".csv":
            frame = pd.read_csv(io.BytesIO(content), encoding="utf-8-sig", low_memory=False)
        elif suffix in {".xlsx", ".xls", ".xlsm"}:
            frame = pd.read_excel(io.BytesIO(content), sheet_name=0)
        else:
            payload = json.loads(content.decode("utf-8-sig"))
            if isinstance(payload, dict):
                if isinstance(payload.get("records"), list):
                    payload = payload["records"]
                elif isinstance(payload.get("data"), list):
                    payload = payload["data"]
                else:
                    payload = [payload]
            if not isinstance(payload, list) or not payload:
                raise UploadValidationError(
                    "JSON must contain an array of row objects, or a 'data'/'records' array."
                )
            if not all(isinstance(row, dict) for row in payload):
                raise UploadValidationError("Each JSON row must be an object with named fields.")
            frame = pd.DataFrame(payload)
    except UploadValidationError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, pd.errors.ParserError,
            ValueError, TypeError, ImportError) as exc:
        raise UploadValidationError(
            "The file could not be parsed. Check its encoding, structure, and Excel format."
        ) from exc
    except Exception as exc:
        raise UploadValidationError(
            "The file could not be read. Check that it is a valid, uncorrupted tabular file."
        ) from exc

    if frame.empty or len(frame.columns) == 0:
        raise UploadValidationError("The file contains no tabular records.")
    if len(frame.columns) > MAX_COLUMNS:
        raise UploadValidationError(f"Too many columns. The limit is {MAX_COLUMNS}.")
    if len(frame) > MAX_ROWS:
        raise UploadValidationError(f"Too many rows. The limit is {MAX_ROWS:,}.")

    names = [str(column).strip() for column in frame.columns]
    if any(not name for name in names):
        raise UploadValidationError("Every column must have a non-empty name.")
    normalized = [name.casefold() for name in names]
    if len(set(normalized)) != len(normalized):
        raise UploadValidationError("Column names must be unique, ignoring letter case.")
    frame.columns = names
    frame = frame.dropna(how="all").reset_index(drop=True)
    if frame.empty:
        raise UploadValidationError("The file contains no non-empty data rows.")
    return frame


def save_dataset(token: str, filename: str, frame: pd.DataFrame) -> str:
    """Persist a validated frame and return its dataset UUID."""
    workspace_hash = _workspace_hash(token)
    suffix = Path(filename).suffix.lower()
    records = json.loads(frame.to_json(orient="records", date_format="iso", force_ascii=False))
    dataset_id = secrets.token_hex(16)
    try:
        with _connect() as connection:
            _ensure_table(connection)
            row = connection.execute(
                """
                INSERT INTO earthwise_user_datasets
                    (id, workspace_hash, filename, file_format, row_count, column_names, records)
                VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s::jsonb)
                RETURNING id::text
                """,
                (
                    dataset_id,
                    workspace_hash,
                    Path(filename).name[:255],
                    suffix.lstrip("."),
                    int(len(frame)),
                    json.dumps(list(frame.columns), ensure_ascii=False),
                    json.dumps(records, ensure_ascii=False),
                ),
            ).fetchone()
            return str(row[0])
    except DatasetStorageError:
        raise
    except Exception as exc:
        raise DatasetStorageError(
            "The dataset could not be saved. Check database permissions, storage limits, and connection health."
        ) from exc


def list_datasets(token: str) -> list[dict[str, Any]]:
    workspace_hash = _workspace_hash(token)
    try:
        with _connect() as connection:
            _ensure_table(connection)
            rows = connection.execute(
                """
                SELECT id::text, filename, file_format, row_count, uploaded_at::text
                FROM earthwise_user_datasets
                WHERE workspace_hash = %s
                ORDER BY uploaded_at DESC
                """,
                (workspace_hash,),
            ).fetchall()
        return [
            {"id": row[0], "filename": row[1], "format": row[2].upper(),
             "rows": int(row[3]), "uploaded_at": row[4]}
            for row in rows
        ]
    except DatasetStorageError:
        raise
    except Exception as exc:
        raise DatasetStorageError(
            "Saved datasets could not be loaded. Check the database connection and permissions."
        ) from exc


def load_dataset(token: str, dataset_id: str) -> pd.DataFrame:
    workspace_hash = _workspace_hash(token)
    try:
        with _connect() as connection:
            _ensure_table(connection)
            row = connection.execute(
                """
                SELECT column_names, records
                FROM earthwise_user_datasets
                WHERE workspace_hash = %s AND id = %s::uuid
                """,
                (workspace_hash, dataset_id),
            ).fetchone()
        if row is None:
            raise DatasetStorageError("That dataset was not found in this workspace.")
        records = row[1]
        if isinstance(records, str):
            records = json.loads(records)
        frame = pd.DataFrame(records, columns=row[0])
        return frame
    except DatasetStorageError:
        raise
    except Exception as exc:
        raise DatasetStorageError(
            "The selected dataset could not be opened. Check the stored record and database connection."
        ) from exc


def delete_dataset(token: str, dataset_id: str) -> bool:
    workspace_hash = _workspace_hash(token)
    try:
        with _connect() as connection:
            _ensure_table(connection)
            cursor = connection.execute(
                """
                DELETE FROM earthwise_user_datasets
                WHERE workspace_hash = %s AND id = %s::uuid
                """,
                (workspace_hash, dataset_id),
            )
            return cursor.rowcount > 0
    except DatasetStorageError:
        raise
    except Exception as exc:
        raise DatasetStorageError(
            "The dataset could not be deleted. Check the database connection."
        ) from exc
