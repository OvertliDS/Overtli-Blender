from __future__ import annotations

import json
import logging
import socket
from dataclasses import dataclass, field
from typing import Any

from .transport import encode_command, receive_full_response


logger = logging.getLogger("BlenderMCPServer")


@dataclass
class BlenderConnection:
    host: str
    port: int
    timeout_seconds: float = 15.0
    sock: socket.socket | None = field(default=None, repr=False)

    def connect(self) -> bool:
        """Connect to the Blender addon socket server."""
        if self.sock:
            return True

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            logger.info("Connected to Blender at %s:%s", self.host, self.port)
            return True
        except Exception as exc:
            logger.error("Failed to connect to Blender: %s", exc)
            self.sock = None
            return False

    def disconnect(self) -> None:
        """Disconnect from the Blender addon."""
        if self.sock:
            try:
                self.sock.close()
            except Exception as exc:
                logger.error("Error disconnecting from Blender: %s", exc)
            finally:
                self.sock = None

    def send_command(self, command_type: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Send a command to Blender and return the response."""
        if not self.sock and not self.connect():
            raise ConnectionError("Not connected to Blender")

        command = {
            "type": command_type,
            "params": params or {},
        }

        try:
            logger.info("Sending command: %s with params: %s", command_type, params)
            self.sock.sendall(encode_command(command))
            logger.info("Command sent, waiting for response...")

            response = receive_full_response(self.sock, timeout_seconds=self.timeout_seconds)
            logger.info("Response parsed, status: %s", response.get("status", "unknown"))

            if response.get("status") == "error":
                logger.error("Blender error: %s", response.get("message"))
                raise Exception(response.get("message", "Unknown error from Blender"))

            return response.get("result", {})
        except socket.timeout:
            logger.error("Socket timeout while waiting for response from Blender")
            self.sock = None
            raise Exception("Timeout waiting for Blender response - try simplifying your request")
        except (ConnectionError, BrokenPipeError, ConnectionResetError) as exc:
            logger.error("Socket connection error: %s", exc)
            self.sock = None
            raise Exception(f"Connection to Blender lost: {str(exc)}")
        except json.JSONDecodeError as exc:
            logger.error("Invalid JSON response from Blender: %s", exc)
            self.sock = None
            raise Exception(f"Invalid response from Blender: {str(exc)}")
        except Exception as exc:
            logger.error("Error communicating with Blender: %s", exc)
            self.sock = None
            raise Exception(f"Communication error with Blender: {str(exc)}")
