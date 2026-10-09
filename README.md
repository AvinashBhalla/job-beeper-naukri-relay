# JobBeeper Naukri Relay

This public repository is a data-only relay, separate from the private JobBeeper application. The generated feed is published on the `naukri-relay` branch.

## Setup

1. Add a repository Actions secret named `PRIVATE_APP_READ_TOKEN` using a fine-grained token restricted to `AvinashBhalla/job-beeper` with Contents: Read-only.
2. Add `.github/workflows/naukri-relay.yml` using the workflow staged in the private repository at `docs/relay-bootstrap/naukri-relay.yml`.
3. Run the `public-naukri-relay` workflow manually and verify that the feed is available at:
   https://raw.githubusercontent.com/AvinashBhalla/job-beeper-naukri-relay/naukri-relay/dashboard/data/naukri_relay.json

The workflow should check out only `v2/config.json` from the private app. Do not copy private application source, database files, user configuration, or runtime secrets into this repository.

The feed contains `updated_at`, `count`, and `jobs`. Empty collections should fail rather than replacing the last-good feed. Job listing data in the feed is public.
