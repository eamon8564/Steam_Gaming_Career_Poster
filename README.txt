Steam Gaming Career Poster

A Python desktop application that turns Steam library records into a shareable gaming career poster.
It supports an offline demo, optional live Steam loading, adjustable poster layouts, and image
export.

Image: Example poster using fictional demo statistics (../presentation/padlet_image.png)

Generate your own Steam poster: step-by-step

1. Extract the entire archive and enter Steam_Gaming_Career_Poster. Keep all subfolders beside
   main.py.
2. Choose your interpreter. Copy setup/python_path.example.txt to setup/python_path.txt; enter the
   full path to your own python.exe, on one line without quotes. Use Python 3.10 or later with
   Tkinter and a graphical desktop for live interactive use.
3. Check Tkinter and install Pillow using that same interpreter. In a terminal opened in the project
   root, run python -m tkinter and python -m pip install -r setup/requirements.txt with your
   environment activated, or use its full executable path as shown above. Close the Tkinter test
   window before continuing.
4. Configure a personal API key. Follow the key guide (docs/STEAM_API_KEY_GUIDE.md). Save only the
   actual 32-character key in steam_api_key.txt beside main.py; an existing STEAM_WEB_API_KEY
   environment variable takes priority. Make sure your game details and playtime are visible to the
   API.
5. Launch and load your library. Double-click launch.cmd, choose Connect Steam, sign in on Steam's
   official browser page, and return to the application. Alternatively use Load SteamID with your
   SteamID64. Wait for library and artwork loading, then check the player name, Steam / live label,
   and game list. Use Demo Data and terminal-only mode use fictional demo records.
6. Inspect and customise. Select All or Recent year, Vertical or Landscape, and Scale. Top N = 0
   shows every played game separately; a positive limit groups the remainder after Apply. Recent
   year retains lifetime hours for the selected recently played games.
7. Save and view. Choose Export Image, select PNG or SVG, and save under output/. Open the PNG in an
   image viewer or SVG in a browser. PNG export and in-app artwork preview need Pillow; SVG export
   can run without it.

Notice for the marker

Run main.py locally after extracting the submission archive. Keep all supplied subfolders beside it.
The root contains only the entry point, Windows launcher and this README; your optional personal key
also belongs here. The full Tkinter GUI requires a graphical desktop. In terminal-only environments,
the entry point falls back to an offline demonstration and writes an SVG poster; it does not open a
window.

Component: Requirement
Python: Python 3.10 or later; Tkinter/Tcl/Tk is required for the GUI
Offline demo: Bundled JSON and artwork; no Steam account, API key, or internet required
Full artwork preview and PNG export: Optional third-party library Pillow
Live Steam functionality: Internet, a personal Steam Web API key, and game details visible to the
API
Audio/video processing: Not used

Verified on Windows with Python 3.12.13 and Pillow 11.1.0. Other operating systems have not been
tested. The program does not require Anaconda or a developer-specific drive path.

Quick start

Open a terminal in this folder, where main.py is located.

1. Check that Tkinter works:

   python -m tkinter

   Close the test window. If Tkinter is unavailable, install Python with Tcl/Tk support using your platform's Python installer. Tkinter is not installed as a normal pip dependency.

2. For the full artwork preview and PNG export, install the optional dependency:

   python -m pip install -r setup/requirements.txt

3. Start the application:

   python main.py

4. Click Use Demo Data.

If your system uses python3, substitute it for python. On Windows, double-click launch.cmd. It uses
STEAM_POSTER_PYTHON when set, then setup/python_path.txt if supplied, then the owner's existing
E:\Anaconda\envs\comp5310 environment if present, a local .venv, or system python / py -3. Other
computers do not need that Anaconda path. Failures stay visible and are recorded in
output/startup.log when Python was launched.

To choose an interpreter explicitly in PowerShell:

$env:STEAM_POSTER_PYTHON = 'E:\Anaconda\envs\comp5310\python.exe'
.\launch.cmd

Set the variable to the full path of an existing python.exe. Extract the archive before launching;
do not run from inside the ZIP.

Using your own Python environment

See ENVIRONMENT_SETUP.md (docs/ENVIRONMENT_SETUP.md) for interpreter configuration and
troubleshooting.

For persistent Windows double-click configuration:

1. Copy setup/python_path.example.txt to setup/python_path.txt.
2. Replace its contents with the full path of your own python.exe, on one line without quotes.
   Example: D:\Anaconda\envs\my_project\python.exe.
3. Install the optional Pillow dependency into that same interpreter if you need PNG or cover
   preview:

   & 'D:\Anaconda\envs\my_project\python.exe' -m pip install -r .\setup\requirements.txt

4. Double-click launch.cmd. The file remains under setup/; it does not clutter the root.

You can alternatively run the interpreter directly, without any launcher configuration:

& 'D:\Anaconda\envs\my_project\python.exe' main.py

Replace the example path with an existing interpreter on your computer. Activate an environment and
use python main.py if you prefer. The terminal-only environment variable example above applies to
the same terminal session; it does not change a separately launched Explorer window.
STEAM_POSTER_PYTHON takes precedence over the path file. Do not distribute your personal
setup/python_path.txt as a required setting for others.

Terminal-only / Ed demonstration

If Tkinter is absent or a graphical display cannot be opened, python main.py automatically prints
fictional demo statistics and generates an SVG in output/. No Steam key, internet, Pillow, or
display is needed for that path. A generated SVG can be downloaded and opened locally in a browser.
This does not provide interactive GUI controls in a terminal.

To select this mode explicitly:

python main.py --no-gui
python main.py --no-gui --orientation landscape --scale 50 --top-n 3

Optional terminal flags: --format svg|png, --mode all|recent_year, --orientation vertical|landscape,
--scale 100|75|65|50|40, and --top-n N. PNG needs Pillow. These settings affect the terminal export;
interactive settings are selected in the GUI. Use python main.py --help for usage.

Without Pillow, the application still runs using the standard library and Tkinter. Its preview shows
coloured tiles and text. SVG export embeds the supplied artwork and can be viewed in a browser.
Artwork preview inside the application and PNG export require Pillow.

Offline demonstration

The supplied library contains 15 owned games, including 12 played games, totalling 98,850 minutes /
1,647.5 hours. All playtimes and activity dates are fictional. Demo Mode loads local data and cached
artwork without contacting Steam.

- Orientation: choose Vertical or Landscape.
- Scale: choose 100%, 75%, 65%, 50%, or 40%. It changes available tile area before layout; larger
  values produce larger poster areas.
- Top N: set 0 to show every played game separately. A positive limit combines the remaining games
  under Other, preserving their total minutes.
- Game list: inspect titles, lifetime hours, shares, optional two-week hours, and last-played dates.
- Hover: reveal a tile's full name, lifetime hours, and actual share.
- Export Image: save PNG or SVG under output/ or one of its subfolders. Export includes the complete
  poster regardless of preview scroll position.

Optional live Steam mode

See STEAM_API_KEY_GUIDE.md (docs/STEAM_API_KEY_GUIDE.md) for step-by-step registration, domain
guidance, key-file format, environment variables, and troubleshooting.

Provide your personal Steam Web API key using either:

- The environment variable STEAM_WEB_API_KEY.
- A local file named steam_api_key.txt next to main.py, containing only the 32-character key,
  without labels, quotes, or JSON.

No key is included in the submission. Keep your key private and exclude it from uploads.

Connect Steam opens Steam's official login page in the default browser. Credentials are entered only
on Steam. OpenID verifies the identity using a temporary local loopback callback; the program then
requests the visible library and artwork. Load SteamID offers an alternative using a valid
SteamID64. Network or API failures show an explanation and offer Demo Mode.

Data and layout semantics

Setting: Meaning
All games: Uses cumulative playtime of returned owned games. Zero-minute games count toward
ownership but occupy no tile area.
Recent year: Selects games last played within the previous 365 days. Displayed hours remain lifetime
hours, not hours played during that year. Missing or invalid dates are excluded.
Landscape: Allocates content area proportionally to lifetime minutes before decorative gaps and
pixel rounding. At 75% it is 1920 × 1080. Width stays fixed; content height changes with Scale.
Vertical: Fixes width at 1080 pixels and grows downward. Small-game weights are increased for
readability, so tile areas are approximate; percentage labels still use actual minutes.

Covers use proportional scaling and centre cropping to avoid stretching. Missing or corrupt artwork
falls back to coloured tiles. Very large PNG exports have a memory safeguard; SVG remains available
for the complete layout.

Project structure

Steam_Gaming_Career_Poster/
├── main.py                 Entry point: python main.py
├── launch.cmd              Windows launcher
├── README.md               Main running instructions
├── steam_api_key.txt        Optional personal key: create locally; not submitted
├── src/
│   ├── ui/                 Tkinter interface and event handling
│   ├── core/               Game models, analysis, validated settings
│   ├── poster/             Layout and rendering
│   ├── steam/              API, OpenID authentication, date filtering
│   └── common/             Project paths, JSON loading, artwork caching
├── data/                   Fictional demonstration library
├── cache/                  Supplied demo artwork
├── output/                 Export destination and startup log
├── setup/
│   ├── requirements.txt    Optional Pillow dependency
│   └── python_path.example.txt  Template for a personal interpreter path
├── docs/                   Plain-text README, technical notes, attribution,
│                          key guides and test report
└── tests/                  Automated and GUI verification

The submission archive also includes a sibling presentation/ folder with a Padlet description,
example images, a timed presentation script, and a code explanation guide.

Programming concepts

- File I/O: reads JSON, reuses cached artwork, and writes exported images.
- Exception handling: handles invalid data/settings, missing files, network failures, and artwork
  fallback.
- Classes and objects: organise game records, collections, poster settings, rendering, and GUI
  control.
- Functions, loops, conditionals, and sorting: support filtering, aggregation, ranking, and layout.

See TECHNICAL_NOTES.txt (docs/TECHNICAL_NOTES.txt) for implementation details and ATTRIBUTION.txt
(docs/ATTRIBUTION.txt) for references and the AI assistance disclosure.

Verification

Run from this folder:

python -m unittest discover -s tests -v
python tests/verify_gui.py
python tests/verify_auth.py

The prepared submission passed 31 functionality/layout/rendering/path/headless tests, 4 simulated
authentication tests, and actual GUI checks with and without Pillow. The extracted archive's main.py
entry point, offline demo, artwork lookup, and PNG/SVG export were also checked.

GUI checks require a graphical desktop. Authentication tests use local loopback and mocked Steam
replies; they do not log into a real account. No real Steam login, external API availability, other
operating system, or tutor computer was retested for this submission. See TEST_REPORT.txt
(docs/TEST_REPORT.txt) and the delivery-level ARCHIVE_VERIFICATION.txt for the scope of
verification.
