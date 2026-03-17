"""MCP Resources — read-only data and guides exposed as MCP resources for agent context."""

from pymemuc import PyMemucError

from utils.memuc_instance import memuc, get_protected_vms


def register_resources(mcp):
    """Register all MCP resources with the server."""

    @mcp.resource("memu://vms")
    def all_vms_resource() -> str:
        """List all MEmu VM instances with their current status."""
        try:
            vms = memuc.list_vm_info()
            if not vms:
                return "No VMs found."
            protected = get_protected_vms()
            protected_indices = {vm["index"] for vm in protected}
            lines = []
            for vm in vms:
                status = "running" if vm["running"] else "stopped"
                tag = " [PROTECTED]" if vm["index"] in protected_indices else ""
                lines.append(
                    f"Index: {vm['index']} | Name: {vm['title']} | "
                    f"Status: {status} | PID: {vm['pid']}{tag}"
                )
            return "\n".join(lines)
        except PyMemucError as e:
            return f"Error: {e}"

    @mcp.resource("memu://vm/{vm_index}/status")
    def vm_status_resource(vm_index: int) -> str:
        """Get the running status of a specific VM."""
        try:
            running = memuc.vm_is_running(vm_index=vm_index)
            return "running" if running else "stopped"
        except PyMemucError as e:
            return f"Error: {e}"

    @mcp.resource("memu://guide")
    def getting_started_guide() -> str:
        """Getting started guide — read this first to understand how to use MCP-MEmu."""
        return """# MCP-MEmu Getting Started Guide

## What is MCP-MEmu?
MCP-MEmu controls MEmu Android Emulator through 60+ tools. You can manage VMs,
install apps, automate UI, take screenshots, transfer files, spoof GPS, and more.

## KEY RULES (read these FIRST)

### State Requirements
| VM State | Available Tools | Unavailable |
|----------|----------------|-------------|
| STOPPED | Config (CPU, RAM, resolution), create, delete, clone, export, import | Screenshots, shell, apps, input, network |
| RUNNING | Screenshot, shell, apps, input, network, file transfer, clipboard | Most config changes |

### Anti-Hallucination Rules
1. NEVER guess screen coordinates — always take a screenshot first
2. NEVER assume an operation succeeded — check the return message
3. NEVER try to modify protected VMs (index 0 is usually protected)
4. NEVER run config changes on a running VM — stop it first
5. If a tool returns an error, REPORT the exact error to the user
6. If a screenshot is blank (<10KB), it's a DirectX rendering issue, NOT your fault

### Error Recovery Patterns
| Error | Likely Cause | Fix |
|-------|-------------|-----|
| "Failed to get adb connection" | VM not running or WiFi off | start_vm() or connect_network() |
| "protected VM" | Trying destructive op on VM 0 | Use a non-protected VM |
| Blank screenshot | DirectX rendering | set_vm_config(key="graphics_render_mode", value="0"), reboot |
| "clone vm failed" | Low disk space | Free space (need 2-4GB) |
| Tool timeout | ADB daemon stuck | reboot_vm() |
| "Max retries exceeded" | VM not fully booted | wait_for_boot() |

## Quick Start Workflow
1. list_vms() → see available VMs and their status
2. boot_and_ready(vm_index=0) → start VM + wait for Android boot
3. screenshot_base64(vm_index=0) → see the screen (will be base64 PNG)
4. tap(vm_index=0, x=360, y=640) → interact with the screen
5. execute_shell(vm_index=0, command="pm list packages") → list installed apps

## Screen Coordinate System (default 720x1280)
Origin (0,0) is TOP-LEFT. X increases rightward, Y increases downward.

```
(0,0)───────────────────(720,0)
│      Status Bar           │    y: 0-50
│───────────────────────────│
│                           │
│     App Content Area      │    y: 50-1200
│     Center: (360, 640)    │
│                           │
│───────────────────────────│
│  ◁(120) ○(360) □(600)    │    y: 1200-1280 (nav bar)
(0,1280)────────────(720,1280)
```

## Creating a Test VM (safe to experiment with)
1. create_vm(vm_version="96") → returns new index (this VM is NOT protected)
2. set_vm_cpu(vm_index=NEW, cores=2) (while stopped)
3. set_vm_memory(vm_index=NEW, mb=2048) (while stopped)
4. boot_and_ready(vm_index=NEW) → start it
5. Do your testing...
6. stop_vm(vm_index=NEW) → stop when done
7. delete_vm(vm_index=NEW) → clean up

## Available Prompts (use these for step-by-step guidance)
- automate_app_testing — Full app testing workflow
- setup_new_vm — Create and configure a VM from scratch
- ui_automation_guide — Detailed coordinate and interaction guide
- batch_device_farm — Set up multiple VMs
- debug_vm_issues — Diagnose problems
- gps_spoofing_guide — GPS location presets
- file_transfer_guide — Push/pull files with path reference
"""

    @mcp.resource("memu://workflows")
    def common_workflows() -> str:
        """Common step-by-step workflows for automation tasks."""
        return """# Common Workflows

## Install & Test App
1. boot_and_ready(vm_index=0)
2. install_apk(vm_index=0, apk_path="C:\\\\path\\\\app.apk")
3. launch_app(vm_index=0, package="com.example.app")
4. screenshot_base64(vm_index=0)

## UI Automation
1. get_screen_size(vm_index=0) → resolution
2. screenshot_base64(vm_index=0) → see screen
3. tap(vm_index=0, x=100, y=200) → tap button
4. input_text(vm_index=0, text="hello") → type text
5. press_enter(vm_index=0) → submit

## Device Config (VM must be stopped first!)
1. stop_vm(vm_index=1)
2. set_vm_cpu(vm_index=1, cores=4)
3. set_vm_memory(vm_index=1, mb=4096)
4. set_vm_resolution(vm_index=1, width=1080, height=1920, dpi=480)
5. boot_and_ready(vm_index=1)

## GPS Spoofing
set_gps_location(vm_index=0, lat=37.7749, lng=-122.4194)  # San Francisco

## File Transfer
push_file(vm_index=0, local_path="C:\\\\f.txt", remote_path="/sdcard/f.txt")
pull_file(vm_index=0, remote_path="/sdcard/f.txt", local_path="C:\\\\out.txt")

## Read All Config
get_all_vm_config(vm_index=0)  → returns all key values in one call
"""

    @mcp.resource("memu://config-keys")
    def config_keys_reference() -> str:
        """Complete reference of all valid VM configuration keys and their descriptions."""
        return """# VM Configuration Keys (for get_vm_config / set_vm_config)

## Hardware
| Key | Description | Values |
|-----|-------------|--------|
| cpus | CPU cores | 1, 2, 4, 8 |
| cpucap | CPU cap percentage | 0-100 |
| memory | RAM in MB | e.g. 1024, 2048, 4096 |

## Display
| Key | Description | Values |
|-----|-------------|--------|
| is_full_screen | Fullscreen mode | 0/1 |
| is_hide_toolbar | Hide toolbar | 0/1 |
| is_customed_resolution | Custom resolution | 0/1 |
| resolution_width | Width (pixels) | e.g. 720, 1080 |
| resolution_height | Height (pixels) | e.g. 1280, 1920 |
| vbox_dpi | Screen DPI | e.g. 240, 480 |
| fps | Frames per second | 0-100 |
| graphics_render_mode | Renderer | 0=OpenGL, 1=DirectX |
| start_window_mode | Start position | 0=Default, 1=Last, 2=Custom |
| win_x | Window X position | pixels |
| win_y | Window Y position | pixels |
| win_scaling_percent2 | Window scaling | percentage |
| disable_resize | Fixed window size | 0=stretchable, 1=fixed |
| geometry | Window geometry | "x y width height" |
| custom_resolution | Resolution+DPI | "width height dpi" |

## Device Identity
| Key | Description | Values |
|-----|-------------|--------|
| name | VM name | string |
| imei | Device IMEI | string |
| imsi | SIM IMSI | string |
| simserial | SIM serial | string |
| linenum | Phone number | string |
| microvirt_vm_brand | Device brand | e.g. "samsung" |
| microvirt_vm_model | Device model | e.g. "SM-G950F" |
| microvirt_vm_manufacturer | Manufacturer | e.g. "Samsung" |
| macaddress | MAC address | string |
| ssid | WiFi name | string or "auto" |

## Performance
| Key | Description | Values |
|-----|-------------|--------|
| turbo_mode | Turbo mode | 0/1 |
| cache_mode | Cache mode | 0=stable, 1=fast |
| enable_su | Root (superuser) | 0/1 |
| enable_audio | Audio support | 0/1 |
| sync_time | Time sync | 0/1 |

## GPS
| Key | Description | Values |
|-----|-------------|--------|
| latitude | GPS latitude | degrees (float) |
| longitude | GPS longitude | degrees (float) |
| selected_map | Map provider | 0=Google, 1=Baidu |

## Input & Layout
| Key | Description | Values |
|-----|-------------|--------|
| vkeyboard_mode | Virtual keyboard | 0/1 |
| phone_layout | Phone layout | 0=Bottom, 1=Right, 2=Toolbar |

## Shared Folders
| Key | Description | Values |
|-----|-------------|--------|
| picturepath | Shared pictures | local path |
| musicpath | Shared music | local path |
| moviepath | Shared movies | local path |
| downloadpath | Shared downloads | local path |
"""

    @mcp.resource("memu://tools")
    def tool_reference() -> str:
        """Complete reference of all available MCP-MEmu tools for LLM context."""
        return """# MCP-MEmu Tool Reference

## Lifecycle (manage VM instances)
| Tool | Args | Description |
|------|------|-------------|
| list_vms | — | List all VMs with index, name, status, PID |
| get_vm_status | vm_index | Check if VM is running or stopped |
| start_vm | vm_index | Boot a VM |
| stop_vm | vm_index | Stop a VM (blocked on protected VMs) |
| stop_all_vms | — | Stop all non-protected VMs |
| reboot_vm | vm_index | Reboot a VM (blocked on protected) |
| create_vm | vm_version="96" | Create new VM (76=Android 7, 96=Android 9) |
| delete_vm | vm_index | Delete a VM (blocked on protected) |
| clone_vm | vm_index, new_name? | Clone a VM (source must be stopped) |
| rename_vm | vm_index, new_name | Rename a VM |
| export_vm | vm_index, output_path | Export to .ova file |
| import_vm | ova_path | Import from .ova file |
| compress_vm | vm_index | Compress disk image |
| sort_out_all_vms | — | Re-tile VM windows |
| check_task_status | task_id | Check async task status |

## Configuration (read/write VM settings)
| Tool | Args | Description |
|------|------|-------------|
| get_all_vm_config | vm_index | Get all common config values at once |
| get_vm_config | vm_index, key | Get a single config value |
| set_vm_config | vm_index, key, value | Set a config value (VM must be stopped) |
| set_vm_cpu | vm_index, cores | Set CPU cores (1/2/4/8) |
| set_vm_memory | vm_index, mb | Set RAM in MB |
| set_vm_resolution | vm_index, width, height, dpi | Set screen resolution |
| set_vm_gps | vm_index, lat, lng | Set GPS coordinates |
| randomize_vm_device | vm_index | Randomize device fingerprint |

## App Management
| Tool | Args | Description |
|------|------|-------------|
| list_apps | vm_index | List installed packages |
| install_apk | vm_index, apk_path | Install APK file |
| uninstall_app | vm_index, package | Uninstall by package name |
| launch_app | vm_index, package | Launch app |
| stop_app | vm_index, package | Force stop app |
| clear_app_data | vm_index, package | Clear app data/cache |
| create_app_shortcut | vm_index, package | Create desktop shortcut |

## UI Interaction (VM must be running)
| Tool | Args | Description |
|------|------|-------------|
| tap | vm_index, x, y | Tap at coordinates |
| swipe | vm_index, x1, y1, x2, y2, duration_ms=300 | Swipe gesture |
| long_press | vm_index, x, y, duration_ms=1000 | Long press |
| input_text | vm_index, text | Type text into focused field |
| send_key | vm_index, key | Send key (home/back/menu/volumeup/volumedown) |
| press_enter | vm_index | Press Enter |
| press_back | vm_index | Press Back |
| press_home | vm_index | Press Home |
| shake_device | vm_index | Shake gesture |
| rotate_screen | vm_index | Toggle orientation |
| zoom_in | vm_index | Pinch zoom in |
| zoom_out | vm_index | Pinch zoom out |
| scroll_up | vm_index, x=540 | Scroll up |
| scroll_down | vm_index, x=540 | Scroll down |

## Screenshot & Capture
| Tool | Args | Description |
|------|------|-------------|
| take_screenshot | vm_index, save_path | Save screenshot to file |
| screenshot_base64 | vm_index | Get screenshot as base64 PNG |
| get_screen_size | vm_index | Get resolution (width x height) |

## Network & Sensors
| Tool | Args | Description |
|------|------|-------------|
| connect_network | vm_index | Enable internet |
| disconnect_network | vm_index | Disable internet |
| get_public_ip | vm_index | Get public IP address |
| set_gps_location | vm_index, lat, lng | Spoof GPS coordinates |
| set_accelerometer | vm_index, x, y, z | Set accelerometer values |
| get_adb_connection_info | vm_index | Get ADB host:port |

## Shell & Advanced
| Tool | Args | Description |
|------|------|-------------|
| execute_shell | vm_index, command | Run shell command via execcmd |
| send_adb | vm_index, command | Send raw ADB command |
| get_device_info | vm_index | Get model, Android version, CPU, language |
| get_running_apps | vm_index | List running processes |
| pull_file | vm_index, remote_path, local_path | Pull file from VM |
| push_file | vm_index, local_path, remote_path | Push file to VM |
| set_clipboard | vm_index, text | Set clipboard text |
| get_clipboard | vm_index | Read clipboard |

## Compound (high-level operations)
| Tool | Args | Description |
|------|------|-------------|
| wait_for_boot | vm_index, timeout=60 | Wait for Android boot |
| boot_and_ready | vm_index, timeout=120 | Start + wait for boot |
| fresh_start_app | vm_index, package | Stop → clear data → relaunch |
| install_and_launch | vm_index, apk_path, package | Install + launch |
| clone_and_configure | source_vm, cpu, memory, width, height, dpi | Clone + configure |
| batch_install | vm_index, apk_paths (;-separated) | Install multiple APKs |
| full_vm_snapshot | vm_index, backup_dir | Stop → export → restart |
| run_monkey_test | vm_index, package, events=500 | Random UI stress test |

## Important Notes
- Commands are validated against a blocklist (rm -rf /, mkfs, dd, etc.)
- Protected VMs cannot be deleted, stopped, renamed, or rebooted
- VM must be RUNNING for: shell, screenshot, input, apps, network
- VM must be STOPPED for: CPU, RAM, resolution config changes
"""

    @mcp.resource("memu://security")
    def security_info() -> str:
        """Security model and protections built into MCP-MEmu."""
        return """# MCP-MEmu Security

## Protected VMs
Pre-existing VMs are snapshotted on first launch. Destructive operations
(delete, stop, rename, reboot) are BLOCKED on protected VMs.

## Input Validation
- vm_index must be a non-negative integer
- Shell commands are checked against a blocklist:
  rm -rf /, mkfs, dd if=, reboot, shutdown, format, wipe

## Audit Logging
All destructive operations are logged with timestamps to stderr:
  [AUDIT 2026-03-17 11:00:00] delete_vm vm_index=1
  [AUDIT 2026-03-17 11:00:05] BLOCKED vm_index=0 operation=delete_vm

## Transport Security
This server uses stdio (local only). For remote deployment,
implement OAuth 2.1 with PKCE per the MCP specification.
"""
