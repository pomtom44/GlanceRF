# Stats module (custom)

Displays telemetry stats such as **total installs** in a grid cell. Requests go to the telemetry server stats endpoint (obfuscated path + key auth).

## Configuration

URL and key are **hardcoded** in the stats module. Edit `api_routes.py` in this folder and set:

- **`TELEMETRY_BASE_URL`** – Your telemetry server base URL (no trailing slash), e.g. `https://glancerf-telemetry.zl4st.com`
- **`STATS_KEY`** – The same secret key as `$stats_secret_key` in telemetry-server `installs.php`

No config file or environment variables are used. The stats path is fixed in code and must match the folder name under the telemetry server.

The endpoint must return JSON with at least:

```json
{ "total_installs": 123 }
```

## Excluding IPs (e.g. 203.86.195.200, 49.50.253.93)

Exclusion is done **on the stats server**, not in GlanceRF. Your telemetry backend should count unique installations (e.g. by GUID or first-seen IP) and exclude the IPs you want (e.g. your own test or dev IPs) before returning `total_installs`.
