# GlanceRF (A Hamclock Modern Rebuild)

### What is GlanceRF
GlanceRF is a modern rebuild of the Original HamClock by Elwood WB0OEW
During development of this project, early in Beta Versions, Elwood passed away.
Originally, this project was to be a side project, and I was going to tell people
"If you want a mature project with support, go use hamclock"
Thoughts go to Elwood, and I thank him for the original project which so many use, and inspired the rebuild of this.

**Disclaimer:**
This is a personal project, I have built it for my needs, but also designed it for ease of use for others.
Once it's working how I want, support will be limited.
However requests, bugs, etc, I will do my best to sort out.


## TLDR Setup Guide.

Download the Project
Install python
Open a terminal to your downloaded location
Run `pip install -r requirements.txt`
or `pip install -r requirements_headless.txt` if you are running on a server with no GUI
(The default version has a pop up window with the main display showing, the headless runs in only a terminal for servers or no GUI popup, and is accessed via a web browser)
Configuration is stored in **`glancerf_config.json`** in the same folder as `run.py` (the Project folder). Edit it to disable desktop mode if running headless.
Run `python run.py` and then follow the setup guide
(If headless, connect via a web browser to continue setup)


## Documentation

Guides in the **[docs/](docs/)** folder:

- **[docs/USER_GUIDE.md](docs/USER_GUIDE.md)** – How to use: first run, setup, keyboard shortcuts (S = Setup, L = Layout), layout editor, map center (Maidenhead or lat,lng), map and clock module options, and configuration.
- **[docs/MODULES.md](docs/MODULES.md)** – Module system and available modules.
- **[docs/CREATING_A_MODULE.md](docs/CREATING_A_MODULE.md)** – How to create a new cell module: folder structure, module.py, index.html, style.css, script.js, naming conventions, and settings.
- **[docs/TELEMETRY.md](docs/TELEMETRY.md)** – Telemetry and privacy information: what data is collected, what isn't, and how to control it.

## Requirements

- Python 3.8 or higher
- See `requirements.txt` for dependencies

**Installation options:**
- **Full installation (with desktop GUI):** `pip install -r requirements.txt`
- **Headless installation (server-only, no GUI):** `pip install -r requirements_headless.txt`

**Note:** For desktop mode, PyQt5 and PyQtWebEngine are required. They are included in `requirements.txt` but not in `requirements_headless.txt`. The application will automatically skip GUI imports if desktop mode is disabled in the configuration.

## Features

 - Desktop app for local use
 - Server only version with web based access
 - Read only mode for 'public' displays
 - Works with any size monitor, dynamic scaling
 - Choose your grid layout, no set grid size
 - Choose which modules go where, no fixed layout
 - Resize modules, have some small and some large

 - Clock with Local, UTC, and International Time
 - Map with various base images

## Feature requests

A list of requested features is in **[docs/FEATURE_REQUESTS.md](docs/FEATURE_REQUESTS.md)**.  
To request a feature, open an Issue and it will be reviewed.


**Disclaimer:**
This project was heavily assisted with AI.
While I could program it all by myself, it would likely take a long time.
The concepts, and code review are all mine, and I am still doing manual fixes and bug reviews.
If you don't like this, each to their own, that is fine, however I would appreciate you keeping it to yourself