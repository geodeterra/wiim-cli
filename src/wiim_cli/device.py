"""Device connection and discovery helpers."""

from __future__ import annotations

import asyncio

from pywiim import Player, WiiMClient, discover_devices
from pywiim.discovery import DiscoveredDevice


async def find_devices(timeout: int = 5) -> list[DiscoveredDevice]:
    """Discover WiiM/LinkPlay devices on the local network."""
    return await discover_devices(ssdp_timeout=timeout)


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
