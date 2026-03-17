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

    # ═══════════════════════════════════════════════════════════════
    # GUIDE — The first thing an LLM should read
    # ═══════════════════════════════════════════════════════════════
    @mcp.resource("memu://guide")
    def getting_started_guide() -> str:
        """Getting started guide — read this first to understand how to use MCP-MEmu."""
        return """# MCP-MEmu Complete Guide

## What is MCP-MEmu?
MCP-MEmu controls MEmu Android Emulator through 69 tools. You can manage VMs,
install apps, automate UI, take screenshots, transfer files, spoof GPS, and more.
It wraps the MEMUC CLI via PyMEMUC and exposes everything through the MCP protocol.

## CRITICAL RULES — Read Before Doing Anything

### 1. VM State Requirements
| VM State | What Works | What Does NOT Work |
|----------|-----------|-------------------|
| STOPPED | Config changes (CPU, RAM, resolution, GPS), clone, export, import, delete, compress | Screenshots, shell, apps, input, network, clipboard, file transfer |
| RUNNING | Screenshots, shell commands, apps, UI input, network, file push/pull, clipboard | Most config changes (CPU, RAM, resolution) |

### 2. Anti-Hallucination Rules
These rules MUST be followed to avoid incorrect outputs:

1. **NEVER guess screen coordinates** — ALWAYS call screenshot_base64() first, then analyze the image to find button/element positions
2. **NEVER assume an operation succeeded** — check the return message from every tool call
3. **NEVER try to modify protected VMs** — VM index 0 is typically protected. Use list_vms() to check which have [PROTECTED] tag
4. **NEVER run config changes on a running VM** — you MUST stop_vm() first, then change config, then boot_and_ready()
5. **NEVER assume an app is installed** — call list_apps() to check, or install_apk() first
6. **If a tool returns an error, REPORT the exact error** — do NOT make up success messages
7. **If a screenshot is blank or very small (<10KB)** — this means DirectX rendering is active, NOT a bug in your code. Tell the user to set graphics_render_mode=0 (OpenGL)
8. **NEVER fabricate tool names** — only use the exact tool names listed in memu://tools
9. **NEVER pass string values where integers are expected** — vm_index is always an integer, never a string
10. **NEVER try to clone a running VM** — clone requires the source VM to be STOPPED

### 3. Error Recovery Patterns
| Error Message | Cause | How to Fix |
|--------------|-------|-----------|
| "Failed to get adb connection" | VM not running or WiFi disabled | Call start_vm() then connect_network() |
| "protected VM" | Destructive op on pre-existing VM | Use a VM you created with create_vm() |
| Blank/tiny screenshot | DirectX rendering mode | set_vm_config(key="graphics_render_mode", value="0") then reboot_vm() |
| "clone vm failed" | Insufficient disk space (need 2-4GB) | Free disk space or delete unused VMs |
| Tool hangs/timeout | ADB daemon crashed | Call reboot_vm() to restart |
| "Max retries exceeded" | VM not fully booted yet | Call wait_for_boot() or boot_and_ready() |
| "Failed to start app" | App not installed | Call install_apk() first |
| "command matches dangerous pattern" | Blocked by security layer | Use a safe alternative command |

### 4. Screen Coordinate System
Default resolution is 720x1280. Origin (0,0) is TOP-LEFT.
X increases rightward, Y increases downward.

```
(0,0)───────────────────────(720,0)
│        Status Bar              │   y: 0-50
│────────────────────────────────│
│                                │
│                                │
│      App Content Area          │   y: 50-1200
│      Center: (360, 640)        │
│                                │
│                                │
│────────────────────────────────│
│  ◁ Back   ○ Home   □ Recent   │   y: 1200-1280
│  (120)    (360)    (600)       │   (navigation bar)
(0,1280)─────────────────(720,1280)
```

Common tap targets:
- Screen center: tap(x=360, y=640)
- Back button: tap(x=120, y=1240) OR press_back()
- Home button: tap(x=360, y=1240) OR press_home()
- Top-left menu/back: tap(x=60, y=80)
- Top-right settings: tap(x=660, y=80)

### 5. Swipe Directions (IMPORTANT — often confused)
- **Scroll DOWN** (see content below): swipe(x1=360, y1=1000, x2=360, y2=300)  — finger moves UP
- **Scroll UP** (see content above): swipe(x1=360, y1=300, x2=360, y2=1000)  — finger moves DOWN
- **Swipe LEFT** (next page): swipe(x1=600, y1=640, x2=100, y2=640)  — finger moves LEFT
- **Swipe RIGHT** (prev page): swipe(x1=100, y1=640, x2=600, y2=640)  — finger moves RIGHT

Or use: scroll_up() and scroll_down() which handle this automatically.

### 6. Quick Start Workflow
```
1. list_vms()                          → see VMs and their status
2. boot_and_ready(vm_index=0)          → start VM + wait for Android boot
3. screenshot_base64(vm_index=0)       → see the current screen
4. tap(vm_index=0, x=360, y=640)       → tap center of screen
5. screenshot_base64(vm_index=0)       → verify what happened
```

### 7. Creating a Safe Test VM
```
1. create_vm(vm_version="96")          → returns new index (NOT protected)
2. set_vm_cpu(vm_index=NEW, cores=2)   → while VM is stopped
3. set_vm_memory(vm_index=NEW, mb=2048)
4. boot_and_ready(vm_index=NEW)        → start and wait
5. ... do testing ...
6. stop_vm(vm_index=NEW)               → stop when done
7. delete_vm(vm_index=NEW)             → clean up (only non-protected)
```

### 8. Available Prompts
Use these for guided step-by-step workflows:
- automate_app_testing — Full app testing with screenshot-first rules
- setup_new_vm — Create and configure a VM from scratch
- ui_automation_guide — Detailed coordinate and interaction guide
- batch_device_farm — Set up multiple VMs with diverse configs
- debug_vm_issues — Diagnostic flowchart with error-fix mapping
- gps_spoofing_guide — GPS presets for 10 cities
- file_transfer_guide — Push/pull files with VM path reference

### 9. Key Android Shell Commands (for execute_shell)
| Command | What it does |
|---------|-------------|
| pm list packages | List all installed packages |
| pm list packages -3 | List third-party apps only |
| dumpsys meminfo PKG | Memory usage of an app |
| dumpsys gfxinfo PKG | Frame rate / rendering info |
| dumpsys battery | Battery status |
| top -n 1 | CPU usage snapshot |
| df | Disk usage |
| getprop ro.product.model | Device model name |
| getprop ro.build.version.release | Android version |
| settings put secure location_mode 3 | Enable GPS |
| am start -a android.intent.action.VIEW -d URL | Open URL |
| uiautomator dump /sdcard/ui.xml | Dump UI hierarchy to XML |
| content query --uri content://sms | Read SMS messages |
| input keyevent 26 | Power button |
| input keyevent 187 | Recent apps |
| screencap -p /sdcard/screen.png | Take screenshot to file |
| logcat -d -t 100 | Last 100 log lines |
"""

    # ═══════════════════════════════════════════════════════════════
    # WORKFLOWS — 15 detailed automation recipes
    # ═══════════════════════════════════════════════════════════════
    @mcp.resource("memu://workflows")
    def common_workflows() -> str:
        """Step-by-step automation workflows for common tasks."""
        return """# MCP-MEmu Automation Workflows

## 1. Install & Test App
```
1. boot_and_ready(vm_index=0)
2. install_apk(vm_index=0, apk_path="C:\\\\path\\\\app.apk")
3. launch_app(vm_index=0, package="com.example.app")
4. screenshot_base64(vm_index=0)    # verify app launched
5. tap(vm_index=0, x=360, y=500)    # interact with UI
6. take_screenshot(vm_index=0, save_path="C:\\\\results\\\\test1.png")
```

## 2. UI Automation (Screenshot-First Pattern)
The golden rule: ALWAYS screenshot -> analyze -> act -> verify
```
1. screenshot_base64(vm_index=0)         # analyze current screen
2. tap(vm_index=0, x=360, y=200)        # tap identified button
3. screenshot_base64(vm_index=0)         # verify tap result
4. input_text(vm_index=0, text="hello")  # type in focused field
5. press_enter(vm_index=0)               # submit
6. screenshot_base64(vm_index=0)         # verify submission
```

## 3. App Onboarding Flow
```
1. fresh_start_app(vm_index=0, package="com.example.app")  # clean state
2. screenshot_base64(vm_index=0)      # see welcome screen
3. swipe(vm_index=0, x1=600, y1=640, x2=100, y2=640, duration_ms=300)  # next
4. screenshot_base64(vm_index=0)      # see page 2
5. tap(vm_index=0, x=360, y=1100)     # "Get Started" button
6. input_text(vm_index=0, text="user@example.com")
7. press_enter(vm_index=0)
```

## 4. Multi-Account Device Farm
```
1. create_vm(vm_version="96")             # VM A
2. create_vm(vm_version="96")             # VM B
3. create_vm(vm_version="96")             # VM C
4. randomize_vm_device(vm_index=A)        # unique fingerprint each
5. randomize_vm_device(vm_index=B)
6. randomize_vm_device(vm_index=C)
7. set_gps_location(vm_index=A, lat=40.7128, lng=-74.0060)   # NYC
8. set_gps_location(vm_index=B, lat=51.5074, lng=-0.1278)    # London
9. set_gps_location(vm_index=C, lat=35.6762, lng=139.6503)   # Tokyo
10. boot_and_ready for each VM
```

## 5. Social Media Automation
```
1. boot_and_ready(vm_index=0)
2. randomize_vm_device(vm_index=0)      # look like real device
3. set_gps_location(vm_index=0, ...)    # realistic location
4. launch_app(vm_index=0, package="com.instagram.android")
5. screenshot_base64(vm_index=0)        # see login
6. tap username field -> input_text -> tap password -> input_text
7. tap login button
8. screenshot_base64(vm_index=0)        # verify logged in
```

## 6. Game Automation
```
1. boot_and_ready(vm_index=0)
2. launch_app(vm_index=0, package="com.game.example")
3. screenshot_base64(vm_index=0)       # see game screen
4. Use tap/swipe/long_press for game inputs
5. For AFK farming: repeat tap at intervals
6. take_screenshot to capture progress
```

## 7. Data Extraction from App
```
1. launch_app(vm_index=0, package="com.target.app")
2. screenshot_base64(vm_index=0)        # read visible data
3. scroll_down(vm_index=0)              # load more content
4. screenshot_base64(vm_index=0)        # read next batch
5. execute_shell(vm_index=0, command="dumpsys activity activities")
6. execute_shell(vm_index=0, command="content query --uri content://...")
```

## 8. Performance Testing
```
1. launch_app(vm_index=0, package="com.example.app")
2. execute_shell(vm_index=0, command="dumpsys meminfo com.example.app")
3. execute_shell(vm_index=0, command="dumpsys gfxinfo com.example.app")
4. execute_shell(vm_index=0, command="dumpsys battery")
5. execute_shell(vm_index=0, command="top -n 1")
6. run_monkey_test(vm_index=0, package="com.example.app", events=1000)
```

## 9. Accessibility Testing
```
1. execute_shell(vm_index=0, command="settings put secure accessibility_enabled 1")
2. launch_app(vm_index=0, package="com.example.app")
3. execute_shell(vm_index=0, command="uiautomator dump /sdcard/ui.xml")
4. pull_file(vm_index=0, remote_path="/sdcard/ui.xml", local_path="C:\\\\ui.xml")
   # Analyze XML for content-description, clickable, focusable attributes
```

## 10. Network Condition Testing
```
1. launch_app(vm_index=0, package="com.example.app")
2. disconnect_network(vm_index=0)        # go offline
3. screenshot_base64(vm_index=0)         # check offline handling
4. connect_network(vm_index=0)           # restore
5. screenshot_base64(vm_index=0)         # check recovery behavior
```

## 11. Screenshot Documentation (App Walkthrough)
```
1. launch_app(vm_index=0, package="com.example.app")
2. take_screenshot(vm_index=0, save_path="C:\\\\docs\\\\01_home.png")
3. tap to navigate to feature A
4. take_screenshot(vm_index=0, save_path="C:\\\\docs\\\\02_feature.png")
5. Repeat for all screens
```

## 12. Regression Testing (Old vs New Version)
```
1. install_apk(vm_index=0, apk_path="old_version.apk")
2. launch_app -> take_screenshot -> save as old_home.png
3. install_apk(vm_index=0, apk_path="new_version.apk")  # upgrade
4. launch_app -> take_screenshot -> save as new_home.png
   # Compare old vs new screenshots
```

## 13. Deep Link & Clipboard Testing
```
1. set_clipboard(vm_index=0, text="https://example.com/deep?id=123")
2. execute_shell(vm_index=0, command="am start -a android.intent.action.VIEW -d 'https://example.com/deep?id=123'")
3. screenshot_base64(vm_index=0)        # verify deep link opened
4. get_clipboard(vm_index=0)            # verify clipboard
```

## 14. Batch APK Testing Pipeline
```
1. batch_install(vm_index=0, apk_paths="app1.apk;app2.apk;app3.apk")
2. For each app:
   a. launch_app -> screenshot -> verify
   b. run_monkey_test(events=200) -> check stability
   c. stop_app
3. list_apps(vm_index=0) -> verify all installed
```

## 15. VM Backup & Restore
```
Backup: full_vm_snapshot(vm_index=0, backup_dir="C:\\\\backups")
Restore: import_vm(ova_path="C:\\\\backups\\\\vm_backup.ova")
```

## GOLDEN RULES FOR ALL WORKFLOWS
- ALWAYS screenshot before tapping — NEVER guess coordinates
- VM RUNNING for: shell, screenshot, input, apps, network
- VM STOPPED for: CPU, RAM, resolution config changes
- Protected VMs CANNOT be deleted/stopped/renamed
- Default screen: 720x1280. Center=(360,640). Nav bar y=1240
"""

    # ═══════════════════════════════════════════════════════════════
    # CONFIG KEYS — Exhaustive reference
    # ═══════════════════════════════════════════════════════════════
    @mcp.resource("memu://config-keys")
    def config_keys_reference() -> str:
        """Complete reference of all valid VM configuration keys and their descriptions."""
        return """# VM Configuration Keys (for get_vm_config / set_vm_config)

IMPORTANT: Most config changes require the VM to be STOPPED first.
Use stop_vm() before changing, then boot_and_ready() after.

## Hardware
| Key | Description | Values | Notes |
|-----|-------------|--------|-------|
| cpus | CPU cores | 1, 2, 4, 8 | More cores = better performance |
| cpucap | CPU cap percentage | 0-100 | Limits CPU usage on host |
| memory | RAM in MB | 1024, 2048, 4096 | Min 1024, typically 2048+ |

## Display
| Key | Description | Values | Notes |
|-----|-------------|--------|-------|
| is_full_screen | Fullscreen mode | 0/1 | 0=windowed, 1=fullscreen |
| is_hide_toolbar | Hide toolbar | 0/1 | |
| is_customed_resolution | Custom resolution | 0/1 | Must be 1 for custom res |
| resolution_width | Width (pixels) | 720, 1080, 1440 | Common: 720, 1080 |
| resolution_height | Height (pixels) | 1280, 1920, 2560 | Common: 1280, 1920 |
| vbox_dpi | Screen DPI | 160, 240, 320, 480 | 240=hdpi, 480=xxhdpi |
| fps | Frames per second | 0-120 | 0=unlimited, 60=default |
| graphics_render_mode | Renderer | 0=OpenGL, 1=DirectX | USE 0 for screenshots! |
| start_window_mode | Start position | 0=Default, 1=Last, 2=Custom | |
| win_x | Window X | pixels | Position on host screen |
| win_y | Window Y | pixels | Position on host screen |
| win_scaling_percent2 | Window scaling | 50-200 | 100=1:1 |
| disable_resize | Fixed window | 0=stretchable, 1=fixed | |
| geometry | Window geometry | "x y width height" | All-in-one position |
| custom_resolution | Full resolution | "width height dpi" | All-in-one display |

## Device Identity (for fingerprint spoofing)
| Key | Description | Values | Notes |
|-----|-------------|--------|-------|
| name | VM display name | string | Shown in MEmu UI |
| imei | Device IMEI | 15-digit string | Use randomize_vm_device() |
| imsi | SIM IMSI | string | Carrier identity |
| simserial | SIM serial | string | |
| linenum | Phone number | string | e.g. "1234567890" |
| microvirt_vm_brand | Device brand | "samsung", "google", "xiaomi" | |
| microvirt_vm_model | Device model | "SM-G950F", "Pixel 6" | |
| microvirt_vm_manufacturer | Manufacturer | "Samsung", "Google" | |
| macaddress | MAC address | hex string | e.g. "AABBCCDDEEFF" |
| ssid | WiFi network name | string or "auto" | |

## Performance
| Key | Description | Values | Notes |
|-----|-------------|--------|-------|
| turbo_mode | Turbo mode | 0/1 | Faster emulation |
| cache_mode | Cache mode | 0=stable, 1=fast | fast=better perf |
| enable_su | Root access | 0/1 | 1=apps can use sudo |
| enable_audio | Audio | 0/1 | Disable for headless |
| sync_time | Time sync | 0/1 | Sync with host clock |

## GPS
| Key | Description | Values | Notes |
|-----|-------------|--------|-------|
| latitude | GPS latitude | -90.0 to 90.0 | Decimal degrees |
| longitude | GPS longitude | -180.0 to 180.0 | Decimal degrees |
| selected_map | Map provider | 0=Google, 1=Baidu | |

## Input & Layout
| Key | Description | Values | Notes |
|-----|-------------|--------|-------|
| vkeyboard_mode | Virtual keyboard | 0/1 | Show on-screen keyboard |
| phone_layout | Phone layout | 0=Bottom, 1=Right, 2=Toolbar | |

## Shared Folders (Windows <-> VM file sharing)
| Key | Description | Values | Notes |
|-----|-------------|--------|-------|
| picturepath | Shared pictures | Windows path | Shows in VM Gallery |
| musicpath | Shared music | Windows path | Shows in VM Music |
| moviepath | Shared movies | Windows path | Shows in VM Video |
| downloadpath | Shared downloads | Windows path | Shows in VM Downloads |

## Common Configuration Recipes

### Budget Phone Profile
cpus=1, memory=1024, resolution=720x1280, vbox_dpi=240

### Mid-Range Phone Profile
cpus=2, memory=2048, resolution=1080x1920, vbox_dpi=420

### High-End Phone Profile
cpus=4, memory=4096, resolution=1440x2560, vbox_dpi=560

### Tablet Profile
cpus=4, memory=4096, resolution=2560x1600, vbox_dpi=320

### Headless/CI Profile (no display overhead)
enable_audio=0, fps=30, graphics_render_mode=0
"""

    # ═══════════════════════════════════════════════════════════════
    # TOOLS — Complete reference for every tool
    # ═══════════════════════════════════════════════════════════════
    @mcp.resource("memu://tools")
    def tool_reference() -> str:
        """Complete reference of all available MCP-MEmu tools for LLM context."""
        return """# MCP-MEmu Tool Reference (69 Tools)

## Lifecycle (15 tools — manage VM instances)
| Tool | Args | Description | Requires |
|------|------|-------------|----------|
| list_vms | — | List all VMs with index, name, running status, PID | Nothing |
| get_vm_status | vm_index | Returns "running" or "stopped" | Nothing |
| start_vm | vm_index | Boot a VM (async — returns immediately) | VM stopped |
| stop_vm | vm_index | Graceful shutdown | VM running, not protected |
| stop_all_vms | — | Stop all non-protected VMs | — |
| reboot_vm | vm_index | Restart a running VM | VM running, not protected |
| create_vm | vm_version="96" | Create new VM (76=Android 7, 96=Android 9) | Nothing |
| delete_vm | vm_index | Permanently delete VM and disk | VM stopped, not protected |
| clone_vm | vm_index, new_name? | Clone VM to new instance | VM stopped, enough disk |
| rename_vm | vm_index, new_name | Change VM display name | Not protected |
| export_vm | vm_index, output_path | Export to .ova file | VM stopped |
| import_vm | ova_path | Import from .ova file | File exists |
| compress_vm | vm_index | Compress virtual disk image | VM stopped |
| sort_out_all_vms | — | Re-tile all VM windows on screen | — |
| check_task_status | task_id | Check status of an async operation | Valid task_id |

## Configuration (8 tools — read/write VM settings)
| Tool | Args | Description | Requires |
|------|------|-------------|----------|
| get_all_vm_config | vm_index | Returns 16 common config values at once | Nothing |
| get_vm_config | vm_index, key | Read a single config value | Valid key |
| set_vm_config | vm_index, key, value | Write a single config value | VM stopped |
| set_vm_cpu | vm_index, cores | Set CPU cores (1, 2, 4, or 8) | VM stopped |
| set_vm_memory | vm_index, mb | Set RAM in MB (e.g. 2048) | VM stopped |
| set_vm_resolution | vm_index, width, height, dpi | Set display resolution | VM stopped |
| set_vm_gps | vm_index, lat, lng | Set GPS coordinates | Nothing |
| randomize_vm_device | vm_index | Randomize IMEI, MAC, model, brand | VM stopped |

## App Management (7 tools)
| Tool | Args | Description | Requires |
|------|------|-------------|----------|
| list_apps | vm_index | List installed packages with versions | VM running |
| install_apk | vm_index, apk_path | Install APK from host path | VM running, valid path |
| uninstall_app | vm_index, package | Remove app by package name | VM running |
| launch_app | vm_index, package | Start an app | VM running, app installed |
| stop_app | vm_index, package | Force stop an app | VM running |
| clear_app_data | vm_index, package | Wipe app data and cache | VM running |
| create_app_shortcut | vm_index, package | Create desktop shortcut | VM running |

## UI Interaction (14 tools — VM must be RUNNING)
| Tool | Args | Description | Notes |
|------|------|-------------|-------|
| tap | vm_index, x, y | Tap at pixel coordinates | x=0-720, y=0-1280 typically |
| swipe | vm_index, x1, y1, x2, y2, duration_ms=300 | Swipe gesture | duration controls speed |
| long_press | vm_index, x, y, duration_ms=1000 | Long press and hold | 1000ms = 1 second |
| input_text | vm_index, text | Type text into currently focused field | Field must be focused |
| send_key | vm_index, key | Send key event | home/back/menu/volumeup/volumedown |
| press_enter | vm_index | Press Enter key | Same as send_key("enter") |
| press_back | vm_index | Press Back button | Same as send_key("back") |
| press_home | vm_index | Press Home button | Same as send_key("home") |
| shake_device | vm_index | Simulate device shake | For shake-to-undo etc. |
| rotate_screen | vm_index | Toggle portrait/landscape | Toggles each call |
| zoom_in | vm_index | Pinch zoom in gesture | |
| zoom_out | vm_index | Pinch zoom out gesture | |
| scroll_up | vm_index, x=540 | Scroll up (see content above) | x = horizontal position |
| scroll_down | vm_index, x=540 | Scroll down (see content below) | x = horizontal position |

## Screenshot & Capture (3 tools)
| Tool | Args | Description | Notes |
|------|------|-------------|-------|
| take_screenshot | vm_index, save_path | Save PNG to host filesystem | 695KB+ for real content |
| screenshot_base64 | vm_index | Return screenshot as base64 string | Best for AI vision |
| get_screen_size | vm_index | Returns "WIDTHxHEIGHT @ DPI" | e.g. "720x1280 @ 240" |

## Network & Sensors (6 tools)
| Tool | Args | Description | Notes |
|------|------|-------------|-------|
| connect_network | vm_index | Enable internet connectivity | Required for ADB |
| disconnect_network | vm_index | Disable internet | Test offline behavior |
| get_public_ip | vm_index | Get the VM's public IP address | Needs network |
| set_gps_location | vm_index, lat, lng | Spoof GPS coordinates | Works even when stopped |
| set_accelerometer | vm_index, x, y, z | Set accelerometer values | For motion-based apps |
| get_adb_connection_info | vm_index | Get ADB host:port | Usually 127.0.0.1:21503 |

## Shell & Advanced (8 tools)
| Tool | Args | Description | Notes |
|------|------|-------------|-------|
| execute_shell | vm_index, command | Run shell command via execcmd | Validated against blocklist |
| send_adb | vm_index, command | Send raw ADB command | Validated against blocklist |
| get_device_info | vm_index | Get model, Android, CPU ABI, language | Returns structured info |
| get_running_apps | vm_index | List running processes | Shows PID and package |
| pull_file | vm_index, remote_path, local_path | Copy file from VM to host | Needs ADB/WiFi |
| push_file | vm_index, local_path, remote_path | Copy file from host to VM | Needs ADB/WiFi |
| set_clipboard | vm_index, text | Set clipboard text on VM | Uses ADB broadcast |
| get_clipboard | vm_index | Read clipboard text from VM | Uses execcmd broadcast |

## Compound (8 tools — multi-step operations)
| Tool | Args | Description | Notes |
|------|------|-------------|-------|
| wait_for_boot | vm_index, timeout=60 | Poll until sys.boot_completed=1 | Use after start_vm() |
| boot_and_ready | vm_index, timeout=120 | start_vm + wait_for_boot combined | Most common start method |
| fresh_start_app | vm_index, package | stop -> clear data -> relaunch | Clean app state |
| install_and_launch | vm_index, apk_path, package | install_apk + launch_app | Convenience combo |
| clone_and_configure | source_vm, cpu, memory, w, h, dpi | Clone + set all hardware | Source must be stopped |
| batch_install | vm_index, apk_paths | Install multiple APKs | Paths separated by ";" |
| full_vm_snapshot | vm_index, backup_dir | stop -> export .ova -> restart | Full backup |
| run_monkey_test | vm_index, package, events=500 | Random UI stress test | Tests for crashes |

## IMPORTANT REMINDERS
- Commands in execute_shell and send_adb are validated against a security blocklist
- Protected VMs (pre-existing) cannot be deleted, stopped, renamed, or rebooted
- VM must be RUNNING for: shell, screenshot, input, apps, network
- VM must be STOPPED for: CPU, RAM, resolution config changes
- Default resolution: 720x1280 with DPI 240
- screenshot_base64 returns base64 encoded PNG — best for AI vision analysis
- take_screenshot saves to a file path — best for documentation/archiving
"""

    # ═══════════════════════════════════════════════════════════════
    # SECURITY
    # ═══════════════════════════════════════════════════════════════
    @mcp.resource("memu://security")
    def security_info() -> str:
        """Security model and protections built into MCP-MEmu."""
        return """# MCP-MEmu Security Model

## Protected VMs
Pre-existing VMs are snapshotted on first server launch into protected_vms.json.
Destructive operations (delete, stop, rename, reboot) are BLOCKED on protected VMs.
Only VMs created during the MCP session can be destroyed.

## Input Validation
- vm_index must be a non-negative integer (0, 1, 2, ...)
- Shell commands are checked against a dangerous command blocklist:
  rm -rf /, mkfs, dd if=, reboot, shutdown, format, wipe
- Invalid inputs are rejected with clear error messages

## Audit Logging
All destructive operations are timestamped and logged to stderr:
  [AUDIT 2026-03-17 11:00:00] delete_vm vm_index=1
  [AUDIT 2026-03-17 11:00:05] BLOCKED vm_index=0 operation=delete_vm (protected VM)
  [AUDIT 2026-03-17 11:00:10] execute_shell vm_index=0 cmd=ls /sdcard

## Transport Security
This server uses stdio transport (local only — no network exposure).
For remote deployment, implement OAuth 2.1 with PKCE per the MCP specification.
"""
