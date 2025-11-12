from __future__ import annotations

from datetime import datetime
from typing import Iterable, Optional

from django.db import migrations, models


def _table_exists(connection, table_name: str) -> bool:
    return table_name in connection.introspection.table_names()


def _normalize_date_key(raw_value: Optional[str]) -> Optional[str]:
    if raw_value is None:
        return None
    value = raw_value.strip()
    if not value:
        return None

    # Try ISO formats and common variants first.
    iso_candidate = value
    if iso_candidate.endswith("Z"):
        iso_candidate = iso_candidate[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(iso_candidate)
        return parsed.date().isoformat()
    except ValueError:
        pass

    # Common date formats that have appeared in historical exports.
    patterns: Iterable[str] = (
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%dT%H:%M",
        "%m/%d/%Y",
        "%m-%d-%Y",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%m/%d/%Y %H:%M:%S",
        "%m-%d-%Y %H:%M:%S",
    )
    for pattern in patterns:
        try:
            parsed = datetime.strptime(value, pattern)
            return parsed.date().isoformat()
        except ValueError:
            continue

    if len(value) == 8 and value.isdigit():
        try:
            parsed = datetime.strptime(value, "%Y%m%d")
            return parsed.date().isoformat()
        except ValueError:
            pass

    # As a last resort keep the trimmed value so data is not discarded.
    return value


def backup_and_rename_legacy(apps, schema_editor):
    connection = schema_editor.connection
    if not _table_exists(connection, "signups"):
        return

    backup_table = "signups_pre_migration_backup"
    legacy_table = "signups_legacy"
    source_table = "signups"
    qn = schema_editor.quote_name

    with connection.cursor() as cursor:
        cursor.execute(f"DROP TABLE IF EXISTS {qn(backup_table)}")
        cursor.execute(
            f"CREATE TABLE {qn(backup_table)} AS SELECT * FROM {qn(source_table)}"
        )
        cursor.execute(
            f"ALTER TABLE {qn(source_table)} RENAME TO {qn(legacy_table)}"
        )


def restore_legacy_table(apps, schema_editor):
    connection = schema_editor.connection
    qn = schema_editor.quote_name

    if _table_exists(connection, "signups_legacy"):
        with connection.cursor() as cursor:
            cursor.execute(
                f"ALTER TABLE {qn('signups_legacy')} RENAME TO {qn('signups')}"
            )
    elif _table_exists(connection, "signups_pre_migration_backup") and not _table_exists(
        connection, "signups"
    ):
        with connection.cursor() as cursor:
            cursor.execute(
                f"ALTER TABLE {qn('signups_pre_migration_backup')} RENAME TO {qn('signups')}"
            )


def copy_and_normalize_from_legacy(apps, schema_editor):
    connection = schema_editor.connection
    if not _table_exists(connection, "signups_legacy"):
        return

    Signup = apps.get_model("calendar_app", "Signup")
    qn = schema_editor.quote_name
    db_alias = connection.alias

    with connection.cursor() as cursor:
        cursor.execute(
            f"SELECT date_key, name, phone FROM {qn('signups_legacy')} ORDER BY date_key"
        )
        rows = cursor.fetchall()

    seen_keys = set()
    manager = Signup.objects.using(db_alias)
    for date_key, name, phone in rows:
        normalized_key = _normalize_date_key(date_key)
        if not normalized_key or normalized_key in seen_keys:
            continue
        seen_keys.add(normalized_key)
        manager.update_or_create(
            date_key=normalized_key,
            defaults={"name": name or "", "phone": phone or ""},
        )

    with connection.cursor() as cursor:
        cursor.execute(f"SELECT COUNT(*) FROM {qn('signups_legacy')}")
        legacy_count = cursor.fetchone()[0]
    new_count = manager.count()
    if legacy_count != new_count:
        # Keep the legacy table so that data can be reviewed manually if counts mismatch.
        return

    # When the copy succeeds and we have a snapshot, remove the legacy table to avoid
    # dual sources of truth. The backup created during the rename is preserved so the
    # data can be restored if needed.
    if _table_exists(connection, "signups_pre_migration_backup"):
        with connection.cursor() as cursor:
            cursor.execute(f"DROP TABLE IF EXISTS {qn('signups_legacy')}")


def reverse_copy_into_legacy(apps, schema_editor):
    connection = schema_editor.connection
    Signup = apps.get_model("calendar_app", "Signup")
    qn = schema_editor.quote_name
    db_alias = connection.alias

    if not _table_exists(connection, "signups_legacy"):
        if _table_exists(connection, "signups_pre_migration_backup"):
            with connection.cursor() as cursor:
                cursor.execute(
                    f"ALTER TABLE {qn('signups_pre_migration_backup')} RENAME TO {qn('signups_legacy')}"
                )
        else:
            return

    placeholder = "?" if connection.vendor == "sqlite" else "%s"

    with connection.cursor() as cursor:
        cursor.execute(f"DELETE FROM {qn('signups_legacy')}")
        inserts = [
            (signup.date_key, signup.name, signup.phone)
            for signup in Signup.objects.using(db_alias).all().order_by("date_key")
        ]
        if inserts:
            # Use executemany for portability.
            cursor.executemany(
                f"INSERT INTO {qn('signups_legacy')} (date_key, name, phone) VALUES ({placeholder}, {placeholder}, {placeholder})",
                inserts,
            )


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.RunPython(backup_and_rename_legacy, restore_legacy_table),
        migrations.CreateModel(
            name="Signup",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date_key", models.CharField(max_length=20, unique=True)),
                ("name", models.CharField(max_length=255)),
                ("phone", models.CharField(max_length=50)),
            ],
            options={
                "db_table": "signups",
            },
        ),
        migrations.RunPython(copy_and_normalize_from_legacy, reverse_copy_into_legacy),
    ]
