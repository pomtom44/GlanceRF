# Configuration

Config is stored in `glancerf_config.json` in the Project directory.

## Config Keys

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `port` | int | 8080 | Main server port |
| `readonly_port` | int | 8081 | Read-only server port |
| `desktop_mode` | str | "browser" | `desktop`, `browser`, `terminal`, `headless`, or `none` |
| `first_run` | bool | true | Redirect to setup when true |
| `max_grid_scale` | int | 10 | Max grid columns/rows (1–20) |
| `grid_columns` | int | — | Grid width |
| `grid_rows` | int | — | Grid height |
| `aspect_ratio` | str | "16:9" | Screen aspect ratio |
| `orientation` | str | "landscape" | `landscape` or `portrait` |
| `layout` | list | — | 2D array of module ids per cell |
| `cell_spans` | dict | {} | Merged cells: `"row_col"` → `{colspan, rowspan}` |
| `module_settings` | dict | {} | Per-cell settings: `"row_col"` → `{...}` |
| `setup_callsign` | str | "" | Callsign for modules |
| `setup_location` | str | "" | Grid square or lat,lng |
| `setup_ssid` | str | "01" | APRS SSID |
| `update_mode` | str | "auto" | `none`, `notify`, or `auto` |
| `update_check_time` | str | "03:00" | HH:MM for update check |
| `telemetry_enabled` | bool | true | Opt-in telemetry |
| `log_level` | str | "default" | `default`, `detailed`, `verbose`, `debug` |
| `log_path` | str | — | Log file path |
| `aprs_debug` | bool | false | Log each incoming APRS packet to console (very verbose at full feed) |
| `disable_gpu` | bool | false | Disable GPU for WebEngine (Sandbox/VMs) |
| `gpio_assignments` | dict | {} | GPIO pin mappings (Raspberry Pi) |
| `on_the_air_shortcut` | str | "" | Shared shortcut for callsign/on_the_air modules |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `GLANCERF_CONFIG_PATH` | Override config file path |
| `GLANCERF_DESKTOP_MODE` | Override `desktop_mode` |
| `GLANCERF_PORT` | Override port |
| `GLANCERF_READONLY_PORT` | Override readonly port |
| `GLANCERF_DOCKER` | Set when running in Docker (headless) |
| `GLANCERF_SHOW_CONSOLE` | Force console visible on Windows |
| `GLANCERF_DISABLE_GPU` | Disable GPU (Sandbox/VMs) |
| `GLANCERF_PROJECT` | Override project/config directory |

## Config Location

- Default: `Project/glancerf_config.json`
- Override: `GLANCERF_CONFIG_PATH` or `GLANCERF_PROJECT`
