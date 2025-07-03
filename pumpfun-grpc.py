import websocket
import json
import threading
import time
import config
import sys


WS_URL = config.my_url
PUMP_FUN_PROGRAM_ID = "pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA"

MAX_RETRIES = 5
INITIAL_RETRY_DELAY = 1  # seconds
retry_count = 0


def send_subscribe_request(ws):
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "logsSubscribe",
        "params": [
            {
                "mentions": [PUMP_FUN_PROGRAM_ID]
            }
        ]
    }
    print("Sending subscription request:")
    print(json.dumps(request, indent=2))
    ws.send(json.dumps(request))


def start_ping(ws):
    def ping():
        while True:
            time.sleep(30)
            try:
                ws.send("ping")
                print("Ping sent")
            except:
                break
    threading.Thread(target=ping, daemon=True).start()


def on_open(ws):
    global retry_count
    print("WebSocket connected")
    retry_count = 0  # Reset retry count on successful connection
    send_subscribe_request(ws)
    start_ping(ws)


def on_message(ws, message):
    try:
        message_obj = json.loads(message)
        
        # Handle subscription confirmation
        if "result" in message_obj and isinstance(message_obj["result"], int):
            print(f"Successfully subscribed with ID: {message_obj['result']}")
            return

        # Handle actual log data
        if message_obj.get("params", {}).get("result"):
            log_data = message_obj["params"]["result"]
            print("Received log data:")
            print(json.dumps(log_data, indent=2))

            signature = log_data.get("signature")
            if signature:
                print(f"Transaction signature: {signature}")

        else:
            print("Received message:")
            print(json.dumps(message_obj, indent=2))

    except json.JSONDecodeError:
        print("Failed to parse message")


def on_error(ws, error):
    print(f"WebSocket error: {error}")


def on_close(ws, close_status_code, close_msg):
    print("WebSocket closed")
    reconnect()


def reconnect():
    global retry_count
    if retry_count >= MAX_RETRIES:
        print("Max retry attempts reached. Exiting.")
        sys.exit(1)

    delay = INITIAL_RETRY_DELAY * (2 ** retry_count)
    print(f"Attempting to reconnect in {delay} seconds... (Attempt {retry_count + 1}/{MAX_RETRIES})")
    time.sleep(delay)
    retry_count += 1
    connect()


def connect():
    ws = websocket.WebSocketApp(
        WS_URL,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    ws.run_forever()


# Start connection
connect()
