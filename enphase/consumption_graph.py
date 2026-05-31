import os
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import json

def generate_consumption_graph(csv_path="production/data/consumption_history.csv", output_dir="production/images/house"):
    """
    Reads the Enphase consumption history CSV, filters for today's data,
    and generates a beautiful household consumption/load graph.
    """
    if not os.path.exists(csv_path):
        print(f"⚠️ Cannot generate graph: {csv_path} does not exist.")
        return False

    os.makedirs(output_dir, exist_ok=True)
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    times = []
    total_loads = []
    net_grids = []

    total_consumption_today = 0
    net_grid_today_wh = 0
    
    # Read history data
    with open(csv_path, mode="r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ts_str = row.get("timestamp", "")
            if ts_str.startswith(today_str):
                try:
                    ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                    times.append(ts)
                    total_loads.append(float(row.get("total_consumption_w", 0.0)))
                    net_grids.append(float(row.get("net_consumption_w", 0.0)))
                    total_consumption_today += float(row.get("total_consumption_w", 0.0))
                    net_grid_today_wh += float(row.get("net_consumption_w", 0.0))
                except Exception:
                    continue

    os.makedirs("production/data", exist_ok=True)
    summary_json = "production/data/consumption.json"
    summary_data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_consumption_w": total_consumption_today,
        "total_consumption_wh_today": net_grid_today_wh,
        "net_consumption_w": "0",
        "net_consumption_wh_today": net_grid_today_wh,
        "raw_envoy1_consumption_w": "0",
        "raw_envoy1_net_w": "0",
        "system1_solar_w": "0",
        "system2_solar_w": "0",
        "ct_scale_factor": 2.0
    }
    with open(summary_json, "w") as f:
        json.dump(summary_data, f, indent=4)
    

    if not times:
        print("⚠️ No Enphase consumption records found for today yet.")
        return False

    # Create the plot
    fig, ax = plt.subplots(figsize=(10, 5), dpi=150)
    
    # Plot Total Load curve (Red/Amber representing power usage)
    ax.plot(times, total_loads, color="#ef4444", linewidth=2.5, label="Total Home Load (Consumption)")
    ax.fill_between(times, total_loads, color="#fee2e2", alpha=0.4)
    
    # Plot Net Grid Import/Export curve (Gray representing grid dependency)
    ax.plot(times, net_grids, color="#6b7280", linewidth=1.5, linestyle="--", label="Net Grid Import/Export")
    
    # Style the axes
    ax.set_title(f"House Power Consumption - {datetime.now().strftime('%B %d, %Y')}", fontsize=14, fontweight="bold", color="#1f2937")
    ax.set_xlabel("Time of Day", fontsize=11, color="#4b5563")
    ax.set_ylabel("Power (Watts)", fontsize=11, color="#4b5563")
    
    # Format x-axis time labels nicely
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))
    fig.autofmt_xdate()
    
    # Add subtle gridlines
    ax.grid(True, linestyle="--", alpha=0.5, color="#e5e7eb")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#d1d5db")
    ax.spines["bottom"].set_color("#d1d5db")
    
    # Add a smart legend below the plot (horizontal layout)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.18), ncol=2, frameon=True, facecolor="white", edgecolor="#e5e7eb")
    
    # Get peak metrics to show in annotation
    peak_load = max(total_loads)
    latest_load = total_loads[-1]
    
    # Display annotations in the bottom-left corner of the plot
    ax.text(0.02, 0.05, f"Peak Load: {peak_load:.1f} W\nLatest Load: {latest_load:.1f} W", 
            transform=ax.transAxes, fontsize=10, verticalalignment='bottom',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='#ffffff', edgecolor='#e5e7eb', alpha=0.9))
    
    # Construct filename based on current date
    timestamp_filename = datetime.now().strftime("%Y%m%d")
    output_filename = os.path.join(output_dir, f"consumption_{timestamp_filename}.png")
    
    # Save the beautiful plot
    plt.tight_layout()
    plt.savefig(output_filename, facecolor='white', bbox_inches='tight')
    plt.close()
    
    print(f"📈 Consumption graph generated successfully: {output_filename}")
    return True

if __name__ == "__main__":
    generate_consumption_graph()
