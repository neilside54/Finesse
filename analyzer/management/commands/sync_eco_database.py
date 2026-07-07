"""
Management-команда для синхронизации локальной ECO-базы дебютов
с github.com/lichess-org/chess-openings.

Использование:
    python manage.py sync_eco_database

Зачем команда, а не ручное скачивание:
    - база на upstream обновляется (новые варианты, исправления),
      команду можно повторно запускать (например, по расписанию/в CI)
      без ручной склейки файлов;
    - результат — один файл analyzer/data/eco_openings.tsv в том же
      формате, который уже понимает EcoOpeningBook.
"""

from __future__ import annotations

import os

import httpx
from django.core.management.base import BaseCommand, CommandError

from analyzer.services.opening_detector import DEFAULT_ECO_DB_PATH

SOURCE_FILES = ("a.tsv", "b.tsv", "c.tsv", "d.tsv", "e.tsv")
RAW_BASE_URL = "https://raw.githubusercontent.com/lichess-org/chess-openings/master"


class Command(BaseCommand):
    help = "Скачивает и склеивает ECO-базу дебютов lichess-org/chess-openings в analyzer/data/eco_openings.tsv"

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--output",
            type=str,
            default=str(DEFAULT_ECO_DB_PATH),
            help="Куда сохранить итоговый TSV (по умолчанию — путь из OpeningDetector)",
        )

    def handle(self, *args, **options) -> None:
        output_path = options["output"]
        merged_rows: list[str] = []
        header_written = False

        with httpx.Client(timeout=20) as client:
            for filename in SOURCE_FILES:
                url = f"{RAW_BASE_URL}/{filename}"
                self.stdout.write(f"Загружаю {url} ...")
                try:
                    response = client.get(url)
                    response.raise_for_status()
                except httpx.HTTPError as exc:
                    raise CommandError(f"Не удалось скачать {url}: {exc}") from exc

                lines = response.text.splitlines()
                if not lines:
                    continue

                if not header_written:
                    merged_rows.append(lines[0])
                    header_written = True
                merged_rows.extend(lines[1:])

        if not header_written:
            raise CommandError("Не удалось собрать ни одной строки базы — проверьте сеть/URL источника.")

        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(merged_rows) + "\n")

        self.stdout.write(self.style.SUCCESS(
            f"Готово: {len(merged_rows) - 1} дебютных линий сохранено в {output_path}"
        ))