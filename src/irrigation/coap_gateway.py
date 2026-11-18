"""HTTP-to-CoAP bridge used by Node-RED for reliable pump commands."""

from __future__ import annotations

import argparse
import asyncio
import json
import time

from aiohttp import web
import aiocoap


async def send_command(pump_url: str, action: str, timeout: float) -> dict[str, object]:
    if action not in {"on", "off"}:
        raise web.HTTPBadRequest(text="action must be 'on' or 'off'")
    started = time.perf_counter()
    try:
        context = await aiocoap.Context.create_client_context()
        request = aiocoap.Message(
            code=aiocoap.Code.POST,
            uri=pump_url + f"/pump/{action}",
            payload=action.encode(),
        )
        response = await asyncio.wait_for(context.request(request).response, timeout)
        latency_ms = (time.perf_counter() - started) * 1000
        if response.code.is_successful():
            return {"success": True, "action": action, "response": response.payload.decode(), "latency_ms": latency_ms}
        return {"success": False, "action": action, "error": str(response.code), "latency_ms": latency_ms}
    except (asyncio.TimeoutError, OSError, aiocoap.error.Error) as exc:
        raise web.HTTPGatewayTimeout(text=f"CoAP command failed: {exc}") from exc


async def command_handler(request: web.Request) -> web.Response:
    payload = await request.json()
    result = await send_command(
        request.app["pump_url"],
        str(payload.get("action", "")),
        request.app["timeout"],
    )
    return web.json_response(result, status=200 if result["success"] else 502)


def create_app(pump_url: str, timeout: float = 5.0) -> web.Application:
    app = web.Application()
    app["pump_url"] = pump_url
    app["timeout"] = timeout
    app.router.add_post("/pump", command_handler)
    return app


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pump-url", default="coap://127.0.0.1:5683")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8081)
    args = parser.parse_args()
    web.run_app(create_app(args.pump_url), host=args.host, port=args.port)


if __name__ == "__main__":
    main()
