import meshtastic
import meshtastic.ble_interface
import meshtastic.serial_interface
import meshtastic.util
import argparse
import sqlite3
import json
from datetime import datetime

try:
    from meshtastic.protobuf import portnums_pb2, telemetry_pb2
    from meshtastic import BROADCAST_NUM
except ImportError:
    from meshtastic import portnums_pb2, telemetry_pb2, BROADCAST_NUM


def initialize_database(db_name="telemetry.db"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS telemetry (
            id TEXT PRIMARY KEY,
            timestamp INTEGER,
            ch1_voltage REAL,
            ch1_current REAL,
            ch2_voltage REAL,
            ch2_current REAL,
            temperature REAL,
            humidity REAL
        )
    ''')
    conn.commit()
    conn.close()

def get_telemetry_from_node(address):
    interface = meshtastic.ble_interface.BLEInterface(address)
    try:
        interface.waitForConfig()
        #telemetry = interface.getNodeTelemetry()
        telemetry = interface.localNode.getMetadata()
        print(telemetry)
        interface.close()
        return telemetry
    except Exception as e:
        print(f"Error getting telemetry from node: {e}")
        return None

def insert_telemetry_into_database(telemetry, db_name="telemetry.db"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO telemetry (id, timestamp, ch1_voltage, ch1_current, ch2_voltage, ch2_current, temperature, humidity)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (telemetry['id'], telemetry['timestamp'], telemetry['ch1_voltage'], telemetry['ch1_current'], telemetry['ch2_voltage'], telemetry['ch2_current'], telemetry['temperature'], telemetry['humidity']))
    conn.commit()
    conn.close()

def print_telemetry(telemetry):
    print(f"Timestamp: {telemetry['timestamp']}")
    print(f"Ch1 Voltage: {telemetry['ch1_voltage']} V")
    print(f"Ch1 Current: {telemetry['ch1_current']} A")
    print(f"Ch2 Voltage: {telemetry['ch2_voltage']} V")
    print(f"Ch2 Current: {telemetry['ch2_current']} A")
    print(f"Temperature: {telemetry['temperature']} C")
    print(f"Humidity: {telemetry['humidity']} %")

def main():
    parser = argparse.ArgumentParser(description="Retrieve telemetry from a Meshtastic node via Bluetooth")
    parser.add_argument('--address', required=True, help='Bluetooth address of the Meshtastic node')
    parser.add_argument('--db', default="telemetry.db", help='Database file name')
    parser.add_argument('--exportonly', default=False, action='store_true', help='Only export the telemetry to JSON')
    args = parser.parse_args()

    initialize_database()
    print(f"Attempting to connect to Meshtastic node with BLE address: {args.address}")
    print("This will take at least 10 seconds just to scan")
    telemetry = get_telemetry_from_node(args.address)
    if not args.exportonly:
        insert_telemetry_into_database(telemetry)
    if args.exportonly:
        print_telemetry(telemetry)

if __name__ == "__main__":
    main()