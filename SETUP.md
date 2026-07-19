# Dechive GitHub Profile Engine

A GitHub Profile README package that turns recent contribution activity into a small animated record-transfer scene.

## Included

- Animated `dechive-record-engine.gif`
- Static preview PNG
- Original pixel skull sprite sheet
- Dechive logo SVG
- Python generator
- GitHub GraphQL contribution reader
- Daily GitHub Actions workflow
- Compact profile `README.md`

## Installation

1. Open the GitHub profile repository named exactly like your account: `Aprasaks/Aprasaks`.
2. Back up the existing `README.md`.
3. Copy every file and folder from this package into the repository root.
4. Commit and push.
5. Open **Actions → Update Dechive Profile Engine → Run workflow**.
6. Confirm that `assets/generated/dechive-record-engine.gif` was regenerated.

No personal access token is required. The workflow uses the repository's built-in `GITHUB_TOKEN`.

## Local generation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/generate.py
```

Without `GITHUB_TOKEN`, the script uses demo contribution data. In GitHub Actions it reads the real contribution calendar.

## Customization

Edit `config.json`:

- `github_username`
- `display_name`
- `site_url`
- `tagline`
- animation size and timing

Visual colors, movement, machine design, and skull sprite are defined in `scripts/generate.py`.

## Notes

- GitHub README pages do not run JavaScript. The animation is a generated GIF.
- The workflow regenerates the GIF once per day and can also be run manually.
- Scheduled GitHub Actions use UTC and may start a few minutes late.
