"""Stats module: displays metrics from the telemetry stats API (e.g. total installs). Configure Stats API URL in Setup or via GLANCERF_STATS_API_URL. The stats endpoint should return JSON e.g. {"total_installs": N} (excluding IPs is done server-side)."""

MODULE = {
    "id": "stats",
    "name": "Stats",
    "color": "#0d1117",
}
