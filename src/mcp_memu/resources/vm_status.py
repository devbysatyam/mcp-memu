"""MCP Resources — read-only data and guides exposed as MCP resources for agent context."""

from pymemuc import PyMemucError

from mcp_memu.utils.memuc_instance import memuc, get_protected_vms


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
        return """# MCP-MEmu Getting Started

## Key Concepts
- **VM Index**: Every VM has a numeric index (0, 1, 2...). Use list_vms to find them.
- **Protected VMs**: Pre-existing VMs are [PROTECTED] — cannot be deleted/stopped/renamed.
- **VM must be running** for: shell commands, screenshots, apps, tap/swipe, network.
- **VM must be stopped** for: CPU, RAM, resolution, and most config changes.
- **Admin required**: MEmu needs administrator privileges to run.

## Quick Start
1. list_vms() → see available VMs
2. boot_and_ready(vm_index=0) → start VM + wait for Android boot
3. screenshot_base64(vm_index=0) → see the screen
4. tap(vm_index=0, x=360, y=640) → tap center
5. execute_shell(vm_index=0, command="pm list packages") → list apps

## Screen Coordinates (720x1280 default)
- Center: (360, 640) | Top-left: (0, 0) | Nav bar: (360, 1240)

## Creating a Test VM
1. create_vm(vm_version="96") → Android 9 64-bit, returns new index
2. boot_and_ready(vm_index=NEW) → start it
3. Do testing...
4. delete_vm(vm_index=NEW) → clean up
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

