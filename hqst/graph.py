import os
import csv
import matplotlib
# Use non-interactive Agg backend to avoid GUI errors when running headless/in cron
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

def generate_graph(csv_path="hqst_history.csv", output_dir="production/images/shed"):
    """
    Reads the solar history CSV, filters for today's data,
    and generates a beautiful production graph saved to the target directory.
    """
    if not os.path.exists(csv_path):
        print(f"⚠️ Cannot generate graph: {csv_path} does not exist.")
        return False

    os.makedirs(output_dir, exist_ok=True)
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    times = []
    powers = []
    voltages = []
    
    # Read history data
    with open(csv_path, mode="r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ts_str = row.get("timestamp", "")
            if ts_str.startswith(today_str):
                try:
                    ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                    times.append(ts)
                    powers.append(float(row.get("pv_power", 0.0)))
                    voltages.append(float(row.get("pv_voltage", 0.0)))
                except Exception:
                    continue

    if not times:
        print("⚠️ No solar production records found for today yet.")
        return False

    # Create the plot
    fig, ax = plt.subplots(figsize=(10, 5), dpi=150)
    
    # Plot power curve with smooth shading
    ax.plot(times, powers, color="#f59e0b", linewidth=2.5, label="Solar Power (W)")
    ax.fill_between(times, powers, color="#fef3c7", alpha=0.5)
    
    # Style the axes
    ax.set_title(f"Shed Solar Production - {datetime.now().strftime('%B %d, %Y')}", fontsize=14, fontweight="bold", color="#1f2937")
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
    
    # Get peak metrics to show in legend/annotation
    peak_power = max(powers)
    latest_power = powers[-1]
    
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
    
    print(f"📈 Production graph generated successfully: {output_filename}")
    return True

if __name__ == "__main__":
    generate_graph()
