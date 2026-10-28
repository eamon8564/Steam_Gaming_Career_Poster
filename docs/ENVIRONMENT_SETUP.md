# Using your own Python environment

You can run this project with your own Python installation. The author's Anaconda path is not required. Extract the complete archive and keep all supplied subfolders beside `main.py`.

## Option 1: configure double-click startup on Windows

1. Find the full path to your own **`python.exe`**, for example `D:\Anaconda\envs\my_project\python.exe`. Use the executable path, not just the environment folder.
2. Copy `setup/python_path.example.txt` to **`setup/python_path.txt`**.
3. Replace its contents with your actual executable path, on one line without quotation marks:

   ```text
   D:\Anaconda\envs\my_project\python.exe
   ```

4. Open PowerShell in the project root, where `main.py` is located. To install Pillow for cover previews and PNG export, run the following using your actual interpreter path:

   ```powershell
   & 'D:\Anaconda\envs\my_project\python.exe' -m pip install -r .\setup\requirements.txt
   ```

5. Double-click **`launch.cmd`** in the project root.

Replace the example path with the interpreter on your computer. You do not need to edit any source code or the launcher. The author's existing development environment remains `E:\Anaconda\envs\comp5310\python.exe`.

## Option 2: run your interpreter directly

In the project root, run:

```powershell
& 'D:\Anaconda\envs\my_project\python.exe' main.py
```

Alternatively, activate your environment using your usual method and run:

```console
python main.py
```

Direct execution does not require `setup/python_path.txt`.

## Requirements

- Python 3.10 or later. Actual development and verification used Python 3.12.13; every supported version has not been individually tested.
- The interactive window requires **Tkinter/Tcl/Tk and a graphical desktop**. Check with `python -m tkinter`, using the same environment that will run the project.
- **Pillow** is optional and provides in-app artwork previews and PNG export. SVG export does not require Pillow.
- Internet and a personal Steam Web API key are required only for live library access. The offline demonstration requires neither.

In a terminal-only environment, such as Ed or a remote shell, the entry point falls back to fictional demo statistics and exports SVG. You can explicitly select that mode:

```console
python main.py --no-gui
```

Download the generated file from `output/` and open it in a local browser. This mode does not offer an interactive window or load your real Steam library. The no-display fallback has been simulated and tested locally, including without third-party libraries; the user's Sahara/Python 3.14 environment has not been directly tested.

## Windows launcher selection order

1. `STEAM_POSTER_PYTHON` environment variable, if set.
2. `setup/python_path.txt`, if present.
3. The author's existing `E:\Anaconda\envs\comp5310\python.exe`, if it exists on the computer.
4. The project's `.venv\Scripts\python.exe`, if present.
5. System `python`, followed by Windows Python launcher `py -3`.

An invalid explicit interpreter path produces an error rather than silently choosing another environment. Python startup errors are recorded in `output/startup.log`.

`STEAM_POSTER_PYTHON` specifies an executable path; `STEAM_WEB_API_KEY` specifies a Steam credential. These are separate settings. The personal key file remains **`steam_api_key.txt` beside `main.py`**. Do not include your real key when sharing the project, and do not distribute your personal `setup/python_path.txt` as a required setting for other users.
