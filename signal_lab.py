"""Reproducible weekday-aware triage for service-level operational metrics."""
import argparse
import csv
import hashlib
import json
import math
from datetime import date, timedelta
from pathlib import Path
from statistics import median


def wilson(k, n, z=1.96):
    p = k / n
    a = z * z / n
    center = (p + a / 2) / (1 + a)
    radius = z * math.sqrt((p * (1 - p) + a / 4) / n) / (1 + a)
    return max(0, center - radius), min(1, center + radius)


def load(raw):
    cells = {}
    for index, row in enumerate(csv.DictReader(raw.decode("utf-8-sig").splitlines()), 2):
        try:
            service = row["service"].strip()
            day = date.fromisoformat(row["date"])
            n, k = int(row["opened"]), int(row["late"])
            if not service or not 0 <= k <= n or n < 1 or (service, day) in cells:
                raise ValueError("invalid denominator, service, or duplicate service/date")
            cells[service, day] = (n, k)
        except (ValueError, KeyError, AttributeError, TypeError) as exc:
            raise ValueError(f"line {index}: {exc}") from exc
    if not cells:
        raise ValueError("no observations")
    return cells


def audit(raw, day, window=56, min_history=5, min_volume=50, threshold=.04):
    if min_history < 1 or window < 7 or min_volume < 1 or not 0 < threshold < 1:
        raise ValueError("invalid configuration")
    cells = load(raw)
    by_service = {}
    for (service, observed), counts in cells.items():
        if day - timedelta(days=window) <= observed < day and observed.weekday() == day.weekday():
            by_service.setdefault(service, []).append(counts)
    rows = []
    for service in sorted({s for (s, d) in cells if d <= day}):
        history = by_service.get(service, [])
        base = median(k / n for n, k in history) if history else None
        row = {"service": service, "history_days": len(history), "baseline": base}
        if (service, day) not in cells:
            row["status"] = "missing"
        else:
            n, k = cells[service, day]
            interval = wilson(k, n)
            row.update(opened=n, late=k, late_rate=k / n, interval_95=interval)
            if base is None or len(history) < min_history:
                row["status"] = "insufficient_history"
            elif n < min_volume:
                row["status"] = "low_volume"
            else:
                deviation = median(abs(bk / bn - base) for bn, bk in history)
                cutoff = base + max(threshold, 3 * 1.4826 * deviation)
                row.update(cutoff=cutoff, excess_cases=round(max(0, k - n * base), 2))
                row["status"] = "review" if interval[0] > cutoff else "monitor"
        rows.append(row)
    rows.sort(key=lambda x: (x["status"] != "review", -x.get("excess_cases", 0), x["service"]))
    return {"as_of": day.isoformat(), "source_sha256": hashlib.sha256(raw).hexdigest(),
            "config": dict(window=window, min_history=min_history, min_volume=min_volume, threshold=threshold),
            "services": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path)
    parser.add_argument("--date", required=True, type=date.fromisoformat)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = json.dumps(audit(args.csv.read_bytes(), args.date), ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.write_text(result, encoding="utf-8", newline="\n")
        else:
            print(result, end="")
    except (OSError, ValueError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
