"""
Flask API to serve live calibrated Enphase solar production, consumption,
import, and export data directly from Envoy gateways.
"""

import os
from concurrent.futures import ThreadPoolExecutor
import requests
import urllib3
from datetime import datetime
from flask import Flask, jsonify, request
from utils.config import ENVOY_IP1, TOKEN1, ENVOY_IP2, TOKEN2, CT_SCALE_FACTOR

# Disable Insecure Request Warning since Enphase certificates are self-signed
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)


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


def fetch_envoy(ip, token):
    """
    Synchronously fetches production.json from an Envoy.
    """
    if not ip:
        return None
    url = f"https://{ip}/production.json"
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        response = requests.get(url, headers=headers, verify=False, timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        app.logger.warning(f"Error querying Envoy at {ip}: {e}")
        return None


@app.route('/real-time', methods=['GET'])
def get_solar_data():
    """
    Fetches real-time telemetry from both Envoys, applies the CT parallel-wiring
    calibration, and returns combined real-time and daily totals.
    """
    # Run requests concurrently in a thread pool to avoid sequential blocking
    with ThreadPoolExecutor(max_workers=2) as executor:
        e1_future = executor.submit(fetch_envoy, ENVOY_IP1, TOKEN1)
        e2_future = executor.submit(fetch_envoy, ENVOY_IP2, TOKEN2)
        e1_data = e1_future.result()
        e2_data = e2_future.result()

    if not e1_data:
        return jsonify({
            "error": "Failed to query Envoy 1 (the main system with consumption CTs)."
        }), 503

    # Extract raw readings from Envoy 1
    raw_total_w, raw_total_wh, raw_net_w, raw_net_wh = parse_consumption_data(e1_data)
    s1_w, s1_wh = parse_solar_data(e1_data)

    # Extract raw readings from Envoy 2
    s2_w, s2_wh = 0.0, 0.0
    envoy2_status = "active"
    if e2_data:
        s2_w, s2_wh = parse_solar_data(e2_data)
    else:
        envoy2_status = "offline/missing"

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

    # Calculate real-time import/export power (W)
    import_w = max(0.0, true_net_grid_w)
    export_w = max(0.0, -true_net_grid_w)

    # Calculate daily import/export energy (Wh)
    import_wh_today = max(0.0, true_net_grid_wh)
    export_wh_today = max(0.0, -true_net_grid_wh)

    # Combined solar production
    combined_production_w = s1_w + s2_w
    combined_production_wh_today = s1_wh + s2_wh

    response_payload = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "production": {
            "w": combined_production_w,
            "wh_today": combined_production_wh_today,
            "kwh_today": round(combined_production_wh_today / 1000.0, 3)
        },
        "consumption": {
            "w": true_consumption_w,
            "wh_today": true_consumption_wh,
            "kwh_today": round(true_consumption_wh / 1000.0, 3)
        },
        "import": {
            "w": import_w,
            "wh_today": import_wh_today,
            "kwh_today": round(import_wh_today / 1000.0, 3)
        },
        "export": {
            "w": export_w,
            "wh_today": export_wh_today,
            "kwh_today": round(export_wh_today / 1000.0, 3)
        },
        "net_grid": {
            "w": true_net_grid_w,
            "wh_today": true_net_grid_wh,
            "kwh_today": round(true_net_grid_wh / 1000.0, 3),
            "status": "exporting" if true_net_grid_w < 0 else "importing"
        },
        "details": {
            "envoy1": {
                "production_w": s1_w,
                "production_wh_today": s1_wh,
                "raw_consumption_w": raw_total_w,
                "raw_consumption_wh_today": raw_total_wh,
                "raw_net_w": raw_net_w,
                "raw_net_wh_today": raw_net_wh
            },
            "envoy2": {
                "status": envoy2_status,
                "production_w": s2_w,
                "production_wh_today": s2_wh
            },
            "ct_scale_factor": CT_SCALE_FACTOR
        }
    }

    return jsonify(response_payload)


@app.route('/health', methods=['GET'])
def health_check():
    """Simple API health check endpoint."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })


if __name__ == '__main__':
    # Listen on all interfaces on port 5000 by default
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
