# Communication Protocol

## Pi–Arduino Communication

The Raspberry Pi and Arduino Nano communicate over a **USB serial cable**. The Pi sends text commands to control movement and steering, while the Nano sends back a status line once a distance-based move is finished.

### Communication Setup

- **Connection**: USB cable, Raspberry Pi ↔ Arduino Nano
- **Baud Rate**: `115200`
- **Protocol**: Plain text commands, comma-separated, one per line (`\n` terminated)
- **Warm-up**: Pi waits ~2 seconds after opening the port before sending anything, since opening the port resets the Nano

### Command Format

#### Pi → Nano (Movement Commands)

| Command Format | Description | Example |
|---|---|---|
| `SERVO,{angle}` | Set steering angle | `SERVO,97` |
| `MOTOR,{direction},{speed}` | Drive continuously | `MOTOR,1,200` |
| `MOVE,{direction},{speed},{ticks}` | Drive a fixed number of encoder ticks, then auto-stop | `MOVE,2,100,1100` |
| `STOP` | Stop the drive motor | `STOP` |
| `RESET` | Reset the encoder tick counter to zero | `RESET` |

**Parameters:**
- `angle`: servo position (steering)
- `direction`: `0` = stop, `1` = forward, `2` = reverse
- `speed`: motor PWM value, `0`–`255`
- `ticks`: number of encoder ticks to travel — this is what makes `MOVE` cover the same distance regardless of speed

#### Nano → Pi (Status Updates)

| Message | Description |
|---|---|
| `DONE,{ticks_moved}` | A `MOVE` command finished — reports ticks actually travelled |
| `DONE,{ticks_moved},TIMEOUT` | `MOVE` gave up early (e.g. robot got stuck) |

### Code Implementation

**Nano side:**
- Listens for `SERVO` / `MOTOR` / `MOVE` / `STOP` / `RESET` commands
- Drives the servo and motor accordingly
- Counts encoder ticks and replies `DONE` once a `MOVE` target is reached

**Pi side:**
- Sends steering + drive commands based on the computer vision pipeline
- Uses `MOVE` (and waits for `DONE`) for parking, where consistent distance matters more than speed
- Uses `MOTOR`/`SERVO` for normal lap driving, where continuous control matters more
