"""
Combined Enphase exporter module.
Concurrently fetches telemetry from both Envoy systems, calculates calibrated
solar production and household consumption, saves summaries, logs history,
and generates/updates daily visualization graphs.
"""

import os
import csv
import json
import asyncio
import requests
import urllib3
from datetime import datetime
from utils.config import ENVOY_IP1, TOKEN1, ENVOY_IP2, TOKEN2, CT_SCALE_FACTOR

# Disable Insecure Request Warning since Enphase certificates are self-signed
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def parse_solar_data(data):
    """
    Parses real-time solar power (W) and daily solar energy (Wh) from an Envoy.
    """
    w_now = 0.0
    wh_today = 0.0
    if not data:
        return w_now, wh_today

    # Try standard 'eim' type (production meter)
    for item in data.get('production', []):
        if item.get('type') in ['eim']:
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


def parse_consumption_data(data):
    """
    Parses real-time power (W) and daily energy (Wh) for total and net consumption from Envoy 1.
    """
    total_w = 0.0
    total_wh = 0.0
    net_w = 0.0
    net_wh = 0.0
    if not data:
        return total_w, total_wh, net_w, net_wh

    for item in data.get('consumption', []):
        m_type = item.get('measurementType')
        if m_type == 'total-consumption':
            total_w = float(item.get('wNow', 0.0))
            total_wh = float(item.get('whToday', 0.0))
        elif m_type == 'net-consumption':
            net_w = float(item.get('wNow', 0.0))
            net_wh = float(item.get('whToday', 0.0))

    return total_w, total_wh, net_w, net_wh


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
    print(f"Fetching Enphase telemetry at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}...")

    # Run fetch operations concurrently in thread pool to prevent sequential blocking
    loop = asyncio.get_running_loop()
    e1_task = loop.run_in_executor(None, fetch_envoy, ENVOY_IP1, TOKEN1)
    e2_task = loop.run_in_executor(None, fetch_envoy, ENVOY_IP2, TOKEN2)

    e1_data, e2_data = await asyncio.gather(e1_task, e2_task)

    if not e1_data and not e2_data:
        print("❌ Failed to query both Enphase Envoy systems.")
        return

    # Create output directory if it does not exist
    os.makedirs("production/data", exist_ok=True)
    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # -------------------------------------------------------------------------
    # PART 1: SOLAR PRODUCTION PROCESSING
    # -------------------------------------------------------------------------
    s1_w, s1_wh = parse_solar_data(e1_data)
    s2_w, s2_wh = parse_solar_data(e2_data)

    total_production_w = s1_w + s2_w
    total_production_wh = s1_wh + s2_wh

    # Save live solar summary to JSON
    enphase_json = "production/data/enphase.json"
    production_summary = {
        "timestamp": timestamp_str,
        "envoy1_power_w": s1_w,
        "envoy1_daily_wh": s1_wh,
        "envoy2_power_w": s2_w,
        "envoy2_daily_wh": s2_wh,
        "total_power_w": total_production_w,
        "total_daily_wh": total_production_wh,
    }
    with open(enphase_json, "w") as f:
        json.dump(production_summary, f, indent=4)

    # Append to solar CSV history
    prod_csv_file = "production/data/enphase_history.csv"
    prod_file_exists = os.path.exists(prod_csv_file)
    prod_fields = [
        "timestamp",
        "envoy1_power",
        "envoy2_power",
        "total_power",
        "envoy1_daily",
        "envoy2_daily",
        "total_daily"
    ]
    prod_row = {
        "timestamp": timestamp_str,
        "envoy1_power": s1_w,
        "envoy2_power": s2_w,
        "total_power": total_production_w,
        "envoy1_daily": s1_wh,
        "envoy2_daily": s2_wh,
        "total_daily": total_production_wh
    }
    with open(prod_csv_file, mode="a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=prod_fields)
        if not prod_file_exists:
            writer.writeheader()
        writer.writerow(prod_row)

    # -------------------------------------------------------------------------
    # PART 2: HOUSEHOLD CONSUMPTION PROCESSING (Envoy 1 only)
    # -------------------------------------------------------------------------
    if e1_data:
        # Extract raw readings from Envoy 1
        raw_total_w, raw_total_wh, raw_net_w, raw_net_wh = parse_consumption_data(e1_data)

        # -------------------------------------------------------------------------
        # MATHEMATICAL CALIBRATION FOR TWO SYSTEMS CONNECTED TO THE SAME HOUSE
        # -------------------------------------------------------------------------
        # Envoy 1's CT measures the net grid current (which physically includes System 2 solar).
        # Correct the net grid measurement with ct_scale_factor (e.g. 2.0 if CT wires are paralleled).
        true_net_grid_w = raw_net_w * CT_SCALE_FACTOR
        true_net_grid_wh = raw_net_wh * CT_SCALE_FACTOR

        # Combined true household consumption: Total Solar + True Net Grid State
        true_consumption_w = s1_w + s2_w + true_net_grid_w
        true_consumption_wh = s1_wh + s2_wh + true_net_grid_wh

        # Fallback/Safety ceiling: Consumption cannot be negative in normal houses
        if true_consumption_w < 0:
            true_consumption_w = 0.0
        if true_consumption_wh < 0:
            true_consumption_wh = 0.0

        # Save real-time summary to JSON
        consumption_json = "production/data/consumption.json"
        consumption_summary = {
            "timestamp": timestamp_str,
            "total_consumption_w": true_consumption_w,
            "total_consumption_wh_today": true_consumption_wh,
            "net_consumption_w": true_net_grid_w,
            "net_consumption_wh_today": true_net_grid_wh,
            "raw_envoy1_consumption_w": raw_total_w,
            "raw_envoy1_net_w": raw_net_w,
            "system1_solar_w": s1_w,
            "system2_solar_w": s2_w,
            "ct_scale_factor": CT_SCALE_FACTOR
        }
        with open(consumption_json, "w") as f:
            json.dump(consumption_summary, f, indent=4)

        # Append to consumption CSV history
        cons_csv_file = "production/data/consumption_history.csv"
        cons_file_exists = os.path.exists(cons_csv_file)
        cons_fields = [
            "timestamp",
            "total_consumption_w",
            "total_consumption_wh_today",
            "net_consumption_w",
            "net_consumption_wh_today"
        ]
        cons_row = {
            "timestamp": timestamp_str,
            "total_consumption_w": true_consumption_w,
            "total_consumption_wh_today": true_consumption_wh,
            "net_consumption_w": true_net_grid_w,
            "net_consumption_wh_today": true_net_grid_wh
        }
        with open(cons_csv_file, mode="a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=cons_fields)
            if not cons_file_exists:
                writer.writeheader()
            writer.writerow(cons_row)
    else:
        print("⚠️ Envoy 1 offline; skipping consumption processing.")

    # -------------------------------------------------------------------------
    # PRINT RESULTS
    # -------------------------------------------------------------------------
    print("-" * 45)
    print("🌞 Enphase Combined Telemetry Summary 🌞")
    print("-" * 45)
    print(f"Timestamp:       {timestamp_str}")
    print(f"System 1 Solar:  {s1_w:.1f} W ({s1_wh/1000.0:.2f} kWh today)")
    print(f"System 2 Solar:  {s2_w:.1f} W ({s2_wh/1000.0:.2f} kWh today)")
    print(f"Combined Solar:  {total_production_w:.1f} W ({total_production_wh/1000.0:.2f} kWh today)")
    if e1_data:
        print(f"True House Load: {true_consumption_w:.1f} W ({true_consumption_wh/1000.0:.2f} kWh today)")
        print(f"True Grid State: {true_net_grid_w:.1f} W ({true_net_grid_wh/1000.0:.2f} kWh today)")
    print("-" * 45)

    # -------------------------------------------------------------------------
    # GENERATE/UPDATE VISUALIZATION GRAPHS
    # -------------------------------------------------------------------------
    print("📈 Generating visualization graphs...")
    try:
        from enphase.graph import generate_enphase_graph
        generate_enphase_graph(csv_path=prod_csv_file)
        print("✔ Production graph updated.")
    except Exception as graph_err:
        print(f"❌ Error generating Enphase production graph: {graph_err}")

    if e1_data:
        try:
            from enphase.consumption_graph import generate_consumption_graph
            generate_consumption_graph(csv_path=cons_csv_file)
            print("✔ Consumption graph updated.")
        except Exception as graph_err:
            print(f"❌ Error generating Enphase consumption graph: {graph_err}")

        try:
            from enphase.comparison_graph import generate_comparison_graph
            generate_comparison_graph(prod_csv_path=prod_csv_file, cons_csv_path=cons_csv_file)
            print("✔ Comparison graph updated.")
        except Exception as graph_err:
            print(f"❌ Error generating Enphase comparison graph: {graph_err}")


if __name__ == "__main__":
    asyncio.run(main())
