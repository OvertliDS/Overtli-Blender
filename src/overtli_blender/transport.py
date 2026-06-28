from __future__ import annotations

import json
import logging
import socket
from typing import Any


logger = logging.getLogger("OvertliBlenderServer")
DEFAULT_BUFFER_SIZE = 8192
TRANSPORT_METADATA_KEYS = {
    "ctx",
    "context",
    "_ctx",
    "_context",
    "request_context",
    "tool_context",
}


class _DropValue:
    pass


DROP_VALUE = _DropValue()


def sanitize_for_transport(value: Any) -> Any:
    """Return a JSON-safe command payload without MCP transport internals."""
    if callable(value):
        return DROP_VALUE
    if isinstance(value, dict):
        clean: dict[str, Any] = {}
        for key, item in value.items():
            if key in TRANSPORT_METADATA_KEYS:
                continue
            cleaned = sanitize_for_transport(item)
            if cleaned is not DROP_VALUE:
                clean[key] = cleaned
        return clean
    if isinstance(value, (list, tuple)):
        clean_items = []
        for item in value:
            cleaned = sanitize_for_transport(item)
            if cleaned is not DROP_VALUE:
                clean_items.append(cleaned)
        return clean_items
    try:
        json.dumps(value)
        return value
    except (TypeError, ValueError):
        return str(value)


def encode_command(command: dict[str, Any]) -> bytes:
    return json.dumps(sanitize_for_transport(command)).encode("utf-8")


def decode_response(data: bytes) -> dict[str, Any]:
    return json.loads(data.decode("utf-8"))


def receive_full_response(sock: socket.socket, *, timeout_seconds: float) -> dict[str, Any]:
    chunks: list[bytes] = []
    sock.settimeout(timeout_seconds)

    try:
        while True:
            try:
                chunk = sock.recv(DEFAULT_BUFFER_SIZE)
                if not chunk:
                    if not chunks:
                        raise ConnectionError("Connection closed before receiving any data")
                    break

                chunks.append(chunk)

                try:
                    data = b"".join(chunks)
                    response = decode_response(data)
                    logger.info("Received complete response (%d bytes)", len(data))
                    return response
                except json.JSONDecodeError:
                    continue
            except socket.timeout:
                logger.warning("Socket timeout during chunked receive")
                break
            except (ConnectionError, BrokenPipeError, ConnectionResetError) as exc:
                logger.error("Socket connection error during receive: %s", exc)
                raise
    except socket.timeout:
        logger.warning("Socket timeout during chunked receive")
    except Exception as exc:
        logger.error("Error during receive: %s", exc)
        raise

    if chunks:
        data = b"".join(chunks)
        logger.info("Returning data after receive completion (%d bytes)", len(data))
        try:
            return decode_response(data)
        except json.JSONDecodeError as exc:
            raise Exception("Incomplete JSON response received") from exc

    raise Exception("No data received")


