"""CoAP pump simulator with MQTT state feedback."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
from datetime import datetime, timezone

import aiocoap
import aiocoap.resource as resource
import paho.mqtt.client as mqtt

LOGGER = logging.getLogger(__name__)


class PumpResource(resource.Resource):
    def __init__(self, state: dict[str, object], mqtt_client: mqtt.Client, topic: str) -> None:
        super().__init__()
        self.state = state
        self.mqtt_client = mqtt_client
        self.topic = topic

    async def render_get(self, request: aiocoap.Message) -> aiocoap.Message:
        return aiocoap.Message(payload=json.dumps(self.state).encode(), code=aiocoap.Code.CONTENT)

    async def render_post(self, request: aiocoap.Message) -> aiocoap.Message:
        command = request.payload.decode("utf-8").strip().lower()
        if command not in {"on", "off"}:
            return aiocoap.Message(payload=b"command must be on or off", code=aiocoap.Code.BAD_REQUEST)
        self.state["state"] = command
        self.state["timestamp"] = datetime.now(timezone.utc).isoformat()
        self.mqtt_client.publish(self.topic, json.dumps(self.state), qos=1)
        return aiocoap.Message(payload=json.dumps(self.state).encode(), code=aiocoap.Code.CHANGED)


async def serve(host: str = "::", port: int = 5683, mqtt_host: str = "localhost") -> None:
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="pump-sim")
    mqtt_client.connect(mqtt_host, 1883, keepalive=30)
    mqtt_client.loop_start()
    state: dict[str, object] = {"state": "off", "timestamp": datetime.now(timezone.utc).isoformat()}
    site = resource.Site()
    pump = PumpResource(state, mqtt_client, "ferme/parcelle1/pompe/etat")
    site.add_resource(["pump", "on"], pump)
    site.add_resource(["pump", "off"], pump)
    site.add_resource(["pump", "state"], pump)
    await aiocoap.Context.create_server_context(site, bind=(host, port))
    try:
        await asyncio.get_running_loop().create_future()
    finally:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=5683)
    parser.add_argument("--mqtt-host", default="localhost")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    asyncio.run(serve(port=args.port, mqtt_host=args.mqtt_host))


if __name__ == "__main__":
    main()
