"""Device connection and discovery helpers."""

from __future__ import annotations

import asyncio
import logging
import socket
from dataclasses import dataclass
from urllib.parse import urlparse

from pywiim import Player, WiiMClient

logger = logging.getLogger(__name__)


@dataclass
class Device:
    """A discovered WiiM device."""

    host: str
    name: str | None = None
    model: str | None = None
    firmware: str | None = None
    uuid: str | None = None


async def find_devices(timeout: int = 5) -> list[Device]:
    """Discover WiiM/LinkPlay devices via SSDP then validate with the API."""
    hosts = await _ssdp_search(timeout)
    devices: list[Device] = []
    tasks = [_probe_device(host) for host in hosts]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    for result in results:
        if isinstance(result, Device):
            devices.append(result)
    return devices


async def _ssdp_search(timeout: int = 5) -> list[str]:
    """Raw SSDP M-SEARCH returning unique host IPs."""
    msg = (
        "M-SEARCH * HTTP/1.1\r\n"
        "HOST: 239.255.255.250:1900\r\n"
        'MAN: "ssdp:discover"\r\n'
        f"MX: {timeout}\r\n"
        "ST: urn:schemas-upnp-org:device:MediaRenderer:1\r\n"
        "\r\n"
    )
    loop = asyncio.get_event_loop()
    hosts: set[str] = set()

    def _do_search() -> set[str]:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(timeout + 1)
        try:
            sock.sendto(msg.encode(), ("239.255.255.250", 1900))
            found: set[str] = set()
            while True:
                try:
                    data, addr = sock.recvfrom(4096)
                    found.add(addr[0])
                except socket.timeout:
                    break
            return found
        finally:
            sock.close()

    hosts = await loop.run_in_executor(None, _do_search)
    return list(hosts)


async def _probe_device(host: str) -> Device | None:
    """Check if a host is a WiiM/LinkPlay device via its HTTP API."""
    client = WiiMClient(host)
    try:
        info = await client.get_device_info()
        if not info:
            return None
        return Device(
            host=host,
            name=info.get("DeviceName") or info.get("device_name"),
            model=info.get("project") or info.get("priv_prj"),
            firmware=info.get("firmware"),
            uuid=info.get("uuid"),
        )
    except Exception:
        return None
    finally:
        await client.close()


async def connect(host: str, timeout: float = 5.0) -> Player:
    """Create a Player connected to the given host."""
    client = WiiMClient(host, timeout=timeout)
    player = Player(client)
    await player.refresh()
    return player


async def disconnect(player: Player) -> None:
    """Close a player connection."""
    await player.client.close()


def run(coro):
    """Run an async coroutine synchronously."""
    return asyncio.run(coro)
