import os
import time
import random
from azure.iot.device import IoTHubDeviceClient, Message
from dotenv import load_dotenv

# Explicitly load the .env file from this folder
BASE_DIR = os.path.dirname(__file__)
load_dotenv(dotenv_path=os.path.join(BASE_DIR, ".env"))

DOWS_LAKE_CONN_STR = os.getenv("DOWS_LAKE_CONN_STR")
FIFTH_AVE_CONN_STR = os.getenv("FIFTH_AVE_CONN_STR")
NAC_CONN_STR = os.getenv("NAC_CONN_STR")

locations ={"Dow's Lake": DOWS_LAKE_CONN_STR, "Fifth Avenue": FIFTH_AVE_CONN_STR, "NAC": NAC_CONN_STR}

def get_telemetry(location):
    return {
        "ice_thickness": random.uniform(1.0, 70.0),
        "surface_temperature": random.uniform(-20.0, 0.0),
        "snow_accumulation": random.uniform(0.0, 45.0),
        "external_temperature": random.uniform(-20.0, 5.0),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
        "location": location
    }
    
# Configuration:
# Language: Python (This is just a recommendation, you can use any programming language or framework)
# Frequency: Send data every 10 seconds
# Locations: Three devices (one per location)
# Data Format: JSON with timestamp

def main():
    print("Sending telemetry of 3 devices to IoT Hub...")
    
    clients = {loc: IoTHubDeviceClient.create_from_connection_string(conn_str)
               for loc, conn_str in locations.items()}
    try:
        while True:
            for loc, client in clients.items():
                telemetry = get_telemetry(loc)
                message = Message(str(telemetry))
                client.send_message(message)
            time.sleep(10)
    except KeyboardInterrupt:
        print("Stopped sending messages.")
    finally:
        for client in clients.values():
            client.disconnect()
if __name__ == "__main__":
    main()