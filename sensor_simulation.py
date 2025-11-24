import time
import random
from azure.iot.device import IoTHubDeviceClient, Message

CONNECTION_STRING = "Your IoT Hub device connection string here"

def get_telemetry():
    return {
        "temperature": random.uniform(20.0, 40.0),
        "humidity": random.uniform(30.0, 70.0)
    }

def main():
    client = IoTHubDeviceClient.create_from_connection_string(CONNECTION_STRING)

    print("Sending telemetry to IoT Hub...")
    try:
        while True:
            telemetry = get_telemetry()
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