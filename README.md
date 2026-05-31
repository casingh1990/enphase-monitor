# Solar Production Monitor

Fetches daily solar production data from Enphase Envoy devices (Enphase microinverters) and real-time solar data from an HQST/Renogy charge controller via Bluetooth.

## Setup

1. Copy `config.ini.example` to `config.ini` and add your credentials/devices:

```bash
cp config.ini.example config.ini
```

2. Edit `config.ini` with your Envoy details and HQST BLE MAC address.

3. Generate Enphase tokens at https://entrez.enphaseenergy.com/ (required for Firmware v7.x.x+)

4. Configure email settings in `email_sender.py`

## Usage

### Enphase Envoy Monitor

Runs daily to get Enphase Envoy production totals and send email reports.

```bash
pipenv run python export.py
```

### HQST Solar Charge Controller Monitor

Reads from the HQST Solar Charge Controller over BLE. Designed to run every minute via cron.

```bash
pipenv run python hqst_export.py
```

#### Cron Setup for HQST (Every minute)

Run `crontab -e` and add the following entry:

```cron
* * * * * /home/amit/code/enphase/bin/hqst.sh
```

### Enphase Consumption Monitor

Fetches whole-home consumption and net grid telemetry. Implements dual-gateway mathematical calibration for parallel CT wiring configurations (`ct_scale_factor` defaulted to `2.0`).

```bash
pipenv run consumption
```

#### Cron Setup for Consumption (Every minute)

```cron
* * * * * /home/amit/code/enphase/bin/consumption.sh
```

### WordPress Auto-Poster

Automatically uploads daily solar charts (House Solar, Shed Solar, Consumption) and posts unified HTML summaries of your daily metrics to WordPress using the REST API.

```bash
pipenv run post
```

#### Cron Setup for WordPress Updates (Every 15-30 minutes)

```cron
*/15 * * * * /home/amit/code/enphase/bin/post.sh
```

### Live Telemetry Flask API

Serves live, calibrated real-time data directly from both Envoy gateways. Returns JSON containing live and daily combined production, consumption, net grid import/export, and per-Envoy details.

To start the API server on port 5000:

```bash
pipenv run api
```

#### Endpoint Structure

`GET /api/solar`
```json
{
  "timestamp": "2026-05-29 17:35:12",
  "production": {
    "w": 4200.0,
    "wh_today": 18450.0,
    "kwh_today": 18.45
  },
  "consumption": {
    "w": 1850.0,
    "wh_today": 12300.0,
    "kwh_today": 12.30
  },
  "import": {
    "w": 0.0,
    "wh_today": 2000.0,
    "kwh_today": 2.0
  },
  "export": {
    "w": 2350.0,
    "wh_today": 8150.0,
    "kwh_today": 8.15
  },
  "net_grid": {
    "w": -2350.0,
    "wh_today": -6150.0,
    "kwh_today": -6.15,
    "status": "exporting"
  }
}
```

## Project Structure

- `export.py` - Enphase daily monitor / email notification main entry point
- `enphase_export.py` - Enphase live production logging script (run every minute)
- `enphase_consumption.py` - Calibrated consumption and grid logger (run every minute)
- `hqst_export.py` - HQST monitor main entry point (run every minute)
- `app.py` - Live Enphase Telemetry Flask API
- `utils/config.py` - Centralized config loader (reads from `config.ini`)
- `utils/update_post.py` - WordPress post updater / media uploader
- `bin/` - Scheduled cron task shell wrappers (daily, hqst, enphase, consumption, post, api)
- `enphase/` - Enphase production fetching and graph modules
- `hqst/` - HQST solar charge controller BLE and graph modules
- `config.ini` - Device credentials (not committed)
- `email_sender.py` - Inline HTML email notification engine
