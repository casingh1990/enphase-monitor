import os
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

def generate_enphase_graph(csv_path="production/data/enphase_history.csv", output_dir="production/images/house"):
    """
    Reads the Enphase history CSV, filters for today's data,
    and generates a beautiful stacked or multi-line production graph.
    """
    if not os.path.exists(csv_path):
        print(f"⚠️ Cannot generate graph: {csv_path} does not exist.")
        return False

    os.makedirs(output_dir, exist_ok=True)
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    times = []
    envoy1_powers = []
    envoy2_powers = []
    total_powers = []
    
    # Read history data
    with open(csv_path, mode="r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ts_str = row.get("timestamp", "")
            if ts_str.startswith(today_str):
                try:
                    ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                    times.append(ts)
                    envoy1_powers.append(float(row.get("envoy1_power", 0.0)))
                    envoy2_powers.append(float(row.get("envoy2_power", 0.0)))
                    total_powers.append(float(row.get("total_power", 0.0)))
                except Exception:
                    continue

    if not times:
        print("⚠️ No Enphase production records found for today yet.")
        return False

    # Create the plot
    fig, ax = plt.subplots(figsize=(10, 5), dpi=150)
    
    # Plot smooth area curves for Envoy 1, Envoy 2, and the combined Total
    ax.plot(times, total_powers, color="#0284c7", linewidth=2.5, label="Total Production")
    ax.fill_between(times, total_powers, color="#e0f2fe", alpha=0.4)
    
    ax.plot(times, envoy1_powers, color="#0ea5e9", linewidth=1.5, linestyle="--", label="System 1 (Envoy 1)", alpha=0.8)
    ax.plot(times, envoy2_powers, color="#38bdf8", linewidth=1.5, linestyle=":", label="System 2 (Envoy 2)", alpha=0.8)
    
    # Style the axes
    ax.set_title(f"House Solar Production - {datetime.now().strftime('%B %d, %Y')}", fontsize=14, fontweight="bold", color="#1f2937")
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
    
    # Add a smart legend
    ax.legend(loc="upper right", frameon=True, facecolor="white", edgecolor="#e5e7eb")
    
    # Get peak metrics to show in annotation
    peak_power = max(total_powers)
    latest_power = total_powers[-1]
    
    # Display annotations
    ax.text(0.02, 0.95, f"Peak: {peak_power:.1f} W\nLatest: {latest_power:.1f} W", 
            transform=ax.transAxes, fontsize=10, verticalalignment='top',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='#ffffff', edgecolor='#e5e7eb', alpha=0.9))
    
    # Construct filename based on current date
    timestamp_filename = datetime.now().strftime("%Y%m%d")
    output_filename = os.path.join(output_dir, f"{timestamp_filename}.png")
    
    # Save the beautiful plot
    plt.tight_layout()
    plt.savefig(output_filename, facecolor='white', bbox_inches='tight')
    plt.close()
    
    print(f"📈 Enphase production graph generated successfully: {output_filename}")
    return True

if __name__ == "__main__":
    generate_enphase_graph()
