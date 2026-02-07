# wiim-cli

CLI tool for controlling WiiM and LinkPlay audio devices on your local network.

Built with [pywiim](https://github.com/mjcumming/pywiim) and [typer](https://typer.tiangolo.com/).

## Install

```bash
uv tool install wiim-cli
```

Or run directly:

```bash
uvx --from wiim-cli wiim --help
```

Requires Python >=3.11.

## Usage

```
wiim discover              # Find devices
wiim status                # Show what's playing
wiim play / pause / stop   # Playback control
wiim next / prev           # Track navigation
wiim volume [0-100]        # Get/set volume
wiim mute / unmute         # Mute control
wiim play-url <url>        # Play audio from URL
wiim play-preset <n>       # Play saved preset
wiim seek <seconds>        # Seek in track
wiim shuffle true/false    # Toggle shuffle
```

All commands accept `--host <ip>` to target a specific device. If omitted and a single device is found on the network, it's used automatically.

## License

MIT
