import asyncio
import logging
from bleak import BleakScanner
from renogy_ble import RenogyBLEDevice, RenogyBleClient

logger = logging.getLogger(__name__)

import asyncio
import logging
from bleak import BleakScanner
from bleak.exc import BleakError
from renogy_ble import RenogyBLEDevice, RenogyBleClient
from renogy_ble.ble import (
    establish_connection,
    BleakClientWithServiceCache,
    create_modbus_read_request,
    RenogyBleReadResult
)

logger = logging.getLogger(__name__)

class PatchedRenogyBleClient(RenogyBleClient):
    async def read_device(self, device: RenogyBLEDevice) -> RenogyBleReadResult:
        """Connect to a device, fetch data with custom delays, and return parsed results."""
        if device.device_type == "shunt300":
            return await super().read_device(device)

        commands = self._commands.get(device.device_type)
        if not commands:
            error = ValueError(f"Unsupported device type: {device.device_type}")
            logger.error("%s", error)
            return RenogyBleReadResult(False, dict(device.parsed_data), error)

        device.parsed_data.clear()

        connection_kwargs = self._connection_kwargs()
        any_command_succeeded = False
        error: Exception | None = None

        client = None
        try:
            client = await establish_connection(
                BleakClientWithServiceCache,
                device.ble_device,
                device.name or device.address,
                max_attempts=self._max_attempts,
                **connection_kwargs,
            )
        except (BleakError, asyncio.TimeoutError) as connection_error:
            logger.info(
                "Failed to establish connection with device %s: %s",
                device.name,
                str(connection_error),
            )
            return RenogyBleReadResult(
                False, dict(device.parsed_data), connection_error
            )

        try:
            logger.debug("Connected to device %s", device.name)
            notification_event = asyncio.Event()
            notification_data = bytearray()

            def notification_handler(_sender, data):
                notification_data.extend(data)
                notification_event.set()

            await client.start_notify(self._read_char_uuid, notification_handler)

            # We will perform the 4 required commands with custom handling for HQST/ChargePro:
            
            # --- 1. device_info ---
            print("Reading device info...")
            notification_data.clear()
            notification_event.clear()
            req_info = create_modbus_read_request(self._device_id, 3, 12, 8)
            await client.write_gatt_char(self._write_char_uuid, req_info, response=False)
            try:
                await asyncio.wait_for(notification_event.wait(), timeout=self._max_notification_wait_time)
                await asyncio.sleep(0.4) # Wait for trailing packets
                result_info = bytes(notification_data[:21])
                device.update_parsed_data(result_info, register=12, cmd_name="device_info")
                any_command_succeeded = True
            except asyncio.TimeoutError:
                print("⚠️ Timeout reading device info")
                
            await asyncio.sleep(0.8)

            # --- 2. device_id ---
            print("Reading device ID...")
            notification_data.clear()
            notification_event.clear()
            req_id = create_modbus_read_request(self._device_id, 3, 26, 1)
            await client.write_gatt_char(self._write_char_uuid, req_id, response=False)
            try:
                await asyncio.wait_for(notification_event.wait(), timeout=self._max_notification_wait_time)
                await asyncio.sleep(0.4)
                result_id = bytes(notification_data[:7])
                device.update_parsed_data(result_id, register=26, cmd_name="device_id")
                any_command_succeeded = True
            except asyncio.TimeoutError:
                print("⚠️ Timeout reading device ID")

            await asyncio.sleep(0.8)

            # --- 3. battery ---
            # HQST ChargePro insists on returning 5 registers (10 bytes data, 15 bytes total) even when count=1 is requested.
            # Setting count=5 makes expected_len match what the controller actually sends, preventing truncation.
            print("Reading battery parameters...")
            notification_data.clear()
            notification_event.clear()
            req_bat = create_modbus_read_request(self._device_id, 3, 57348, 5)
            await client.write_gatt_char(self._write_char_uuid, req_bat, response=False)
            try:
                await asyncio.wait_for(notification_event.wait(), timeout=self._max_notification_wait_time)
                await asyncio.sleep(0.4)
                result_bat = bytes(notification_data[:15])
                # Pass the 15-byte packet. The parser only decodes the register at 57348 (offset 3)
                device.update_parsed_data(result_bat, register=57348, cmd_name="battery")
                any_command_succeeded = True
            except asyncio.TimeoutError:
                print("⚠️ Timeout reading battery parameters")

            await asyncio.sleep(0.8)

            # --- 4. pv (Split Read & Merge) ---
            # ChargePro times out on 34 registers at once. We read 20 registers starting at 256,
            # and then 14 registers starting at 276, merging the data into a fake 73-byte packet.
            print("Reading PV (solar) parameters...")
            part1_data = None
            part2_data = None

            # PV Part 1 (20 registers starting at 256)
            notification_data.clear()
            notification_event.clear()
            req_pv1 = create_modbus_read_request(self._device_id, 3, 256, 20)
            await client.write_gatt_char(self._write_char_uuid, req_pv1, response=False)
            try:
                await asyncio.wait_for(notification_event.wait(), timeout=self._max_notification_wait_time)
                await asyncio.sleep(0.4)
                if len(notification_data) >= 45:
                    part1_data = bytes(notification_data[3:43])
            except asyncio.TimeoutError:
                print("⚠️ Timeout reading PV part 1")

            if part1_data:
                await asyncio.sleep(0.8)
                
                # PV Part 2 (14 registers starting at 276)
                notification_data.clear()
                notification_event.clear()
                req_pv2 = create_modbus_read_request(self._device_id, 3, 276, 14)
                await client.write_gatt_char(self._write_char_uuid, req_pv2, response=False)
                try:
                    await asyncio.wait_for(notification_event.wait(), timeout=self._max_notification_wait_time)
                    await asyncio.sleep(0.4)
                    if len(notification_data) >= 33:
                        part2_data = bytes(notification_data[3:31])
                except asyncio.TimeoutError:
                    print("⚠️ Timeout reading PV part 2")

            if part1_data and part2_data:
                # Merge the data blocks and construct a fake 34-register Modbus response packet
                merged_payload = part1_data + part2_data
                fake_pv_packet = bytes([self._device_id, 3, 68]) + merged_payload + b"\x00\x00"
                
                device.update_parsed_data(fake_pv_packet, register=256, cmd_name="pv")
                any_command_succeeded = True
            else:
                print("⚠️ Failed to read or merge PV parameters")

            await client.stop_notify(self._read_char_uuid)
            if not any_command_succeeded:
                error = RuntimeError("No commands completed successfully")
        except BleakError as exc:
            logger.info("BLE error with device %s: %s", device.name, str(exc))
            error = exc
        except Exception as exc:
            logger.error("Error reading data from device %s: %s", device.name, str(exc))
            error = exc
        finally:
            if client is not None and client.is_connected:
                try:
                    await client.disconnect()
                    logger.debug("Disconnected from device %s", device.name)
                except Exception as exc:
                    logger.debug(
                        "Error disconnecting from device %s: %s",
                        device.name,
                        str(exc),
                    )
                    if error is None:
                        error = exc

        return RenogyBleReadResult(
            any_command_succeeded, dict(device.parsed_data), error
        )

async def get_hqst_production(mac_address=None, device_name=None, device_type="controller", device_id=1, read_char_uuid=None, write_char_uuid=None):
    """
    Connects to the HQST/Renogy BLE solar charge controller and fetches real-time data.
    """
    ble_device = None
    
    # Set default characteristics for HQST ChargePro devices if not specified
    if not read_char_uuid:
        read_char_uuid = "0000ffe1-0000-1000-8000-00805f9b34fb"
    if not write_char_uuid:
        write_char_uuid = "0000ffe1-0000-1000-8000-00805f9b34fb"
    
    if mac_address and mac_address != "AA:BB:CC:DD:EE:FF":
        print(f"Connecting to HQST device via MAC Address: {mac_address}...")
        try:
            ble_device = await BleakScanner.find_device_by_address(mac_address, timeout=10.0)
        except Exception as e:
            print(f"❌ Error scanning for MAC address {mac_address}: {e}")
            
    if not ble_device:
        # Fallback to scanning/discovery
        target_name = device_name if (device_name and device_name != "BT-TH-XXXXXXXX") else None
        print(f"Scanning for BLE devices matching 'Renogy', 'BT-TH', or custom name...")
        try:
            devices = await BleakScanner.discover(timeout=10.0)
            for d in devices:
                name = d.name or ""
                # Match custom name if specified, otherwise look for known Renogy/HQST prefixes
                if target_name and target_name in name:
                    print(f"Found custom matched BLE device: {d.name} [{d.address}]")
                    ble_device = d
                    break
                elif "Renogy" in name or name.startswith("BT-TH") or name.startswith("RNG") or "ChargePro" in name:
                    print(f"Found candidate BLE device: {d.name} [{d.address}]")
                    ble_device = d
                    break
        except Exception as e:
            print(f"❌ Error discovering BLE devices: {e}")
            return None

    if not ble_device:
        print("❌ Error: HQST BLE device not found.")
        return None

    print(f"Found device: {ble_device.name} [{ble_device.address}]. Connecting and reading...")
    try:
        renogy_device = RenogyBLEDevice(ble_device, device_type=device_type)
        # Use our patched client that supports timing delays and custom characteristics
        client = PatchedRenogyBleClient(
            device_id=device_id,
            read_char_uuid=read_char_uuid,
            write_char_uuid=write_char_uuid,
            max_notification_wait_time=5.0, # Increased timeout for slow UART-BLE serial bridges
            max_attempts=3
        )
        result = await client.read_device(renogy_device)
        
        if result.success:
            return result.parsed_data
        else:
            print(f"❌ Read failed: {result.error}")
            return None
    except Exception as e:
        print(f"❌ Connection or communication error: {e}")
        return None
