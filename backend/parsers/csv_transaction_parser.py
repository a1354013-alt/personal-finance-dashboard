from __future__ import annotations

import csv
import io


def parse_csv_rows(content: bytes) -> list[dict[str, str]]:
    for encoding in ("utf-8-sig", "utf-8", "cp950"):
        try:
            text = content.decode(encoding)
            break
        except UnicodeDecodeError:
            text = ""
    else:
        raise ValueError("Unable to decode CSV file. Please use UTF-8 or Big5 encoding.")

    stream = io.StringIO(text)
    reader = csv.DictReader(stream)
    if not reader.fieldnames:
        raise ValueError("CSV file is missing a header row.")
    return [{str(key or "").strip(): value for key, value in row.items()} for row in reader]

