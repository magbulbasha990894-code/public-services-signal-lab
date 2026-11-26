"""Generate deterministic fictional daily data, no network required."""
from datetime import date, timedelta
from pathlib import Path
from random import Random
import csv


def write_demo(path):
    rng = Random(174)
    start = date(2025, 1, 1)
    target = date(2025, 3, 5)
    services = {"permit-intake": (205, .12), "street-repairs": (125, .15),
                "records-desk": (110, .10), "library-support": (24, .16)}
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(("service", "date", "opened", "late"))
        day = start
        while day <= target + timedelta(days=4):
            for service, (capacity, typical) in services.items():
                if day == target and service == "records-desk":
                    continue
                n = capacity + rng.randint(-8, 8)
                rate = typical + (.05 if day.weekday() >= 5 else 0)
                if day == target and service in {"permit-intake", "library-support"}:
                    rate += .30
                writer.writerow((service, day.isoformat(), n, round(n * (rate + rng.uniform(-.02, .02)))))
            day += timedelta(days=1)


if __name__ == "__main__":
    write_demo(Path(__file__).with_name("demo.csv"))
