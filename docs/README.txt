STEAM GAMING CAREER POSTER — COMP9001 FINAL PROJECT

ENTRY POINT: main.py
Run all commands from the application root (one folder above docs/),
where main.py and launch.cmd are located, after extracting the archive.

VIEW YOUR OWN STEAM POSTER: STEP BY STEP
1. Extract the whole archive and open the application folder with main.py.
2. Copy setup/python_path.example.txt to setup/python_path.txt and replace its
   content with your own full python.exe path, one line with no quotes.
3. Using that interpreter, check Tkinter and install optional Pillow:
       python -m tkinter
       python -m pip install -r setup/requirements.txt
   These commands assume your chosen environment is activated; otherwise use
   its full executable path. A local graphical desktop is needed for the GUI.
4. Put your personal 32-character key alone in steam_api_key.txt beside main.py.
   See STEAM_API_KEY_GUIDE.md in docs/ for registration and troubleshooting.
5. Double-click launch.cmd and choose Connect Steam. Complete sign-in on Steam's
   official browser page, return to the program, and wait for library/artwork.
   Check player name, Steam / live and Game list to confirm it is your library.
   Load SteamID is an alternative; API key and visible game details are needed.
6. Set All/Recent year, Vertical/Landscape, Scale and Top N. Recent year uses
   lifetime hours for recently played games. Top N changes require Apply.
7. Click Export Image, save PNG/SVG under output/, then open the saved file.
   PNG needs Pillow in the environment actually running the application.
Use Demo Data and terminal-only mode show fictional data, not your own library.
The terminal command python main.py --no-gui exports only an offline demo.
Full English and Chinese instructions are in the top-level README.md.

IMPORTANT NOTICE FOR THE MARKER
The full local desktop GUI uses Tkinter and needs a graphical display.
Without Tkinter or a display, main.py automatically exports an offline SVG
demo and prints statistics. Use python main.py --no-gui to select that mode. Steam functionality uses the
network; PNG export and artwork preview use the optional third-party
library Pillow. No audio/video processing is used. No API key is included.

1. REQUIREMENTS AND QUICK START
Use Python 3.10 or later. The GUI needs Tkinter/Tcl/Tk and a graphical desktop;
the offline terminal SVG demo uses only the standard library.
Verified environment: Windows, Python 3.12.13, Pillow 11.1.0.
Other operating systems have not been tested.

To check Tkinter, run:
    python -m tkinter
A small window should open; close it to continue. If Tkinter is missing,
install Python with Tcl/Tk support using the platform's Python installer.
Tkinter cannot be installed using pip as a normal third-party package.

For the complete artwork preview and PNG export, install Pillow:
    python -m pip install -r setup/requirements.txt

Start the program:
    python main.py

Windows users can double-click launch.cmd after extracting the archive.
The launcher checks STEAM_POSTER_PYTHON, then setup/python_path.txt,
then the owner's existing comp5310
Anaconda environment if present, a local .venv, and system python/py.
Other machines do not require the owner's Anaconda environment.
Launch errors remain visible; Python errors are saved in output/startup.log.
To select your own interpreter in PowerShell:
    $env:STEAM_POSTER_PYTHON = 'C:\path\to\python.exe'
    .\launch.cmd
If your system uses python3 instead of python, substitute python3 in the
commands. No Anaconda environment or developer-specific drive is needed.

2. OFFLINE MARKING PATH — NO STEAM ACCOUNT OR KEY REQUIRED
Click Use Demo Data. The supplied JSON contains 15 owned games, including
12 with recorded playtime, totalling 1,647.5 hours. All playtime and activity
dates are fictional. Required demo artwork is supplied in cache/.
Loading Demo does not download files or contact Steam.

Select Vertical or Landscape and change Scale. Larger scales allocate
more poster area before the tiles are arranged. Top N = 0 shows every
played game separately; a positive limit groups the remaining minutes
under Other. Open Game list or hover over tiles to inspect the data.
Click Export Image, choose PNG or SVG, and save under output/ or one of
its subfolders. Scroll position does not limit the exported image.

Pillow is OPTIONAL for a runnable demonstration. With only the standard
library and Tkinter, the GUI shows coloured tiles and text; SVG export
embeds the supplied artwork and can be opened in a browser. PNG export
and artwork preview in the application require Pillow.

3. OPTIONAL LIVE STEAM MODE
See STEAM_API_KEY_GUIDE.md for registration and step-by-step configuration.
Internet access, a personal Steam Web API key, and game details visible
to the API are required. Use either STEAM_WEB_API_KEY in the environment
or a file named steam_api_key.txt next to main.py. Its entire contents
must be the 32-character key, without quotes, labels or JSON.
Do not share or upload your API key.

Connect Steam opens Steam's official website in the default browser.
Credentials are entered only on Steam. OpenID returns an identity which
is verified using a temporary loopback callback on this computer. The
application then requests the visible game library and cover artwork.
Load SteamID is an alternative for a valid SteamID64.
API or network failures show an explanation and offer Demo Mode.

4. DATA MEANING AND LIMITATIONS
All: uses cumulative playtime of the returned owned games. Games with
zero minutes count toward ownership but do not occupy poster tiles.
Recent year: includes games whose returned last-played timestamp falls
within the last 365 days. Their displayed hours are LIFETIME hours, not
hours played within that year. Missing or invalid dates are excluded;
the interface explains when there are no usable dates.

Landscape allocates tile area in proportion to lifetime minutes, before
decorative gaps and pixel rounding. At 75% it is 1920 x 1080; width stays
fixed and content height changes with Scale. Vertical fixes width at
1080 and grows downward. It raises small-game layout weights to maintain
readable sizes, so its areas are approximate; percentage labels always
use actual minutes. There is no achievement or minimum-area control.

Missing or corrupt artwork uses a coloured placeholder. Very large PNGs
have a memory safeguard; SVG is available for the complete layout.

5. FILES AND PROGRAMMING CONCEPTS
main.py              starts the application
src/ui/app.py               GUI events, worker queue, settings and export dialog
src/core/models.py            Game and GameLibrary classes; validated source data
src/core/analyzer.py          reusable library statistics
src/core/config.py            validated poster settings
src/poster/treemap_layout.py    sorting, optional grouping and squarified layout
src/poster/image_renderer.py    shared scene for preview, PNG and SVG
src/steam/steam_data.py        filtering and precise date/time semantics
src/steam/steam_api.py         Web API requests and local key loading
src/steam/steam_auth.py        official OpenID sign-in and callback verification
src/common/utils.py             JSON file loading and optional artwork downloads
data/                fictional offline demonstration library
cache/               only the supplied demo's cover artwork
output/              image export destination
tests/               automated checks and GUI/callback verification

Advanced topics demonstrated include file I/O (JSON, cached images,
exported files) and exception handling (invalid files/settings, network
failures and rendering fallbacks). Classes and objects organise game
data and the GUI. Loops, conditionals, functions and sorting support the
analysis and layout. See TECHNICAL_NOTES.txt for details.

6. OPTIONAL VERIFICATION
    python -m unittest discover -s tests -v
    python tests/verify_gui.py
    python tests/verify_auth.py
GUI verification needs a desktop. Auth verification uses local loopback
networking and mocked Steam replies, not a real account or login.

Artwork attribution and design references are in ATTRIBUTION.txt.
TEST_REPORT.txt records what was actually checked for this package.

PERSONAL ENVIRONMENT CONFIGURATION
Copy setup/python_path.example.txt to setup/python_path.txt. Replace the
contents with your own full python.exe path on one line without quotes.
Double-click launch.cmd. Install Pillow with that same interpreter if desired.
Alternatively activate your environment and run python main.py directly.
See the top-level README.md for commands and terminal-mode options.
