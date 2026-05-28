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

## Project Structure

- `export.py` - Enphase monitor main entry point
- `hqst_export.py` - HQST monitor main entry point
- `bin/daily.sh` - Daily task wrapper script
- `bin/hqst.sh` - Every-minute task wrapper script for HQST
- `enphase/` - Enphase production fetching module
- `hqst/` - HQST solar charge controller BLE module
- `config.ini` - Device credentials (not committed)
- `email_sender.py` - Email notification logic
