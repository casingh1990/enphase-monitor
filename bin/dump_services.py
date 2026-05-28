import asyncio
from bleak import BleakClient

async def main():
    address = "C8:47:80:13:44:41"
    output = []
    output.append(f"Connecting to {address}...")
    try:
        async with BleakClient(address, timeout=15.0) as client:
            output.append(f"Connected: {client.is_connected}")
            output.append("\nServices and Characteristics:")
            output.append("=" * 60)
            for service in client.services:
                output.append(f"\nService: {service.uuid} ({service.description})")
                output.append("-" * 60)
                for char in service.characteristics:
                    output.append(f"  Characteristic: {char.uuid} ({char.description})")
                    output.append(f"    Properties: {', '.join(char.properties)}")
                    if "read" in char.properties:
                        try:
                            value = await client.read_gatt_char(char.uuid)
                            hex_val = value.hex() if value else 'empty'
                            # Remove null bytes or other weird characters to ensure a clean text file
                            hex_val = hex_val.replace('\x00', '')
                            output.append(f"    Value hex: {hex_val}")
                        except Exception as e:
                            output.append(f"    Value: (failed to read: {e})")
            output.append("=" * 60)
    except Exception as e:
        output.append(f"❌ Connection or discovery failed: {e}")
        
    with open("dump.txt", "w") as f:
        f.write("\n".join(output))

if __name__ == "__main__":
    asyncio.run(main())
