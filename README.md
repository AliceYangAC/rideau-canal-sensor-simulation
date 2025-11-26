# Rideau Canal Skateway - IoT Device Sensor Simulation

This script simulates **IoT telemetry metrics** from three Rideau Canal locations (**Dow’s Lake**, **Fifth Avenue**, and **NAC**) by generating randomized environmental data every 10 seconds. For each location, it produces metrics for:

- Ice Thickness (cm)  
- Surface Temperature (°C)  
- Snow Accumulation (cm)  
- External Temperature (°C)  
- Timestamp and location metadata

The simulator connects to **Azure IoT Hub** using device-specific (`dows_lake`, `fifth_avenue`, `nac`) connection strings and sends each telemetry payload as a message. This emulates real-world sensor behavior and feeds the data ingestion hub for downstream processing via Azure Stream Analytics, Cosmos DB, and Blob Storage.

## Technologies Used

- **Python 3.13**: language for IoT device simulation logic and message generation  
- **Azure IoT SDK for Python** (`azure.iot.device`): Python library used to create device clients from device connection strings and send their messages to IoT Hub  
- **dotenv**: loads environment variables from a `.env` file for secure connection string management  
- **Random / Time modules**: generate metric values from a range and timestamps

## Setup

### Prerequisites

- **Python 3.13+**
- **pip** for dependency management

### Installation

Clone the repos and install dependencies.

```bash
git clone https://github.com/aliceyangac/rideau-canal-dashboard.git
cd rideau-canal-dashboard
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Deploy Azure Services

#### Azure IoT Hub

1. Create an IoT Hub with **Basics -> Tier: Free** named `rideau-canal-iot-hub`
2. Register 3 devices with the names `dows-lake`, `fifth-avenue`, and `nac`

#### Azure Cosmos DB

1. Create a Cosmos DB for NoSQL with **Basics -> Workload Type: Learning** and ensure the default free provisioning options are enabled at the bottom of the page. Name it `rideau-canal-cosmos`
2. In the resource portal, navigate to **Data explorer** and create a DB with the following configurations:
   ```
    Database: RideauCanalDB
    Container: SensorAggregations
    Partition Key: /location
    Document ID: {location}-{timestamp}
    ```

#### Azure Storage Account

1. Create a Storage Account with **Basics -> Redundancy: LRS** named `rideaucanalstorage`
2. In the resource portal, navigate to **Data storage -> Containers** and create a container with the following configurations:
   ```
    Container: historical-data
    Path Pattern: aggregations/{date}/{time}
    Format: JSON (line separated)
   ```

#### Azure Stream Analytics Job

1. Create a Stream Analytics Job with **Basics -> Streaming units: Lowest value possible (1/3)**
2. In the resource portal, navigate to **Job topology -> Inputs** and create an input source from `rideau-canal-iot-hub`. It should be the default option loaded in.
3. In the resource portal, navigate to **Job topology -> Outputs** and create output sources into `rideau-canal-cosmos` and `rideaucanalstorage` respective containers, `SensorAggregations` and `historical-data`. They should be the default options loaded in for the resource.
4. In the resource portal, navigate to **Job topology -> Query** and copy + paste the SQL query below and save it.
   ```sql
   SELECT 
      CONCAT(c.location, '-', MAX(TRY_CAST(c.timestamp AS datetime))) as id,
      c.location,
      MAX(TRY_CAST(c.timestamp AS datetime)) as timestamp,
      AVG(c.ice_thickness) AS avg_ice_thickness,
      MIN(c.ice_thickness) AS min_ice_thickness,
      MAX(c.ice_thickness) AS max_ice_thickness,
      AVG(c.surface_temperature) AS avg_surface_temperature,
      MIN(c.surface_temperature) AS min_surface_temperature,
      MAX(c.surface_temperature) AS max_surface_temperature,
      MAX(c.snow_accumulation) AS max_snow_accumulation,
      AVG(c.external_temperature) AS avg_external_temperature,
      COUNT(1) AS reading_count
   INTO SensorAggregations
   FROM "rideau-canal-iot-hub" AS c
   GROUP BY TumblingWindow( minute , 5 ), c.location

   SELECT 
      CONCAT(c.location, '-', MAX(TRY_CAST(c.timestamp AS datetime))) as id,
      c.location,
      MAX(TRY_CAST(c.timestamp AS datetime)) as timestamp,
      AVG(c.ice_thickness) AS avg_ice_thickness,
      MIN(c.ice_thickness) AS min_ice_thickness,
      MAX(c.ice_thickness) AS max_ice_thickness,
      AVG(c.surface_temperature) AS avg_surface_temperature,
      MIN(c.surface_temperature) AS min_surface_temperature,
      MAX(c.surface_temperature) AS max_surface_temperature,
      MAX(c.snow_accumulation) AS max_snow_accumulation,
      AVG(c.external_temperature) AS avg_external_temperature,
      COUNT(1) AS reading_count
   INTO "historical-data"
   FROM "rideau-canal-iot-hub" AS c
   GROUP BY TumblingWindow( minute , 5 ), c.location
   ```

### Configuration

Copy `.env.example` as `.env` and replace the placeholder values with your IoT Hub device connection strings:

```env
DOWS_LAKE_CONN_STR=your_dows_lake_device_connection_string
FIFTH_AVE_CONN_STR=your_fifth_ave_device_connection_string
NAC_CONN_STR=your_nac_device_connection_string
```

### Usage

1. Run the sensor simulation to start sending telemetry:
   ```bash
   python sensor_simulation.py
   ```
2. In Stream Analytics, **Start Job** in the top menu blade.
3. Stop the simulator with `Ctrl+C`. All clients will disconnect cleanly.

## Details
```
+-------------------+
| IoT Devices       |
| (Simulated:       |
|  Dow's Lake,      |
|  Fifth Ave, NAC)  |
+---------+---------+
          |
          v
+-------------------+
| Azure IoT Hub     |
| (telemetry ingest)|
+---------+---------+
          |
          v
+-------------------+
| Azure Stream      |
| Analytics         |
| (5-min tumbling   |
|  window agg)      |
+---------+---------+
          |
          +-------------------+
          |                   |
          v                   v
+-------------------+   +-------------------+
| Cosmos DB         |   | Blob Storage      |
| (fast query for   |   | (historical data  |
|  dashboard)       |   |  archive)         |
+---------+---------+   +---------+---------+
```

- **Purpose**: Emulates IoT sensors along the Rideau Canal to test the end‑to‑end pipeline.  
- **Data Flow**:  
  - Telemetry → Azure IoT Hub  
  - IoT Hub → Stream Analytics (5‑minute tumbling window aggregation)  
  - Aggregated data → Cosmos DB (for live queries)  
  - Historical data → Blob Storage (for archival and trend analysis)

## Code Structure
```
+-------------------+
|   .env file       |
|  (connection strs)|
+---------+---------+
          |
          v
+-------------------+
| Load env vars     |
| (Dow's Lake,      |
|  Fifth Ave, NAC)  |
+---------+---------+
          |
          v
+-------------------+
| Create IoT Hub    |
| clients per       |
| location          |
+---------+---------+
          |
          v
+-------------------+
| Loop every 10 sec |
+---------+---------+
          |
          v
+-------------------+
| For each location |
|  -> generate      |
|     telemetry     |
|  -> wrap in       |
|     Message       |
|  -> send to IoT   |
|     Hub           |
+---------+---------+
          |
          v
+-------------------+
| Graceful shutdown |
| (Ctrl+C disconnect|
|  all clients)     |
+-------------------+
```

### Main Components Explained

- **Environment Setup**  
  - Loads `.env` file using `dotenv` to securely manage IoT Hub device connection strings.  
  - Connection strings for three locations (`Dow's Lake`, `Fifth Avenue`, `NAC`) are retrieved from environment variables.

- **Location Mapping**  
  - A dictionary (`locations`) maps each canal location to its IoT Hub connection string.  
  - This allows the script to simulate multiple devices in parallel.

- **Telemetry Generator (`get_telemetry`)**  
  - Produces randomized sensor readings for ice thickness, surface temperature, snow accumulation, and external temperature.  
  - Adds a UTC timestamp and the location name to each record.

- **Main Loop (`main`)**  
  - Creates IoT Hub device clients for each location using the Azure IoT SDK.  
  - Enters an infinite loop, sending telemetry messages every 10 seconds.  
  - Handles graceful shutdown on `Ctrl+C` (KeyboardInterrupt) by disconnecting all clients.

### Key Functions

- **`get_telemetry(location)`**  
  - Inputs: `location` (string)  
  - Outputs: Dictionary with randomized sensor values and metadata.  
  - Purpose: Simulates realistic IoT sensor readings for a given canal location.

- **`main()`**  
  - Initializes IoT Hub clients for all locations.  
  - Iterates through each client, generates telemetry via `get_telemetry`, wraps it in an IoT Hub `Message`, and sends it upstream.  
  - Sleeps for 10 seconds before repeating.  
  - Ensures clean disconnection of clients when stopped.

## Sensor Data Format

### JSON Schema

```json
{
    "event": {
        "origin": "device name",
        "module": "for IoT Plug and Play",
        "interface": "for IoT Plug and Play",
        "component": "for IoT Plug and Play",
        "payload": "stringified JSON object containing the actual telemetry values"
    }
}
```

### Example Output

```json
{
    "event": {
        "origin": "nac",
        "module": "",
        "interface": "",
        "component": "",
        "payload": "{'ice_thickness': 33.36326398943026, 'surface_temperature': -6.304130488761269, 'snow_accumulation': 4.274066439361688, 'external_temperature': -10.148687979751413, 'timestamp': '2025-11-26 14:07:12', 'location': 'NAC'}"
    }
}
```

## Troubleshooting

### 1. The simulator won’t start locally.
- **Cause:** Missing dependencies or virtual environment not activated.  
- **Fix:**  
  ```bash
  source venv/bin/activate   # or venv\Scripts\activate on Windows
  pip install -r requirements.txt
  python sensor_simulation.py
  ```

### 2. Connection errors when sending telemetry to IoT Hub.
- **Cause:** Invalid or missing IoT Hub device connection strings in `.env`.  
- **Fix:**  
  - Ensure `.env` file exists in the project root.  
  - Verify values for:  
    ```env
    DOWS_LAKE_CONN_STR=your_dows_lake_device_connection_string
    FIFTH_AVE_CONN_STR=your_fifth_ave_device_connection_string
    NAC_CONN_STR=your_nac_device_connection_string
    ```  
  - Confirm devices are registered in IoT Hub with matching names.

### 3. No data flowing into Stream Analytics.
- **Cause:** Stream Analytics job not started or input not bound to IoT Hub.  
- **Fix:**  
  - In Stream Analytics **Job topology ->  Inputs**, confirm IoT Hub is configured.  
  - Start the job from the top menu blade.  
  - Check logs for dropped events.

### 4. Cosmos DB container remains empty.
- **Cause:** Output not configured or partition key mismatch.  
- **Fix:**  
  - In Stream Analytics **Job topology ->  Outputs**, confirm Cosmos DB container is `SensorAggregations`.  
  - Partition key must be `/location`.  
  - Verify query includes `c.location` and `id`.

### 5. Blob Storage container has no files.
- **Cause:** Output path or format misconfigured.  
- **Fix:**  
  - In Stream Analytics **Job topology ->  Outputs**, confirm Storage Accounts container is `historical-data`.  
  - Path pattern should be:  
    ```
    aggregations/{date}/{time}
    ```  
  - Format must be **JSON (line separated)**.

### 6. Simulator stops unexpectedly after a few seconds.
- **Cause:** KeyboardInterrupt or unhandled exception.  
- **Fix:**  
  - If intentional, restart with:  
    ```bash
    python sensor_simulation.py
    ```  
  - If unintentional, check logs for stack traces (e.g., invalid env vars, network errors). 

### 7. IoT Hub shows messages but downstream services don’t update.
- **Cause:** Latency or aggregation window delay.  
- **Fix:**  
  - Stream Analytics uses a **5‑minute tumbling window**. 
  - Confirm job is running and not paused.