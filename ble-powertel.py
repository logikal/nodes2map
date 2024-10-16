import meshtastic
import meshtastic.ble_interface
import meshtastic.serial_interface
import meshtastic.util

remote_node = "^local"
want_response = True
channel = 1

print("Connecting to node")
interface = meshtastic.ble_interface.BLEInterface("BEED1ABC-B08A-E4D3-D4DF-69B95A58E79C")
print("Waiting for config")
interface.waitForConfig()
print("Sending telemetry request")
interface.sendTelemetry(remote_node, want_response, channel)
print("Closing interface")
interface.close()


# def get_telemetry_from_node(address):
    
#     try:
#         interface.waitForConfig()
#         #telemetry = interface.getNodeTelemetry()
#         telemetry = interface.localNode.getMetadata()
#         print(telemetry)
#         interface.close()
#         return telemetry
#     except Exception as e:
#         print(f"Error getting telemetry from node: {e}")
#         return None