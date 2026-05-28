# Enphase Production Monitor

Fetches daily solar production data from Enphase Envoy devices and sends email reports.

## Setup

1. Copy `config.ini.example` to `config.ini` and add your credentials:

```bash
cp config.ini.example config.ini
```

2. Edit `config.ini` with your actual IP addresses and tokens.

3. Generate tokens at https://entrez.enphaseenergy.com/ (required for Firmware v7.x.x+)

4. Configure email settings in `email_sender.py`

## Usage

```bash
python export.py
```

## Project Structure

- `export.py` - Main entry point
- `enphase/production.py` - Production data fetching module
- `config.ini` - Device credentials (not committed)
- `email_sender.py` - Email notification logic
