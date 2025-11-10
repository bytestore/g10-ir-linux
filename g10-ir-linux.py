#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Program IR buttons via BlueZ D-Bus (dbus-next) and exit without disconnecting.
Usage: python3 g10-ir-linux.py E8:DF:24:50:C1:E4
"""

import asyncio
import sys
from dbus_next.aio import MessageBus
from dbus_next import Variant, BusType

# UUIDs used by device (as in your device)
CHAR_STARTSTOP_UUID = "d343bfc1-5a21-4f05-bc7d-af01f617b664"
CHAR_KEY_UUID       = "d343bfc2-5a21-4f05-bc7d-af01f617b664"
CHAR_VALUE_UUID     = "d343bfc3-5a21-4f05-bc7d-af01f617b664"

# IR codes (replace / extend as needed)
IR_CODES = [
    (b"\x00\x18", "0221017c0020123c000a0046000a001e000a001e000a001e000a001e000a001e000a001e000a0046000a001e000a0046000a001e000a001e000a001e000a0046000a001e000a06ff000a0046000a001e000a001e000a001e000a001e000a0046000a0046000a001e000a0046000a001e000a0046000a0046000a0046000a001e000a0046000a05f4"),  # VolUp
    (b"\x00\x19", "0221017c0020123c000a0046000a001e000a001e000a001e000a001e000a0046000a001e000a0046000a001e000a0046000a001e000a001e000a001e000a0046000a001e000a06d7000a0046000a001e000a001e000a001e000a001e000a001e000a0046000a001e000a0046000a001e000a0046000a0046000a0046000a001e000a0046000a06d7"),  # VolDown
    (b"\x00\xa4", "00"),  # Mute
    (b"\x00\x1a", "00"),  # Power
    (b"\x00\xb2", "0221017c0020123c000a0046000a001e000a001e000a001e000a001e000a001e000a0046000a0046000a001e000a0046000a001e000a001e000a001e000a0046000a001e000a06d7000a0046000a001e000a001e000a001e000a001e000a0046000a001e000a001e000a0046000a001e000a0046000a0046000a0046000a001e000a0046000a05f4"),  # input
]

BLUEZ_BUS_NAME = "org.bluez"
ADAPTER_PATH = "/org/bluez/hci0"

def mac_to_devpath(mac: str) -> str:
    """Convert MAC like AA:BB:CC:DD:EE:FF -> dev_AA_BB_CC_DD_EE_FF"""
    dev = "dev_" + mac.replace(":", "_")
    return f"{ADAPTER_PATH}/{dev}"

async def find_char_path(managed_objects, device_path, uuid):
    """Search managed objects dict for characteristic matching device_path and uuid"""
    for path, ifaces in managed_objects.items():
        gatt = ifaces.get("org.bluez.GattCharacteristic1")
        if not gatt:
            continue
        # gatt is a dict of Variants, key "UUID"
        uuid_val = gatt.get("UUID")
        if uuid_val and uuid_val.value.lower() == uuid.lower() and path.startswith(device_path):
            return path
    return None

async def write_char(bus, char_path: str, value: bytes):
    """Write bytes to GATT characteristic via D-Bus WriteValue"""
    # introspect and get proxy object
    introspection = await bus.introspect(BLUEZ_BUS_NAME, char_path)
    proxy = bus.get_proxy_object(BLUEZ_BUS_NAME, char_path, introspection)
    char_iface = proxy.get_interface("org.bluez.GattCharacteristic1")
    # WriteValue expects array of bytes and options dict
    # dbus-next will accept Python bytes directly for the 'ay' signature
    await char_iface.call_write_value(value, {})
    # small safety sleep handled by caller if needed

async def program_device(bus, device_path):
    # get managed objects once
    introspection_root = await bus.introspect(BLUEZ_BUS_NAME, "/")
    root = bus.get_proxy_object(BLUEZ_BUS_NAME, "/", introspection_root)
    mgr = root.get_interface("org.freedesktop.DBus.ObjectManager")
    managed = await mgr.call_get_managed_objects()

    # find characteristic paths
    startstop_path = await find_char_path(managed, device_path, CHAR_STARTSTOP_UUID)
    key_path       = await find_char_path(managed, device_path, CHAR_KEY_UUID)
    value_path     = await find_char_path(managed, device_path, CHAR_VALUE_UUID)

    if not (startstop_path and key_path and value_path):
        print("Cannot find all gatt. Searched:")
        print(" startstop:", startstop_path)
        print(" key:      ", key_path)
        print(" value:    ", value_path)
        raise SystemExit(1)

    print("Find these gatt:")
    print(" START/STOP:", startstop_path)
    print(" KEY:       ", key_path)
    print(" VALUE:     ", value_path)

    # Some devices expect START before programming; some expect after.
    # We'll follow: START -> write each (key,value) with delays -> STOP
    print("Start programming (START)")
    await write_char(bus, startstop_path, b"\x01")
    await asyncio.sleep(0.25)

    for key, hexvalue in IR_CODES:
        print(f"→ write key {key.hex()}")
        await write_char(bus, key_path, key)
        await asyncio.sleep(0.18)
        print(f"→ write value ({len(hexvalue)//2} bytes)")
        await write_char(bus, value_path, bytes.fromhex(hexvalue))
        # pause a bit to let device flash write
        await asyncio.sleep(0.35)
        print("  OK")

    print("Disable programming (STOP)")
    await write_char(bus, startstop_path, b"\x00")
    await asyncio.sleep(0.2)
    print("Programming comlete, BlueZ dont disconnect remote")

async def main():
    if len(sys.argv) < 2:
        print("Usage: python3 g10-ir-linux.py <MAC>")
        raise SystemExit(1)

    mac = sys.argv[1].upper()
    device_path = mac_to_devpath(mac)
    print("Device path:", device_path)


    # Connect to system bus
    bus = await MessageBus(bus_type=BusType.SYSTEM).connect()

    # Ensure device object exists and is connected
    try:
        introspection = await bus.introspect(BLUEZ_BUS_NAME, device_path)
    except Exception as e:
        print("Device object not found on D-Bus. Is it paired/connected via bluetoothctl?")
        print("Exception:", e)
        raise SystemExit(1)

    # Check Device1 Connected property
    dev_obj = bus.get_proxy_object(BLUEZ_BUS_NAME, device_path, introspection)
    dev_props = dev_obj.get_interface("org.freedesktop.DBus.Properties")
    props = await dev_props.call_get_all("org.bluez.Device1")
    connected = props.get("Connected", False)
    if not connected:
        print("Device is not connected. Connect it (e.g. bluetoothctl connect) and run again.")
        raise SystemExit(1)

    # Program device
    await program_device(bus, device_path)

    # Done — quit. BlueZ keeps the connection alive.
    #await bus.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
