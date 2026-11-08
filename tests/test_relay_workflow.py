from pathlib import Path
import json
import re
import sys
import textwrap
import types
import unittest
from tempfile import TemporaryDirectory
from unittest.mock import patch

WORKFLOW_PATH = Path(__file__).resolve().parents[1] / ".github/workflows/naukri-relay.yml"


def load_collector_script():
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
    match = re.search(r"python - <<'PY'\n(.*?)\n          PY", workflow, re.S)
    if not match:
        raise AssertionError("Collector Python heredoc was not found")
    return textwrap.dedent(match.group(1))


class FakeFrame:
    def __init__(self, rows):
        self.rows = rows
        self.empty = not rows

    def to_dict(self, orient):
        if orient != "records":
            raise AssertionError("Unexpected dataframe conversion mode")
        return self.rows


class RelayWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.collector_script = load_collector_script()

    def run_collector(self, *, queries, rows_by_query, last_good):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "private-app/v2").mkdir(parents=True)
            (root / "private-app/v2/config.json").write_text(
                json.dumps({
                    "naukri_queries": queries,
                    "naukri_locations": ["Bangalore"],
                }),
                encoding="utf-8",
            )
            (root / "last_good_naukri_relay.json").write_text(
                json.dumps(last_good),
                encoding="utf-8",
            )

            def scrape_jobs(*, search_term, **kwargs):
                result = rows_by_query.get(search_term)
                if isinstance(result, Exception):
                    raise result
                return FakeFrame(result or [])

            fake_jobspy = types.ModuleType("jobspy")
            fake_jobspy.scrape_jobs = scrape_jobs
            namespace = {"__name__": "__main__"}

            with patch.dict(sys.modules, {"jobspy": fake_jobspy}):
                old_cwd = Path.cwd()
                try:
                    import os
                    os.chdir(root)
                    exec(compile(self.collector_script, "workflow_collector.py", "exec"), namespace)
                finally:
                    os.chdir(old_cwd)

            output_path = root / "naukri_relay.json"
            if output_path.exists():
                return json.loads(output_path.read_text(encoding="utf-8"))
            return None

    @staticmethod
    def row(job_id, url=None):
        return {
            "id": job_id,
            "job_url": url or f"https://www.naukri.com/job-listings-{job_id}",
            "title": "Software Engineer",
            "company": "Example Labs",
            "location": "Bangalore",
            "date_posted": "2026-11-07",
            "description": "Python services",
        }

    def test_partial_target_failure_aborts_before_writing_new_feed(self):
        with self.assertRaisesRegex(SystemExit, "preserving the last-good feed"):
            self.run_collector(
                queries=["good", "bad"],
                rows_by_query={
                    "good": [self.row("one")],
                    "bad": RuntimeError("simulated source timeout"),
                },
                last_good={
                    "updated_at": "2026-11-07T10:00:00+00:00",
                    "count": 1,
                    "jobs": [{"id": "nk-one"}],
                },
            )

    def test_complete_scan_preserves_first_seen_and_adds_new_timestamps(self):
        previous_first_seen = "2026-11-07T10:00:00+00:00"
        payload = self.run_collector(
            queries=["existing", "new"],
            rows_by_query={
                "existing": [self.row("one")],
                "new": [self.row("two")],
            },
            last_good={
                "updated_at": "2026-11-07T11:00:00+00:00",
                "count": 1,
                "jobs": [{
                    "id": "nk-one",
                    "url": self.row("one")["job_url"],
                    "relay_first_observed_at": previous_first_seen,
                    "relay_last_observed_at": "2026-11-07T10:50:00+00:00",
                }],
            },
        )

        self.assertIsNotNone(payload)
        self.assertEqual(payload["count"], 2)
        by_id = {job["id"]: job for job in payload["jobs"]}
        self.assertEqual(by_id["nk-one"]["relay_first_observed_at"], previous_first_seen)
        self.assertEqual(by_id["nk-one"]["relay_last_observed_at"], payload["updated_at"])
        self.assertEqual(by_id["nk-two"]["relay_first_observed_at"], payload["updated_at"])
        self.assertEqual(by_id["nk-two"]["relay_last_observed_at"], payload["updated_at"])
        self.assertNotEqual(by_id["nk-one"]["relay_first_observed_at"], payload["updated_at"])

    def test_legacy_job_uses_previous_snapshot_time_as_migration_baseline(self):
        previous_feed_time = "2026-11-07T11:00:00+00:00"
        payload = self.run_collector(
            queries=["existing"],
            rows_by_query={"existing": [self.row("one")]},
            last_good={
                "updated_at": previous_feed_time,
                "count": 1,
                "jobs": [{"id": "nk-one", "url": self.row("one")["job_url"]}],
            },
        )
        job = payload["jobs"][0]
        self.assertEqual(job["relay_first_observed_at"], previous_feed_time)
        self.assertEqual(job["relay_last_observed_at"], payload["updated_at"])


if __name__ == "__main__":
    unittest.main()