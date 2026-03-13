# Debugging GlanceRF

This guide covers logging, debug options, and troubleshooting.

## Log levels

Set `log_level` in `glancerf_config.json` to control how much GlanceRF logs:

| Level | What you see |
|-------|--------------|
| `default` | Startup, shutdown, errors only |
| `detailed` | Default + web requests, API calls |
| `verbose` | Detailed + step-by-step internals |
| `debug` | Same as verbose (alias) |

Example:

```json
"log_level": "debug"
```

Restart GlanceRF after changing the log level.

## Log output

- **Console**: Logs always go to stderr (terminal/console).
- **File**: Set `log_path` to write logs to a file:

```json
"log_path": "glancerf.log"
```

Or use an absolute path:

```json
"log_path": "C:\\GlanceRF\\logs\\glancerf.log"
```

The log directory is created automatically if it does not exist.

## APRS-specific debug

To see incoming APRS packets from APRS-IS in the console, set:

```json
"aprs_debug": true
```

When enabled, each packet received is logged as:

```
APRS << CALLSIGN>APRS,TCPIP*:...
```

**Note:** At full feed, APRS-IS can send hundreds of packets per second. This option is very verbose. Use it briefly to verify the connection, then set to `false`.

Requirements for APRS debug to show anything:

- `setup_callsign` must be set in config (Setup → Station & updates)
- APRS cache must be connected to APRS-IS
- Packets must be arriving (connection successful)

## Verifying APRS packet reception

The APRS cache logs every 60 seconds while receiving:

```
APRS cache: 1234 packets received, 45.2/sec
```

If you see `APRS cache: SQLite error dropping packet:` in the logs, packets are being lost due to database errors (e.g. disk full, lock). Check disk space and permissions.

The cache connects to the APRS-IS full feed (`rotate.aprs.net:10152`) and stores all packets. Filtering (e.g. by callsign prefix) is done when the dashboard reads from the cache, not at ingest.

## APRS cache location

The APRS cache file is created at:

```
{config_dir}/cache/aprs.db
```

`config_dir` is the directory containing `glancerf_config.json` (or the path in `GLANCERF_PROJECT`).

The file is created when the first packet is received. If it does not exist:

1. Ensure `setup_callsign` is set
2. Restart GlanceRF
3. Check logs for `APRS cache started:` or `APRS cache: not started`
4. With `log_level: "debug"`, connection errors are logged

## APRS real-time updates

The APRS list and map overlay use WebSocket for real-time updates. When new packets arrive in the cache, the server broadcasts an `aprs_update` message. Clients receive it and refetch from the API immediately (typically within 1–2 seconds of new data).

## Quick reference

| Config key | Purpose |
|------------|---------|
| `log_level` | `default`, `detailed`, `verbose`, or `debug` |
| `log_path` | Optional file path for logs |
| `aprs_debug` | Log each incoming APRS packet (very verbose) |
| `aprs_cache_max_size_mb` | Max cache file size in MB before purging (Setup) |
| `aprs_cache_max_age_hours` | Purge records older than this (Setup) |

For environment variables (e.g. `GLANCERF_PROJECT`, `GLANCERF_CONFIG_PATH`), see [CONFIGURATION.md](CONFIGURATION.md).
