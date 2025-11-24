import os
import time
import random
from azure.iot.device import IoTHubDeviceClient, Message
from dotenv import load_dotenv

# Explicitly load the .env file from this folder
BASE_DIR = os.path.dirname(__file__)
load_dotenv(dotenv_path=os.path.join(BASE_DIR, ".env"))

# Ice Thickness (cm)
# Surface Temperature (°C)
# Snow Accumulation (cm)
# External Temperature (°C)

CONNECTION_STRING = os.getenv("CONNECTION_STRING")

locations =["Dow's Lake", "Fifth Avenue", "NAC"]

def get_telemetry(location):
    return {
        "ice_thickness": random.uniform(5.0, 30.0),
        "surface_temperature": random.uniform(-10.0, 0.0),
        "snow_accumulation": random.uniform(0.0, 20.0),
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
    client = IoTHubDeviceClient.create_from_connection_string(CONNECTION_STRING)

    print("Sending telemetry of 3 devices to IoT Hub...")
    try:
        for location in locations:
            telemetry = get_telemetry(location)
            message = Message(str(telemetry))
            client.send_message(message)
            print(f"Sent message: {message}")
            time.sleep(10)
    except KeyboardInterrupt:
        print("Stopped sending messages.")
    finally:
        client.disconnect()

if __name__ == "__main__":
    main()