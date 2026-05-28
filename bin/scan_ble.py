import asyncio
from bleak import BleakScanner

async def main():
    print("Scanning for BLE devices... (this will take 10 seconds)")
    devices = await BleakScanner.discover(timeout=10.0)
    print("\nDiscovered Devices:")
    print("-" * 60)
    print(f"{'Name':<30} | {'Address (MAC)':<20}")
    print("-" * 60)
    for d in devices:
        name = d.name or "Unknown"
        print(f"{name:<30} | {d.address:<20}")
    print("-" * 60)
    print("If you see your HQST controller (often named 'BT-TH-XXXXXXXX' or 'Renogy BT-1'),")
    print("copy its Address and paste it into your config.ini [hqst] section as mac_address.")

if __name__ == "__main__":
    asyncio.run(main())
