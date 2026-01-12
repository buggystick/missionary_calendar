import csv
from datetime import datetime
from django.core.management.base import BaseCommand
from django.db import transaction
from meals.models import MealSignUp

class Command(BaseCommand):
    help = "Import signups from signups.csv"

    def add_arguments(self, parser):
        parser.add_argument(
            "--wipe",
            action="store_true",
            help="Delete existing MealSignUp records before importing",
        )
        parser.add_argument(
            "--file",
            default="signups.csv",
            help="Path to the signups.csv file",
        )

    def handle(self, *args, **options):
        file_path = options["file"]
        
        try:
            with open(file_path, mode="r", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)
                rows = list(reader)
        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f"File not found: {file_path}"))
            return

        self.stdout.write(f"Found {len(rows)} rows in CSV")

        created = 0
        updated = 0
        skipped = 0

        with transaction.atomic():
            if options["wipe"]:
                self.stdout.write("Wiping existing MealSignUp records")
                MealSignUp.objects.all().delete()

            for row in rows:
                date_key = row.get("date_key")
                name = row.get("name", "")
                phone = row.get("phone", "")

                if not date_key:
                    skipped += 1
                    continue

                try:
                    # date_key is in YYYY-M-D or YYYY-MM-DD format
                    date_obj = datetime.strptime(date_key.strip(), "%Y-%m-%d").date()
                except ValueError:
                    skipped += 1
                    self.stderr.write(f"Skipping invalid date_key: {date_key!r}")
                    continue

                is_unavailable = False
                name_stripped = name.strip()
                if name_stripped.lower() in ["unavailable", "not available"]:
                    is_unavailable = True

                obj, was_created = MealSignUp.objects.update_or_create(
                    date=date_obj,
                    defaults={
                        "name": name_stripped,
                        "phone": phone.strip(),
                        "is_unavailable": is_unavailable,
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
