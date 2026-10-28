# Getting and configuring a personal Steam Web API key

**Demo Mode needs no key.** A key is only needed for live Steam library requests. If you already have a personal key, reuse it; creating a new key is unnecessary.

## Why a key is required

Steam sign-in and library access serve different purposes. OpenID identifies the Steam account. The Web API key authorises API requests such as reading the visible owned-game library. Logging in alone does not configure the key for this local application.

This project uses a standard **user Web API key**. You do not need a publisher key or a Steamworks publisher account.

## Get a key from Steam

1. Open the official [Steam Web API registration page](https://steamcommunity.com/dev/apikey).
2. Sign in on Steam's website and complete any Steam Guard verification requested there.
3. If a key is already displayed, use that key. Otherwise, follow the registration form, provide the domain name associated with your intended use, and agree to the Steam Web API Terms of Use if you accept them.
4. Complete any confirmation Steam requests, then copy the resulting key privately.

The logged-in form and eligibility checks can vary by account. If Steam blocks registration, follow the explanation shown by Steam; do not try to bypass it. The public registration URL redirects to sign-in until authenticated, so this guide does not claim to reproduce every field or account-specific requirement.

### What about the domain name?

Valve's documentation requires a domain name associated with the user key. For a project with a website, use the appropriate domain you control. This desktop application does not read that domain from a configuration file, host a public website, or deploy a server.

For local development, `localhost` may be accepted by the registration form, but the public documentation does not guarantee this. Use it only if Steam accepts it for your intended local use; otherwise follow the current form's requirements. Do not enter a third party's domain as if you owned it. An existing accepted key can be reused without buying a domain for this application.

## Recommended setup: a local text file

1. In the folder containing `main.py`, create **`steam_api_key.txt`**.
2. Paste only the key on one line, with no quotes, labels, spaces within the key, or JSON:

   ```text
   <paste your actual 32-character key here>
   ```

   The line above is an instruction placeholder, not a valid key. Replace the entire line with the actual key. The program accepts 32 hexadecimal characters (`0–9`, `a–f`, case-insensitive).

3. On Windows, enable **File name extensions** in File Explorer and check that the name is not `steam_api_key.txt.txt`.
4. Restart the application and choose **Connect Steam** or **Load SteamID**.

The configured key remains local. Do not include it in your submission archive, Padlet image, screenshot, or shared code.

## Alternative: environment variable

In PowerShell, set the variable for the current terminal session and start the application from that same session:

```powershell
$env:STEAM_WEB_API_KEY = 'PASTE_YOUR_ACTUAL_KEY_HERE'
& 'E:\Anaconda\envs\comp5310\python.exe' main.py
```

That Python path is the project's existing environment on the owner's computer. On another computer use its installed Python instead. A variable set this way does not automatically appear in applications launched separately from File Explorer.

The application checks **the environment variable first**, then `steam_api_key.txt`. If the environment contains an old or incorrect key, it overrides the file. Remove it for the current terminal session with:

```powershell
Remove-Item Env:STEAM_WEB_API_KEY -ErrorAction SilentlyContinue
```

## Library visibility and troubleshooting

| Symptom | What to check |
| --- | --- |
| Missing-key message | Put the file next to `main.py`, check its extension, or start from the terminal where the variable was set. |
| Invalid-key format | Supply only 32 hexadecimal characters; remove labels, quotes and placeholder text. |
| Key is rejected by Steam | Check the registered key on the official page and check whether a stale environment variable overrides your file. |
| No visible games | Review your Steam profile privacy settings, including Game details and playtime visibility. The API only returns details visible to the requester. |
| Registration unavailable | Follow Steam's account-specific instructions or use Demo Mode. |
| App does not open | This is a Python/startup issue; check `output/startup.log` and README.md. A Steam key is not required to open the app. |

Keep the key private. If it is exposed, manage or revoke it using Steam's official registration page, then update the local configuration.

## Official references

- [Steam Web API documentation and registration link](https://steamcommunity.com/dev)
- [User-key authentication requirements](https://partner.steamgames.com/doc/webapi_overview/auth)
- [GetOwnedGames and visibility requirements](https://partner.steamgames.com/doc/webapi/IPlayerService)

Public documentation checked on 28 October 2026. Registration was not performed on your behalf.
