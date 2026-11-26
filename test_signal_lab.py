import tempfile
import unittest
from datetime import date
from pathlib import Path

from make_demo import write_demo
from signal_lab import audit, wilson


class SignalLabTests(unittest.TestCase):
    def setUp(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "data.csv"
            write_demo(path)
            self.raw = path.read_bytes()
        self.day = date(2025, 3, 5)

    def test_demo_separates_review_low_volume_missing_and_monitor(self):
        report = audit(self.raw, self.day)
        statuses = {r["service"]: r["status"] for r in report["services"]}
        self.assertEqual(statuses, {"permit-intake": "review", "street-repairs": "monitor",
                                    "records-desk": "missing", "library-support": "low_volume"})
        self.assertEqual(report["services"][0]["service"], "permit-intake")

    def test_future_and_other_weekdays_do_not_change_signal(self):
        altered = self.raw + b"new-service,2025-03-06,90,90\n"
        self.assertEqual(audit(self.raw, self.day)["services"], audit(altered, self.day)["services"])

    def test_reject_duplicate_and_out_of_range(self):
        for row in [b"permit-intake,2025-03-05,1,0\n", b"new,2025-03-05,2,3\n"]:
            with self.assertRaises(ValueError):
                audit(self.raw + row, self.day)

    def test_wilson_not_overconfident(self):
        self.assertLess(wilson(2, 2)[0], .5)
        self.assertGreater(wilson(0, 2)[1], .5)

    def test_insufficient_history_is_not_silently_ranked(self):
        report = audit(self.raw, date(2025, 1, 2))
        self.assertTrue(all(row["status"] == "insufficient_history" for row in report["services"]))


if __name__ == "__main__":
    unittest.main()
