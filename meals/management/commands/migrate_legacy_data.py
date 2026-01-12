from django.core.management.base import BaseCommand
from django.db import connections, transaction
from meals.models import MealSignUp
from datetime import datetime


class Command(BaseCommand):
    help = "Migrate data from legacy signups table to MealSignUp model"

    def add_arguments(self, parser):
        parser.add_argument(
            "--wipe",
            action="store_true",
            help="Delete existing MealSignUp records before importing",
        )

    def handle(self, *args, **options):
        legacy_conn = connections["legacy"]

        with legacy_conn.cursor() as cursor:
            cursor.execute("SELECT date_key, name, phone FROM signups ORDER BY date_key")
            rows = cursor.fetchall()

        self.stdout.write(f"Found {len(rows)} legacy rows")

        created = 0
        updated = 0
        skipped = 0

        with transaction.atomic():
            if options["wipe"]:
                self.stdout.write("Wiping existing MealSignUp records")
                MealSignUp.objects.all().delete()

            for date_key, name, phone in rows:
                try:
                    # This handles both 2025-7-23 and 2025-07-23
                    date_obj = datetime.strptime(date_key.strip(), "%Y-%m-%d").date()
                except ValueError:
                    skipped += 1
                    self.stderr.write(f"Skipping invalid date_key: {date_key!r}")
                    continue

                obj, was_created = MealSignUp.objects.update_or_create(
                    date=date_obj,
                    defaults={
                        "name": (name or "").strip(),
                        "phone": (phone or "").strip(),
                    },
                )

                if was_created:
                    created += 1
                else:
                    updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Import complete — created: {created}, updated: {updated}, skipped: {skipped}"
            )
        )
