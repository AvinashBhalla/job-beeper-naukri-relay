# JobBeeper Naukri Relay

This public repository is a data-only relay, separate from the private JobBeeper application. The workflow publishes only the generated Naukri feed to the `naukri-relay` branch.

Before running it, configure the required `PRIVATE_APP_READ_TOKEN` repository Actions secret with read-only access to the private `AvinashBhalla/job-beeper` repository. Never commit credentials. Then open Actions → public-naukri-relay → Run workflow.

Verify that this URL returns valid JSON with `updated_at`, `count`, and a non-empty `jobs` array:
https://raw.githubusercontent.com/AvinashBhalla/job-beeper-naukri-relay/naukri-relay/dashboard/data/naukri_relay.json

The workflow checks out only `v2/config.json` from the private app's `v2-live-radar` branch. It does not copy private application source, databases, or runtime secrets. Job listing data and descriptions in the generated feed are public. Empty collection fails rather than replacing the last-good feed. Do not cut production over until the raw URL returns fresh, valid JSON.
