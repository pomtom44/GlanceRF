# Telemetry and Privacy

GlanceRF can send anonymous usage data to help improve the application. This document describes what is collected, what is not, and how to control it.

## What data is collected

When telemetry is enabled, the following data may be sent to the telemetry server:

### System information (anonymous)

- Operating system (e.g. Windows, Linux, Darwin)
- OS release and version
- CPU architecture (e.g. x86_64, ARM64)
- Python version and implementation (e.g. CPython)
- Processor identifier (generic model string from the OS)

### GlanceRF usage (anonymous)

- Application version
- Grid size (columns and rows)
- Number of cells that have a module assigned
- List of **enabled module IDs** (e.g. `["clock", "weather"]`) – the module type names only, not any settings or content
- Number of installed modules and their **IDs** (e.g. `["clock", "empty", "weather"]`)
- Whether the desktop window mode is enabled
- Update check mode (e.g. "auto", "none")

### Session and events

- A randomly generated anonymous ID (GUID) assigned by the server on first run, used only to approximate unique installations and aggregate usage over time
- Event type: `installation` (first run), `startup`, `heartbeat` (periodic), or `test` (manual test only)
- Timestamp (UTC) for when the event was sent

## What is NOT collected

- Your callsign, location, or any text you enter in Setup or module settings
- IP addresses are not stored as part of your profile (they may be seen in server logs for normal HTTP requests)
- No personal data, credentials, or content from any module (e.g. no weather data, no calendar data)

## How telemetry is used

- To understand which platforms and Python versions are in use
- To see which modules are popular and how grid sizes are used
- To prioritize fixes and features (e.g. platform-specific issues, module usage)
- To approximate install base and version distribution

Data is sent over HTTPS to the telemetry endpoint and handled according to the server operator's policy.

## How to control telemetry

- **Default:** Telemetry is **enabled** (opt-out).
- **Disable:** Open **Setup** (from the main menu or first-run wizard), go to **Page 2**, set **Telemetry** to **Disabled (Opt-out)**. No further data is sent until you turn it back on.
- You can change this setting at any time. The application works the same with telemetry on or off.

## When data is sent

- **Installation / first run:** One installation event may be sent when you complete setup (to obtain the anonymous GUID).
- **Startup:** One event when the application has finished starting (after setup is complete).
- **Heartbeat:** Approximately once per hour while the app is running (only after setup is complete).

If you disable telemetry, the startup and heartbeat are disabled, however first run still runs to get the GUID.

## Technical details

- Telemetry is implemented in `glancerf/telemetry.py`.
- The telemetry endpoint URL is: `https://glancerf-telemetry.zl4st.com/telemetry.php`
- Requests are sent as JSON over HTTPS with a 10-second timeout. Failures are logged but do not affect application behavior.

For the full list of fields and event types, see the `get_system_info()`, `get_glancerf_info()`, and payload construction in `glancerf/telemetry.py`.
