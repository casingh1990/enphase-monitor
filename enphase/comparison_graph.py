import os
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

def generate_comparison_graph(
    prod_csv_path="production/data/enphase_history.csv",
    cons_csv_path="production/data/consumption_history.csv",
    output_dir="production/images/house"
):
    """
    Generates a beautiful comparison graph showing both solar production and
    household consumption overlaid on the same chart for today.
    """
    if not os.path.exists(prod_csv_path) or not os.path.exists(cons_csv_path):
        print("⚠️ Cannot generate comparison graph: One or both history files do not exist.")
        return False

    os.makedirs(output_dir, exist_ok=True)
    today_str = datetime.now().strftime("%Y-%m-%d")

    # Load production data
    prod_times = []
    prod_powers = []
    envoy1_powers = []
    envoy2_powers = []
    with open(prod_csv_path, mode="r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ts_str = row.get("timestamp", "")
            if ts_str.startswith(today_str):
                try:
                    ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                    prod_times.append(ts)
                    prod_powers.append(float(row.get("total_power", 0.0)))
                    envoy1_powers.append(float(row.get("envoy1_power", 0.0)))
                    envoy2_powers.append(float(row.get("envoy2_power", 0.0)))
                except Exception:
                    continue

    # Load consumption data
    cons_times = []
    cons_powers = []
    net_grids = []
    with open(cons_csv_path, mode="r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ts_str = row.get("timestamp", "")
            if ts_str.startswith(today_str):
                try:
                    ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                    cons_times.append(ts)
                    cons_powers.append(float(row.get("total_consumption_w", 0.0)))
                    net_grids.append(float(row.get("net_consumption_w", 0.0)))
                except Exception:
                    continue

    if not prod_times or not cons_times:
        print("⚠️ Not enough data points to generate production/consumption comparison graph.")
        return False

    # Create plot
    fig, ax = plt.subplots(figsize=(10, 5), dpi=150)

    # Plot baseline reference for Net Grid Zero (Import vs Export threshold)
    ax.axhline(0, color="#9ca3af", linestyle=":", linewidth=1.2, alpha=0.7, label="Grid Balance Zero")

    # Plot Total Solar Production (Green Area)
    ax.plot(prod_times, prod_powers, color="#10b981", linewidth=2.5, label="Total Solar Production")
    ax.fill_between(prod_times, prod_powers, color="#ecfdf5", alpha=0.35)

    # Plot Individual System Productions
    ax.plot(prod_times, envoy1_powers, color="#34d399", linewidth=1.2, linestyle="--", label="System 1 Solar (Envoy 1)", alpha=0.8)
    ax.plot(prod_times, envoy2_powers, color="#059669", linewidth=1.2, linestyle=":", label="System 2 Solar (Envoy 2)", alpha=0.8)

    # Plot House Consumption (Red Area)
    ax.plot(cons_times, cons_powers, color="#ef4444", linewidth=2.5, label="Household Load (Consumption)")
    ax.fill_between(cons_times, cons_powers, color="#fef2f2", alpha=0.3)

    # Plot Net Grid Import/Export (Blue line)
    # Positive values mean importing, negative values mean exporting to grid
    ax.plot(cons_times, net_grids, color="#3b82f6", linewidth=1.8, linestyle="-.", label="Net Grid State (Import/Export)")

    # Styling
    ax.set_title(f"Solar Production vs. Home Consumption & Grid State - {datetime.now().strftime('%B %d, %Y')}", 
                 fontsize=13, fontweight="bold", color="#1f2937")
    ax.set_xlabel("Time of Day", fontsize=11, color="#4b5563")
    ax.set_ylabel("Power (Watts)", fontsize=11, color="#4b5563")

    # Format x-axis time labels
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))
    fig.autofmt_xdate()

    # Subtle grids
    ax.grid(True, linestyle="--", alpha=0.5, color="#e5e7eb")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#d1d5db")
    ax.spines["bottom"].set_color("#d1d5db")

    # Legend placed below the plot (horizontal layout with 3 columns)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.18), ncol=3, frameon=True, facecolor="white", edgecolor="#e5e7eb")

    # Annotate summary details
    peak_prod = max(prod_powers) if prod_powers else 0.0
    peak_cons = max(cons_powers) if cons_powers else 0.0
    latest_prod = prod_powers[-1] if prod_powers else 0.0
    latest_cons = cons_powers[-1] if cons_powers else 0.0

    # Calculate grid imports and exports
    imports = [g for g in net_grids if g > 0]
    exports = [abs(g) for g in net_grids if g < 0]
    peak_import = max(imports) if imports else 0.0
    peak_export = max(exports) if exports else 0.0
    latest_grid = net_grids[-1] if net_grids else 0.0

    grid_state_str = f"Exporting: {abs(latest_grid):.0f} W" if latest_grid < 0 else f"Importing: {latest_grid:.0f} W"

    # Display annotations in the bottom-left corner of the plot
    ax.text(0.02, 0.05, 
            f"Peak Solar: {peak_prod:.0f} W (Latest: {latest_prod:.0f} W)\n"
            f"Peak Load: {peak_cons:.0f} W (Latest: {latest_cons:.0f} W)\n"
            f"Peak Import: {peak_import:.0f} W\n"
            f"Peak Export: {peak_export:.0f} W\n"
            f"Grid State: {grid_state_str}",
            transform=ax.transAxes, fontsize=9.0, verticalalignment='bottom',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='#ffffff', edgecolor='#e5e7eb', alpha=0.9))

    # Save comparison image
    timestamp_filename = datetime.now().strftime("%Y%m%d")
    output_filename = os.path.join(output_dir, f"comparison_{timestamp_filename}.png")

    plt.tight_layout()
    plt.savefig(output_filename, facecolor='white', bbox_inches='tight')
    plt.close()

    print(f"📈 Comparison graph generated successfully: {output_filename}")
    return True
