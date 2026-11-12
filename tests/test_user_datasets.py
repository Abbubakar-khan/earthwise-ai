import io
import json

import pandas as pd
import pytest

from src.user_datasets import (
    DatasetStorageError,
    UploadValidationError,
    create_workspace_token,
    database_configured,
    load_dataset,
    parse_uploaded_file,
    validate_workspace_token,
)


def test_parse_csv_and_clean_empty_rows():
    frame = parse_uploaded_file(
        "climate.csv",
        b"date,temperature,rainfall\n2025-01-01,18.5,0\n,,\n2025-01-02,19,2.5\n",
    )
    assert list(frame.columns) == ["date", "temperature", "rainfall"]
    assert len(frame) == 2
    assert frame.loc[0, "temperature"] == 18.5


def test_parse_json_records_and_data_wrapper():
    payload = {"data": [{"city": "Peshawar", "temperature": 21}, {"city": "Lahore", "temperature": 29}]}
    frame = parse_uploaded_file("cities.json", json.dumps(payload).encode())
    assert list(frame["city"]) == ["Peshawar", "Lahore"]
    assert len(frame) == 2


def test_parse_excel_xlsx():
    buffer = io.BytesIO()
    pd.DataFrame({"date": ["2025-01-01"], "temperature": [22.4]}).to_excel(
        buffer, index=False, engine="openpyxl"
    )
    frame = parse_uploaded_file("weather.xlsx", buffer.getvalue())
    assert frame.loc[0, "temperature"] == 22.4


def test_reject_unsupported_file_type():
    with pytest.raises(UploadValidationError, match="Unsupported"):
        parse_uploaded_file("archive.zip", b"not a table")


def test_reject_empty_and_oversized_files():
    with pytest.raises(UploadValidationError, match="empty"):
        parse_uploaded_file("empty.csv", b"")
    with pytest.raises(UploadValidationError, match="15 MB"):
        parse_uploaded_file("large.csv", b"x" * (15 * 1024 * 1024 + 1))


def test_reject_duplicate_column_names_case_insensitive():
    with pytest.raises(UploadValidationError, match="unique"):
        parse_uploaded_file("duplicate.json", b'[{"Temperature": 1, "temperature": 2}]')


def test_reject_non_object_json_rows():
    with pytest.raises(UploadValidationError, match="row must be an object"):
        parse_uploaded_file("bad.json", b'[1, 2, 3]')


def test_workspace_recovery_key_is_high_entropy_and_valid():
    token = create_workspace_token()
    assert token.startswith("ew1_")
    assert validate_workspace_token(token)
    assert not validate_workspace_token("not-a-key")


def test_load_requires_valid_workspace_key():
    with pytest.raises(ValueError, match="Invalid workspace"):
        load_dataset("invalid", "00000000-0000-0000-0000-000000000000")


def test_database_configuration_is_explicit(monkeypatch):
    monkeypatch.delenv("EARTHWISE_DATABASE_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert database_configured() is False
    with pytest.raises(DatasetStorageError, match="not configured"):
        from src.user_datasets import list_datasets
        list_datasets(create_workspace_token())

def test_parse_json_column_oriented_object():
    frame = parse_uploaded_file(
        "series.json",
        b'{"city": ["Peshawar", "Lahore"], "temperature": [20, 29]}',
    )
    assert len(frame) == 2
    assert list(frame["city"]) == ["Peshawar", "Lahore"]


def test_reject_duplicate_csv_headers():
    with pytest.raises(UploadValidationError, match="unique"):
        parse_uploaded_file("duplicate.csv", b"Temperature,temperature\n20,21\n")
