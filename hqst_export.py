import asyncio
import json
import configparser
import os
import csv
from datetime import datetime
from hqst.production import get_hqst_production

# Load config
config = configparser.ConfigParser()
config_file = 'config.ini'

mac_address = None
device_name = None
device_type = 'controller'
device_id = 1
read_char_uuid = "0000ffe1-0000-1000-8000-00805f9b34fb"
write_char_uuid = "0000ffe1-0000-1000-8000-00805f9b34fb"
power_multiplier = 0.5
generation_multiplier = 0.05

if os.path.exists(config_file):
    config.read(config_file)
    if 'hqst' in config:
        mac_address = config['hqst'].get('mac_address', None)
        device_name = config['hqst'].get('device_name', None)
        device_type = config['hqst'].get('device_type', 'controller')
        device_id = config['hqst'].getint('device_id', 1)
        read_char_uuid = config['hqst'].get('read_char_uuid', '0000ffe1-0000-1000-8000-00805f9b34fb')
        write_char_uuid = config['hqst'].get('write_char_uuid', '0000ffe1-0000-1000-8000-00805f9b34fb')
        power_multiplier = config['hqst'].getfloat('power_multiplier', 0.5)
        generation_multiplier = config['hqst'].getfloat('generation_multiplier', 0.05)

async def main():
    data = await get_hqst_production(
        mac_address=mac_address,
        device_name=device_name,
        device_type=device_type,
        device_id=device_id,
        read_char_uuid=read_char_uuid,
        write_char_uuid=write_char_uuid
    )
    
    if data:
        # Save latest reading to hqst.json
        output_json = "hqst.json"
        
        # Apply scaling multipliers to live data
        scaled_data = dict(data)
        scaled_data["pv_power"] = int(data.get("pv_power", 0) * power_multiplier)
        scaled_data["power_generation_today"] = int(data.get("power_generation_today", 0) * generation_multiplier)
        scaled_data["power_generation_total"] = int(data.get("power_generation_total", 0) * generation_multiplier)
        
        with open(output_json, "w") as f:
            json.dump(scaled_data, f, indent=4)
        
        # Append reading to hqst_history.csv
        csv_file = "hqst_history.csv"
        file_exists = os.path.exists(csv_file)
        
        fields = [
            "timestamp",
            "model",
            "pv_voltage",
            "pv_current",
            "pv_power",
            "battery_voltage",
            "battery_percentage",
            "battery_current",
            "controller_temperature",
            "power_generation_today",
            "power_generation_total"
        ]
        
        row = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "model": scaled_data.get("model", "Unknown"),
            "pv_voltage": scaled_data.get("pv_voltage", 0.0),
            "pv_current": scaled_data.get("pv_current", 0.0),
            "pv_power": scaled_data.get("pv_power", 0),
            "battery_voltage": scaled_data.get("battery_voltage", 0.0),
            "battery_percentage": scaled_data.get("battery_percentage", 0),
            "battery_current": scaled_data.get("battery_current", 0.0),
            "controller_temperature": scaled_data.get("controller_temperature", 0),
            "power_generation_today": scaled_data.get("power_generation_today", 0),
            "power_generation_total": scaled_data.get("power_generation_total", 0)
        }
        
        with open(csv_file, mode="a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)
        
        print("-" * 30)
        print("☀️ HQST Charge Controller Data ☀️")
        print("-" * 30)
        print(f"Timestamp:         {row['timestamp']}")
        print(f"Device:            {row['model']}")
        print(f"PV (Solar) Input:  {row['pv_voltage']:.2f} V @ {row['pv_current']:.2f} A ({row['pv_power']} W)")
        print(f"Battery:           {row['battery_voltage']:.2f} V ({row['battery_percentage']}% SOC)")
        print(f"Battery Current:   {row['battery_current']:.2f} A")
        print(f"Controller Temp:   {row['controller_temperature']} °C")
        print(f"Daily Production:  {row['power_generation_today']} Wh")
        print(f"Total Production:  {row['power_generation_total'] / 1000.0:.2f} kWh")
        print("-" * 30)
        print(f"Latest status saved to {output_json}")
        print(f"Historical record appended to {csv_file}")
        
        # Generate/update the production graph every minute
        print("� Generating/updating production graph...")
        try:
            from hqst.graph import generate_graph
            generate_graph(csv_path=csv_file)
        except Exception as graph_err:
            print(f"❌ Error generating graph: {graph_err}")
    else:
        print("❌ Failed to retrieve data from HQST charge controller.")

if __name__ == "__main__":
    asyncio.run(main())
