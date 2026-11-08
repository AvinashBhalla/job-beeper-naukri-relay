# JobBeeper Naukri Relay

This public repository is a data-only relay, separate from the private JobBeeper application. The workflow publishes only the generated Naukri feed to the `naukri-relay` branch.

Before running it, configure the required `PRIVATE_APP_READ_TOKEN` repository Actions secret with read-only access to the private `AvinashBhalla/job-beeper` repository. Never commit credentials. Then open Actions → public-naukri-relay → Run workflow.

Verify that this URL returns valid JSON with `updated_at`, `count`, and a non-empty `jobs` array:
https://raw.githubusercontent.com/AvinashBhalla/job-beeper-naukri-relay/naukri-relay/dashboard/data/naukri_relay.json

The workflow checks out only `v2/config.json` from the private app's `v2-live-radar` branch. It does not copy private application source, databases, or runtime secrets. Job listing data and descriptions in the generated feed are public. Empty collection fails rather than replacing the last-good feed. Do not cut production over until the raw URL returns fresh, valid JSON.


## Snapshot reliability and per-job observation timestamps

The workflow loads the last published feed before collection. If any configured query/location target fails, the run exits without publishing a partial snapshot; the previous relay branch remains the last-good feed. An empty overall result also fails closed.

Each successfully published job includes:
- relay_first_observed_at: the first relay snapshot time in which the job was observed. For pre-existing jobs during rollout, the previous snapshot updated_at is used as a migration baseline; it is not claimed to be the job's historic first-seen time.
- relay_last_observed_at: the time of the current successful relay scan.

The top-level updated_at remains the completion timestamp for the whole snapshot. These are relay-observation timestamps, not employer publication timestamps. Date-only posted values still do not support exact publication or discovery-latency calculations.


## Local workflow regression tests

Run the publisher contract tests without scraping or making network requests:

```bash
python -m unittest discover -s tests -v
```

The tests execute the embedded collector with a stubbed JobSpy provider. They cover partial-target failure (no replacement feed), successful first/last observation timestamps and the migration baseline for existing feed records.