# GitMeName

```
   █████████   ███   █████    ██████   ██████          ██████   █████                                   
  ███░░░░░███ ░░░   ░░███    ░░██████ ██████          ░░██████ ░░███                                    
 ███     ░░░  ████  ███████   ░███░█████░███   ██████  ░███░███ ░███   ██████   █████████████    ██████ 
░███         ░░███ ░░░███░    ░███░░███ ░███  ███░░███ ░███░░███░███  ░░░░░███ ░░███░░███░░███  ███░░███
░███    █████ ░███   ░███     ░███ ░░░  ░███ ░███████  ░███ ░░██████   ███████  ░███ ░███ ░███ ░███████ 
░░███  ░░███  ░███   ░███ ███ ░███      ░███ ░███░░░   ░███  ░░█████  ███░░███  ░███ ░███ ░███ ░███░░░  
 ░░█████████  █████  ░░█████  █████     █████░░██████  █████  ░░█████░░████████ █████░███ █████░░██████ 
  ░░░░░░░░░  ░░░░░    ░░░░░  ░░░░░     ░░░░░  ░░░░░░  ░░░░░    ░░░░░  ░░░░░░░░ ░░░░░ ░░░ ░░░░░  ░░░░░░  
                                                                                                        

```

**GitMeName** is a fast, async, production-ready CLI for checking username
availability across GitHub, Reddit, Twitch, and 9 other platforms — using
official APIs where they exist, and smart URL-based detection everywhere
else. Built with [Rich](https://github.com/Textualize/rich) for a clean
terminal UI: live progress bars, a live statistics panel, and colored
result tables.

---

## Features

- **API-first**: GitHub, Reddit, and Twitch are checked via their official,
  documented APIs — never scraped.
- **Smart URL fallback**: TikTok, Instagram, Twitter/X, Telegram, Snapchat,
  Pinterest, Kick, Steam, and Roblox are checked by requesting the public
  profile URL and inspecting status codes, redirects, and page content.
- **Async everything**: built on `aiohttp` with connection pooling, a
  configurable concurrency limit, and automatic retries with exponential
  backoff.
- **Never guesses blindly**: every result is `AVAILABLE`, `TAKEN`, or
  `UNKNOWN` (network error, rate limiting, or bot protection) — GitMeName
  is honest when it can't be sure.
- **Fully configurable**: every platform's URL, headers, timeout, and
  detection rules live in `config.yaml` — no code changes needed to tune
  them.
- **Structured logging**: every single check is logged with timestamp,
  platform, username, method, response code, response time, and result.
- **Rich terminal output**: live progress, live stats, and a final colored
  results table (Platform / Username / Status / Response Time / Method).

---

## Installation

### Requirements
- Python 3.10+
- pip

### Standard install (Linux / macOS / Windows)

```bash
git clone https://github.com/ru-3/GitMeName.git
cd gitmename
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Termux (Android)

```bash
pkg update && pkg upgrade -y
pkg install python git -y

git clone https://github.com/yourname/gitmename.git
cd gitmename

pip install --upgrade pip
pip install -r requirements.txt

python main.py
```

> **Termux tip:** if `aiohttp` fails to build a wheel, install the build
> toolchain first: `pkg install clang python-dev libffi openssl -y`, then
> re-run `pip install -r requirements.txt`.

---

## Usage

```bash
python main.py
```

You'll be walked through an interactive flow:

1. Confirm you're ready to start.
2. Pick a platform from the numbered list (API-backed platforms are
   listed first).
3. Choose a username generation mode (`3`, `4`, `near_3`, `near_4`, or
   `custom`) and, optionally, a separator character.
4. Choose how many candidate usernames to generate and check.
5. Watch a live progress bar and live statistics panel while checks run.
6. Get a final Rich table of every result, plus any available usernames
   saved to `output/`.

### Example output

```
┏━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━┓
┃ Platform┃ Username    ┃  Status   ┃ Response Time ┃ Method ┃
┡━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━┩
│ GitHub  │ x7q         │ AVAILABLE │        142 ms │  API   │
│ GitHub  │ kx9         │ TAKEN     │         98 ms │  API   │
│ GitHub  │ zz1         │ UNKNOWN   │       10021 ms│  API   │
└─────────┴─────────────┴───────────┴───────────────┴────────┘
```

---

## Supported Platforms

| Platform    | Method | Detection Source                              |
|-------------|--------|------------------------------------------------|
| GitHub      | API    | `GET api.github.com/users/{username}`           |
| Reddit      | API    | `GET reddit.com/api/username_available.json`    |
| Twitch      | API    | `GET api.twitch.tv/helix/users` (OAuth)         |
| TikTok      | URL    | `tiktok.com/@{username}`                        |
| Instagram   | URL    | `instagram.com/{username}/`                     |
| Twitter/X   | URL    | `x.com/{username}`                              |
| Telegram    | URL    | `t.me/{username}`                               |
| Snapchat    | URL    | `snapchat.com/add/{username}`                   |
| Pinterest   | URL    | `pinterest.com/{username}/`                     |
| Kick        | URL    | `kick.com/{username}`                           |
| Steam       | URL    | `steamcommunity.com/id/{username}`              |
| Roblox      | URL    | `roblox.com/users/profile?username={username}`  |

**API** platforms use an official, documented endpoint. **URL** platforms
have no public availability API, so GitMeName requests the public profile
page and infers availability from the HTTP status code, redirects, and
page content (see [Configuration](#configuration)).

- **GitHub**: works out of the box (60 requests/hour); add a token to
  raise the limit to 5,000/hour.
- **Reddit**: works out of the box, no credentials needed.
- **Twitch**: requires `TWITCH_CLIENT_ID` / `TWITCH_CLIENT_SECRET` from
  [dev.twitch.tv/console/apps](https://dev.twitch.tv/console/apps).

---

## Configuration

Copy the example config and edit it:

```bash
cp config.example.yaml config.yaml
```

`config.yaml` controls:

- **`network`**: timeout, retry count/backoff, max concurrent requests,
  user agent.
- **`logging`**: log level, log file path, rotation size/backups.
- **`output`**: where available usernames get saved.
- **`auth`**: `github_token`, `twitch_client_id`, `twitch_client_secret`
  (env vars `GITHUB_TOKEN` / `TWITCH_CLIENT_ID` / `TWITCH_CLIENT_SECRET`
  always take priority — never commit real secrets to `config.yaml`).
- **`platforms`**: per-platform URL template, status-code rules, and
  "not found" phrases for every URL-based checker — tune detection
  without touching any code.

Example platform override:

```yaml
platforms:
  tiktok:
    profile_url: "https://www.tiktok.com/@{username}"
    not_found_status: [404]
    found_status: [200]
    ambiguous_status: [403, 429, 503]
    not_found_phrases:
      - "couldn't find this account"
      - "user not found"
    timeout: 12
```

---

## Logging

Every check writes one structured line to `logs/gitmename.log`:

```
2026-07-26 10:00:00 | INFO | gitmename | platform=GitHub username=x7q method=API response_code=404 response_time=0.142s result=available
```

Logs rotate automatically based on `logging.max_bytes` / `backup_count`.

---

## Troubleshooting

| Problem                                   | Fix                                                                 |
|--------------------------------------------|----------------------------------------------------------------------|
| Lots of `UNKNOWN` results on a URL platform | The site is likely rate-limiting or bot-protecting you — lower `max_concurrent_requests`, raise `timeout`, or slow down. |
| GitHub returns `UNKNOWN` after a while       | You hit the 60/hour anonymous limit — add `GITHUB_TOKEN`.            |
| Twitch always returns `UNKNOWN`              | Set `TWITCH_CLIENT_ID` / `TWITCH_CLIENT_SECRET` (env vars or config).|
| `aiohttp` fails to install on Termux          | `pkg install clang python-dev libffi openssl -y`, then reinstall.    |
| Detection seems wrong for a platform          | Sites change their markup — tune `platforms.<name>` in `config.yaml`.|

---

## Project Structure

```
GitMeName/
├── main.py                 # CLI entrypoint & Rich UI
├── banner.py                # ASCII art logo / startup banner
├── config.py                 # Config loading (defaults + config.yaml + env)
├── config.example.yaml       # Copy to config.yaml and customize
├── generator.py               # Candidate username generation
├── requirements.txt
├── checker/
│   ├── base.py                # Status / CheckResult / PlatformChecker
│   ├── url_checker.py         # Generic URL-based fallback checker
│   ├── registry.py            # Platform registry
│   ├── github.py, reddit.py, twitch.py        # API-backed checkers
│   └── tiktok.py, instagram.py, twitter.py,   # URL-fallback checkers
│       telegram.py, snapchat.py, pinterest.py,
│       kick.py, steam.py, roblox.py
├── utils/
│   ├── http.py                # aiohttp client: pooling, retries, timeouts
│   ├── logger.py               # Rotating file logger + structured log_check()
│   └── stats.py                # Live run statistics
├── logs/
└── output/
```

---

## License

MIT License — do what you want, no warranty. See `LICENSE` for full text.
