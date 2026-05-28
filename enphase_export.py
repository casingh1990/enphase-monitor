import os
import csv
import json
import asyncio
import configparser
import requests
import urllib3
from datetime import datetime

# Disable Insecure Request Warning since Enphase certificates are self-signed
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load config
config = configparser.ConfigParser()
config_file = 'config.ini'

ENVOY_IP1 = None
TOKEN1 = None
ENVOY_IP2 = None
TOKEN2 = None

if os.path.exists(config_file):
    config.read(config_file)
    if 'envoy1' in config:
        ENVOY_IP1 = config['envoy1'].get('ip', None)
        TOKEN1 = config['envoy1'].get('token', None)
    if 'envoy2' in config:
        ENVOY_IP2 = config['envoy2'].get('ip', None)
        TOKEN2 = config['envoy2'].get('token', None)

def parse_envoy_data(data):
    """
    Parses real-time power (W) and daily energy (Wh) from Enphase Envoy production.json.
    """
    w_now = 0.0
    wh_today = 0.0
    if not data:
        return w_now, wh_today
        
    for item in data.get('production', []):
        if item.get('type') in ['eim']:
            # Premium meter configuration
            w_now = float(item.get('wNow', 0.0))
            wh_today = float(item.get('whToday', 0.0))
            return w_now, wh_today
            
    # Fallback to standard inverter sums
    for item in data.get('production', []):
        if item.get('type') in ['inverters']:
            w_now = float(item.get('wNow', 0.0))
            wh_today = float(item.get('whToday', 0.0))
            return w_now, wh_today
            
    return w_now, wh_today

def fetch_envoy(ip, token):
    """
    Synchronously fetches production.json from a single Envoy.
    """
    if not ip:
        return None
    url = f"https://{ip}/production.json"
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        response = requests.get(url, headers=headers, verify=False, timeout=8)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"⚠️ Error querying Envoy at {ip}: {e}")
        return None

async def main():
    print(f"Fetching Enphase production data at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}...")
    
    # Run fetch operations concurrently in thread pool to prevent sequential blocking
    loop = asyncio.get_running_loop()
    e1_task = loop.run_in_executor(None, fetch_envoy, ENVOY_IP1, TOKEN1)
    e2_task = loop.run_in_executor(None, fetch_envoy, ENVOY_IP2, TOKEN2)
    
    e1_data, e2_data = await asyncio.gather(e1_task, e2_task)
    
    if not e1_data and not e2_data:
        print("❌ Failed to query both Enphase Envoy systems.")
        return

    e1_power, e1_daily = parse_envoy_data(e1_data)
    e2_power, e2_daily = parse_envoy_data(e2_data)
    
    total_power = e1_power + e2_power
    total_daily = e1_daily + e2_daily

    # Create output directory if it does not exist
    os.makedirs("production/data", exist_ok=True)

    # Save real-time summary to json
    enphase_json = "production/data/enphase.json"
    summary_data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "envoy1_power_w": e1_power,
        "envoy1_daily_wh": e1_daily,
        "envoy2_power_w": e2_power,
        "envoy2_daily_wh": e2_daily,
        "total_power_w": total_power,
        "total_daily_wh": total_daily,
    }
    with open(enphase_json, "w") as f:
        json.dump(summary_data, f, indent=4)

    # Append to CSV history
    csv_file = "production/data/enphase_history.csv"
    file_exists = os.path.exists(csv_file)
    
    fields = [
        "timestamp",
        "envoy1_power",
        "envoy2_power",
        "total_power",
        "envoy1_daily",
        "envoy2_daily",
        "total_daily"
    ]
    
    row = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "envoy1_power": e1_power,
        "envoy2_power": e2_power,
        "total_power": total_power,
        "envoy1_daily": e1_daily,
        "envoy2_daily": e2_daily,
        "total_daily": total_daily
    }
    
    with open(csv_file, mode="a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

    print("-" * 35)
    print("🌞 Enphase Home Solar System 🌞")
    print("-" * 35)
    print(f"Timestamp:       {row['timestamp']}")
    print(f"System 1 Output: {e1_power:.1f} W ({e1_daily/1000.0:.2f} kWh today)")
    print(f"System 2 Output: {e2_power:.1f} W ({e2_daily/1000.0:.2f} kWh today)")
    print(f"Combined Output: {total_power:.1f} W ({total_daily/1000.0:.2f} kWh today)")
    print("-" * 35)
    print(f"Latest status saved to {enphase_json}")
    print(f"Historical record appended to {csv_file}")
    
    # Generate/update the house production graph every minute
    print("📈 Generating production graph for Enphase...")
    try:
        from enphase.graph import generate_enphase_graph
        generate_enphase_graph(csv_path=csv_file)
    except Exception as graph_err:
        print(f"❌ Error generating Enphase graph: {graph_err}")

if __name__ == "__main__":
    asyncio.run(main())
