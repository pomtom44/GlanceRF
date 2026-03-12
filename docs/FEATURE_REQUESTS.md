# Feature Requests

This document tracks requested features and their status.

## Implemented

| Feature | Status | Notes |
|---------|--------|-------|
| Satellite passes on map | Done | Satellite pass module shows positions and tracks on map overlay |
| Docker implementation | Done | `GLANCERF_DOCKER` env var; headless mode; see INSTALLATION.md |
| GPIO | Done | Raspberry Pi GPIO for inputs/outputs; configure via Menu → GPIO |
| APRS | Done | APRS module with last-heard list and map overlay from APRS-IS cache |
| Map overlay layout | Done | Map only modules page; modules feed map without taking a grid cell |
| Themes, fonts, colors | Partial | Per-module colors; no global theme system yet |

## Requested (not yet implemented)

| Feature | Description |
|---------|-------------|
| Predicted radiosonde landing locations | Show predicted landing spots for radiosondes on the map |
| GPS integration | Use GPS hardware for automatic location |
| Global themes | System-wide theme, font, and color controls |
| Radiosonde tracking | Track and display radiosonde positions |

## How to request a feature

Open an issue on [GitHub](https://github.com/pomtom44/GlanceRF/issues) with:

- Clear description of the feature
- Use case (why it would help)
- Any technical constraints or preferences
