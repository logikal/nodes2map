import meshtastic
import meshtastic.ble_interface
import meshtastic.serial_interface
import meshtastic.util
import argparse
import sqlite3
import json
from datetime import datetime

def initialize_database(db_name="nodes.db"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS nodes (
            id TEXT PRIMARY KEY,
            num INTEGER,
            user_id TEXT,
            long_name TEXT,
            short_name TEXT,
            hw_model TEXT,
            latitude REAL,
            longitude REAL,
            altitude INTEGER,
            snr REAL,
            last_heard INTEGER,
            hops_away INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def get_nodedb_via_bluetooth(address, db_name="nodes.db"):
    # Connect to the Meshtastic node via Bluetooth
    interface = meshtastic.ble_interface.BLEInterface(address)
    # Wait for the node database to be received
    try:
        interface.waitForConfig()

        # Retrieve the node database
        nodedb = interface.nodes

        # Open the SQLite database
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        # Track the number of nodes updated
        nodes_updated = 0

        # Insert or update nodes in the database
        for node_id, node in nodedb.items():
            last_heard = node.get('lastHeard')

            # Attempt to convert last_heard to a formatted string
            # This causes errors when we receive garbled NodeInfo 
            # packets from nodes and we lack a lastHeard value
            try:
                last_heard_str = datetime.fromtimestamp(last_heard).strftime('%Y-%m-%d %H:%M:%S')
            except (TypeError, ValueError) as e:
                # If there's an error in conversion, skip this node
                continue
            user = node.get('user', {})
            position = node.get('position', {})
            cursor.execute('''
                INSERT INTO nodes (id, num, user_id, long_name, short_name, hw_model, latitude, longitude, altitude, snr, last_heard, hops_away)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    num=excluded.num,
                    user_id=excluded.user_id,
                    long_name=excluded.long_name,
                    short_name=excluded.short_name,
                    hw_model=excluded.hw_model,
                    latitude=excluded.latitude,
                    longitude=excluded.longitude,
                    altitude=excluded.altitude,
                    snr=excluded.snr,
                    last_heard=excluded.last_heard,
                    hops_away=excluded.hops_away
                WHERE excluded.last_heard > nodes.last_heard
            ''', (
                node_id,
                node.get('num'),
                user.get('id'),
                user.get('longName'),
                user.get('shortName'),
                user.get('hwModel'),
                position.get('latitude'),
                position.get('longitude'),
                position.get('altitude'),
                node.get('snr'),
                node.get('lastHeard'),
                node.get('hopsAway')
            ))
            nodes_updated = conn.total_changes

        # Commit changes to the database
        conn.commit()
        print("Database updated")
    except (meshtastic.ble_interface.BLEInterface.BLEError) as e:
        print(f"Couldn't connect to the node. Is someone else connected to it? {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print("Closing Connections")
        # Close the database connection
        conn.close()
        print("Database closed")
        # Close the interface connection
        print("Disconnecting from Meshtastic node")
        interface._sendDisconnect()
        interface.close()

    # Print the number of nodes updated
    print(f"Number of nodes updated: {nodes_updated}")

def format_last_heard(last_heard):
    try:
        return datetime.fromtimestamp(last_heard).strftime('%Y-%m-%d %H:%M:%S')
    except (TypeError, ValueError):
        return 'N/A'

def extract_nodes_to_json(db_name="nodes.db", output_file="nodes.json"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("SELECT latitude, longitude, short_name, long_name, snr, last_heard FROM nodes WHERE (hops_away is null OR hops_away = 0) AND latitude >0")
    nodes = cursor.fetchall()
    conn.close()

    nodes_list = [
        {
            "latitude": lat,
            "longitude": lon,
            "short_name": short_name,
            "long_name": long_name,
            "snr": snr,
            "last_heard": format_last_heard(last_heard)
        }
        for lat, lon, short_name, long_name, snr, last_heard in nodes
    ]

    with open(output_file, "w") as f:
        json.dump(nodes_list, f)

def main():
    parser = argparse.ArgumentParser(description="Retrieve node database from a Meshtastic node via Bluetooth")
    parser.add_argument('--address', required=True, help='Bluetooth address of the Meshtastic node')
    parser.add_argument('--jsonexport', default="nodes.json", help='Output file for the node database')
    parser.add_argument('--exportonly', default=False, action='store_true', help='Only export the node database to JSON')
    args = parser.parse_args()

    if args.exportonly:
        print("Skipping node connection and db update")
    else:
        print(f"Attempting to connect to Meshtastic node with BLE address: {args.address}")
        print("This will take at least 10 seconds just to scan")
        initialize_database()
        get_nodedb_via_bluetooth(args.address)
    extract_nodes_to_json(output_file=args.jsonexport)
if __name__ == "__main__":
    main()