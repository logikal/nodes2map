#!/bin/bash
#
while true
do
	uv run nodes.py --address "CA:30:DC:3B:65:FB" --jsonexport map/nodes.json
	uv run meshtastic --no-nodes --request-telemetry power --dest '!dc3b65fb' --host 192.168.104.87
	sleep 600
done
