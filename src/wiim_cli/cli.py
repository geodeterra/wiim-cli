"""WiiM CLI — control WiiM devices from the command line."""

from __future__ import annotations

import sys
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from wiim_cli.device import connect, disconnect, find_devices, run

app = typer.Typer(
    name="wiim",
    help="Control WiiM audio devices on your local network.",
    no_args_is_help=True,
)
console = Console()
err_console = Console(stderr=True)


def _resolve_host(host: str | None) -> str:
    """Return the host or auto-discover a single device."""
    if host:
        return host
    devices = run(find_devices())
    if len(devices) == 0:
        err_console.print("[red]No WiiM devices found on the network.[/red]")
        raise typer.Exit(1)
    if len(devices) > 1:
        err_console.print(
            f"[yellow]Multiple devices found ({len(devices)}). "
            "Use --host to pick one:[/yellow]"
        )
        for d in devices:
            err_console.print(f"  {d.host}  {d.name or '(unknown)'}")
        raise typer.Exit(1)
    return devices[0].host


# ---------------------------------------------------------------------------
# discover
# ---------------------------------------------------------------------------

@app.command()
def discover(
    timeout: int = typer.Option(5, help="SSDP discovery timeout in seconds."),
) -> None:
    """Discover WiiM devices on the local network."""
    devices = run(find_devices(timeout=timeout))
    if not devices:
        console.print("[yellow]No devices found.[/yellow]")
        raise typer.Exit(0)

    table = Table(title="WiiM Devices")
    table.add_column("Name", style="cyan")
    table.add_column("Host", style="green")
    table.add_column("Model")
    table.add_column("Firmware")
    table.add_column("UUID", style="dim")

    for d in devices:
        table.add_row(
            d.name or "—",
            d.host,
            d.model or "—",
            d.firmware or "—",
            d.uuid or "—",
        )

    console.print(table)


# ---------------------------------------------------------------------------
# status
# ---------------------------------------------------------------------------

@app.command()
def status(
    host: Optional[str] = typer.Option(None, help="Device IP or hostname."),
) -> None:
    """Show the current playback status."""

    async def _status():
        player = await connect(_resolve_host(host))
        try:
            table = Table(title=f"{player.name or player.host} — Status")
            table.add_column("Property", style="cyan")
            table.add_column("Value")

            state = player.play_state or "unknown"
            table.add_row("State", state)
            table.add_row("Volume", f"{int((player.volume_level or 0) * 100)}%")
            table.add_row("Muted", str(player.is_muted or False))
            table.add_row("Source", player.source or "—")
            table.add_row("Title", player.media_title or "—")
            table.add_row("Artist", player.media_artist or "—")
            table.add_row("Album", player.media_album or "—")

            pos = player.media_position
            dur = player.media_duration
            if pos is not None and dur is not None:
                table.add_row(
                    "Position",
                    f"{_fmt_time(pos)} / {_fmt_time(dur)}",
                )
            elif pos is not None:
                table.add_row("Position", _fmt_time(pos))

            table.add_row("Shuffle", str(player.shuffle or False))
            table.add_row("Repeat", player.repeat or "off")

            console.print(table)
        finally:
            await disconnect(player)

    run(_status())


def _fmt_time(seconds: int) -> str:
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


# ---------------------------------------------------------------------------
# play / pause / stop / next / prev
# ---------------------------------------------------------------------------

@app.command()
def play(
    host: Optional[str] = typer.Option(None, help="Device IP or hostname."),
) -> None:
    """Resume playback."""

    async def _play():
        player = await connect(_resolve_host(host))
        try:
            await player.play()
            console.print("[green]▶ Playing[/green]")
        finally:
            await disconnect(player)

    run(_play())


@app.command()
def pause(
    host: Optional[str] = typer.Option(None, help="Device IP or hostname."),
) -> None:
    """Pause playback."""

    async def _pause():
        player = await connect(_resolve_host(host))
        try:
            await player.pause()
            console.print("[yellow]⏸ Paused[/yellow]")
        finally:
            await disconnect(player)

    run(_pause())


@app.command()
def stop(
    host: Optional[str] = typer.Option(None, help="Device IP or hostname."),
) -> None:
    """Stop playback."""

    async def _stop():
        player = await connect(_resolve_host(host))
        try:
            await player.stop()
            console.print("[red]⏹ Stopped[/red]")
        finally:
            await disconnect(player)

    run(_stop())


@app.command(name="next")
def next_track(
    host: Optional[str] = typer.Option(None, help="Device IP or hostname."),
) -> None:
    """Skip to the next track."""

    async def _next():
        player = await connect(_resolve_host(host))
        try:
            await player.next_track()
            console.print("[green]⏭ Next track[/green]")
        finally:
            await disconnect(player)

    run(_next())


@app.command(name="prev")
def prev_track(
    host: Optional[str] = typer.Option(None, help="Device IP or hostname."),
) -> None:
    """Skip to the previous track."""

    async def _prev():
        player = await connect(_resolve_host(host))
        try:
            await player.previous_track()
            console.print("[green]⏮ Previous track[/green]")
        finally:
            await disconnect(player)

    run(_prev())


# ---------------------------------------------------------------------------
# volume
# ---------------------------------------------------------------------------

@app.command()
def volume(
    level: Optional[int] = typer.Argument(None, help="Volume 0-100. Omit to show current."),
    host: Optional[str] = typer.Option(None, help="Device IP or hostname."),
) -> None:
    """Get or set the volume (0-100)."""

    async def _volume():
        player = await connect(_resolve_host(host))
        try:
            if level is None:
                current = int((player.volume_level or 0) * 100)
                console.print(f"🔊 Volume: {current}%")
            else:
                clamped = max(0, min(100, level))
                await player.set_volume(clamped / 100.0)
                console.print(f"🔊 Volume set to {clamped}%")
        finally:
            await disconnect(player)

    run(_volume())


@app.command()
def mute(
    host: Optional[str] = typer.Option(None, help="Device IP or hostname."),
) -> None:
    """Mute the device."""

    async def _mute():
        player = await connect(_resolve_host(host))
        try:
            await player.set_mute(True)
            console.print("[yellow]🔇 Muted[/yellow]")
        finally:
            await disconnect(player)

    run(_mute())


@app.command()
def unmute(
    host: Optional[str] = typer.Option(None, help="Device IP or hostname."),
) -> None:
    """Unmute the device."""

    async def _unmute():
        player = await connect(_resolve_host(host))
        try:
            await player.set_mute(False)
            console.print("[green]🔊 Unmuted[/green]")
        finally:
            await disconnect(player)

    run(_unmute())


# ---------------------------------------------------------------------------
# play-url / play-preset
# ---------------------------------------------------------------------------

@app.command(name="play-url")
def play_url(
    url: str = typer.Argument(help="URL to play (MP3, FLAC, M3U, etc.)."),
    host: Optional[str] = typer.Option(None, help="Device IP or hostname."),
) -> None:
    """Play audio from a URL."""

    async def _play_url():
        player = await connect(_resolve_host(host))
        try:
            await player.play_url(url)
            console.print(f"[green]▶ Playing URL:[/green] {url}")
        finally:
            await disconnect(player)

    run(_play_url())


@app.command(name="play-preset")
def play_preset(
    preset: int = typer.Argument(help="Preset number (1-20)."),
    host: Optional[str] = typer.Option(None, help="Device IP or hostname."),
) -> None:
    """Play a saved preset by number."""

    async def _play_preset():
        player = await connect(_resolve_host(host))
        try:
            await player.play_preset(preset)
            console.print(f"[green]▶ Playing preset {preset}[/green]")
        finally:
            await disconnect(player)

    run(_play_preset())


@app.command()
def seek(
    position: int = typer.Argument(help="Position in seconds."),
    host: Optional[str] = typer.Option(None, help="Device IP or hostname."),
) -> None:
    """Seek to a position in the current track."""

    async def _seek():
        player = await connect(_resolve_host(host))
        try:
            await player.seek(position)
            console.print(f"[green]⏩ Seeked to {_fmt_time(position)}[/green]")
        finally:
            await disconnect(player)

    run(_seek())


@app.command()
def shuffle(
    enabled: bool = typer.Argument(help="true or false."),
    host: Optional[str] = typer.Option(None, help="Device IP or hostname."),
) -> None:
    """Enable or disable shuffle."""

    async def _shuffle():
        player = await connect(_resolve_host(host))
        try:
            await player.set_shuffle(enabled)
            state = "on" if enabled else "off"
            console.print(f"[green]🔀 Shuffle {state}[/green]")
        finally:
            await disconnect(player)

    run(_shuffle())


if __name__ == "__main__":
    app()
