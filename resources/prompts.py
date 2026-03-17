"""MCP Prompts — reusable prompt templates for common automation workflows.

These prompts give LLMs structured, step-by-step instructions for complex
multi-tool operations, reducing hallucination and ensuring correct tool usage.
"""


def register_prompts(mcp):
    """Register all MCP prompts with the server."""

    @mcp.prompt()
    def automate_app_testing(package: str, vm_index: int = 0) -> str:
        """Step-by-step prompt for automated app testing on a MEmu VM.

        Args:
            package: Android package name (e.g. com.example.app)
            vm_index: VM index to test on (default 0)
        """
        return f"""You are automating app testing on MEmu Android Emulator VM {vm_index}.
Target app: {package}

Follow these steps IN ORDER. Do NOT skip steps. Do NOT guess coordinates — always take a screenshot first.

## Step 1: Ensure VM is running
Call: get_vm_status(vm_index={vm_index})
- If stopped → call boot_and_ready(vm_index={vm_index})
- If running → proceed

## Step 2: Take initial screenshot
Call: screenshot_base64(vm_index={vm_index})
- Analyze the screen to understand current state
- Note the resolution for coordinate calculations

## Step 3: Launch the app
Call: launch_app(vm_index={vm_index}, package="{package}")
- Wait 3 seconds for app to load
- Take another screenshot to verify app launched

## Step 4: Interact with the app
Based on what you see in the screenshot:
- Use tap(vm_index={vm_index}, x=..., y=...) for buttons
- Use input_text(vm_index={vm_index}, text="...") for text fields
- Use swipe(vm_index={vm_index}, ...) for scrolling
- Use press_back(vm_index={vm_index}) to navigate back

## Step 5: Capture results
Call: take_screenshot(vm_index={vm_index}, save_path="C:\\\\test_result.png")

## CRITICAL RULES:
- ALWAYS screenshot before tapping — never guess coordinates
- Default resolution is 720x1280. Center = (360, 640)
- Navigation bar is at y=1240
- Status bar is at y=0-50
- If a tool returns an error, report it — do NOT retry silently
- If screenshot is blank/small (<10KB), the VM may use DirectX rendering
"""

    @mcp.prompt()
    def setup_new_vm(vm_version: str = "96", cpu: int = 2, memory: int = 2048) -> str:
        """Step-by-step prompt for creating and configuring a new MEmu VM.

        Args:
            vm_version: Android version (76=Android 7, 96=Android 9)
            cpu: Number of CPU cores
            memory: RAM in MB
        """
        return f"""You are creating and configuring a new MEmu Android VM.

## Step 1: Create the VM
Call: create_vm(vm_version="{vm_version}")
- Note the returned vm_index — you'll need it for all subsequent steps
- The new VM is NOT protected, so you can freely modify/delete it

## Step 2: Configure hardware (VM must be STOPPED for this)
Call these in order:
1. set_vm_cpu(vm_index=NEW_INDEX, cores={cpu})
2. set_vm_memory(vm_index=NEW_INDEX, mb={memory})
3. set_vm_resolution(vm_index=NEW_INDEX, width=720, height=1280, dpi=240)

## Step 3: Boot the VM
Call: boot_and_ready(vm_index=NEW_INDEX, timeout=120)
- This starts the VM and waits until Android is fully booted
- If it times out, the VM may still be booting — try wait_for_boot()

## Step 4: Verify
Call: get_device_info(vm_index=NEW_INDEX)
- Confirm model, Android version, and ABI

## Step 5: Optional — Randomize device fingerprint
Call: randomize_vm_device(vm_index=NEW_INDEX)
- Changes IMEI, MAC, model, brand — makes VM look like a different device

## IMPORTANT RULES:
- Config changes (CPU, RAM, resolution) require the VM to be STOPPED
- The VM you just created is NOT protected — you can delete it later
- Pre-existing VMs (index 0 typically) ARE protected
- clone_vm requires the source VM to be stopped and sufficient disk space (~2-4GB)
"""

    @mcp.prompt()
    def ui_automation_guide(vm_index: int = 0) -> str:
        """Detailed guide for UI automation with correct coordinate handling.

        Args:
            vm_index: VM index to automate
        """
        return f"""You are performing UI automation on MEmu VM {vm_index}.

## CRITICAL: How to determine tap coordinates

1. ALWAYS call screenshot_base64(vm_index={vm_index}) FIRST
2. Analyze the screenshot to identify UI elements
3. Estimate coordinates based on the element's position

## Default Screen Layout (720x1280)

```
┌──────────────────────────┐ y=0
│      Status Bar (50px)    │
├──────────────────────────┤ y=50
│                          │
│                          │
│      App Content         │
│      Center: (360, 640)  │
│                          │
│                          │
├──────────────────────────┤ y=1200
│   ◁    ○    □            │ Navigation Bar
│  Back Home Recent        │
│ (120,1240)(360,1240)     │
│           (600,1240)     │
└──────────────────────────┘ y=1280
```

## Available Input Tools

| Action | Tool | Example |
|--------|------|---------|
| Tap button | tap(vm_index, x, y) | tap({vm_index}, 360, 640) |
| Swipe/scroll | swipe(vm_index, x1, y1, x2, y2, ms) | swipe({vm_index}, 360, 900, 360, 300, 300) |
| Type text | input_text(vm_index, text) | input_text({vm_index}, "hello") |
| Press key | send_key(vm_index, key) | send_key({vm_index}, "home") |
| Scroll up | scroll_up(vm_index) | scroll_up({vm_index}) |
| Scroll down | scroll_down(vm_index) | scroll_down({vm_index}) |
| Long press | long_press(vm_index, x, y, ms) | long_press({vm_index}, 360, 500, 1500) |

## Swipe Direction Guide
- Scroll DOWN (see content below): swipe from bottom to top → swipe(x, 1200, x, 400)
- Scroll UP (see content above): swipe from top to bottom → swipe(x, 400, x, 1200)
- Swipe LEFT (next page): swipe from right to left → swipe(600, y, 100, y)
- Swipe RIGHT (prev page): swipe from left to right → swipe(100, y, 600, y)

## ANTI-HALLUCINATION RULES:
1. NEVER guess coordinates without a screenshot
2. NEVER assume an app is open — verify with screenshot
3. NEVER assume a tap worked — take a screenshot after to verify
4. If you don't see the expected result, REPORT it. Don't make up a success message.
5. Coordinates are ALWAYS (x, y) where x=horizontal, y=vertical from TOP-LEFT
6. The VM resolution may NOT be 720x1280 — call get_screen_size() if unsure
"""

    @mcp.prompt()
    def batch_device_farm(count: int = 3) -> str:
        """Prompt for setting up multiple VMs as a device farm.

        Args:
            count: Number of VMs to create
        """
        return f"""You are setting up a device farm of {count} MEmu Android VMs.

## Step 1: Check existing VMs
Call: list_vms()
- Note which VMs already exist and are protected
- Protected VMs CANNOT be deleted/stopped/renamed

## Step 2: Create VMs
For each of {count} VMs:
1. Call: create_vm(vm_version="96")
2. Note each new vm_index

## Step 3: Configure each VM differently
For VM diversity, configure each with different specs:
- VM A: set_vm_cpu(cores=2), set_vm_memory(mb=2048), set_vm_resolution(720, 1280, 240)
- VM B: set_vm_cpu(cores=4), set_vm_memory(mb=4096), set_vm_resolution(1080, 1920, 480)
- VM C: set_vm_cpu(cores=2), set_vm_memory(mb=3072), set_vm_resolution(1080, 2340, 440)

For each VM, call randomize_vm_device() to give unique fingerprints.

## Step 4: Boot all VMs
For each VM:
1. Call: boot_and_ready(vm_index=X, timeout=120)

## Step 5: Verify all VMs
For each VM:
1. Call: get_device_info(vm_index=X)
2. Call: screenshot_base64(vm_index=X) to verify screen

## Step 6: Install apps on all VMs
Use: batch_install(vm_index=X, apk_paths="path1.apk;path2.apk")

## IMPORTANT:
- Each VM requires 2-4GB of disk space
- Creating too many VMs on low disk space will fail
- Use sort_out_all_vms() to arrange windows
- When done testing, delete non-protected VMs to free space
"""

    @mcp.prompt()
    def debug_vm_issues(vm_index: int = 0) -> str:
        """Diagnostic prompt for troubleshooting VM issues.

        Args:
            vm_index: VM to diagnose
        """
        return f"""You are diagnosing issues with MEmu VM {vm_index}.

## Step 1: Check VM status
Call: get_vm_status(vm_index={vm_index})
- If stopped, ask user if they want to start it
- If running, proceed with diagnostics

## Step 2: Check ADB connectivity
Call: get_adb_connection_info(vm_index={vm_index})
- Should return host:port (usually 127.0.0.1:21503)
- If "not available", the VM may not be fully booted

## Step 3: Check device info
Call: get_device_info(vm_index={vm_index})
- Verify Model, Android Version, CPU ABI values
- If any show "N/A", the VM might be in a bad state

## Step 4: Test screenshot
Call: screenshot_base64(vm_index={vm_index})
- If blank/black → likely DirectX rendering issue
  - Fix: set_vm_config(vm_index={vm_index}, key="graphics_render_mode", value="0") then reboot
- If error → ADB may be disconnected
  - Fix: connect_network(vm_index={vm_index}), then retry

## Step 5: Check network
Call: connect_network(vm_index={vm_index})
Call: get_public_ip(vm_index={vm_index})
- If no IP → network stack may be down

## Step 6: Check configuration
Call: get_all_vm_config(vm_index={vm_index})
- Verify CPU, memory, resolution values are reasonable

## Common Issues & Fixes:
| Problem | Cause | Fix |
|---------|-------|-----|
| Blank screenshot | DirectX renderer | set graphics_render_mode=0, reboot |
| ADB offline | WiFi disabled | connect_network() |
| Tool hangs | ADB daemon crashed | Reboot VM: reboot_vm() |
| Clone fails | Low disk space | Free space (need 2-4GB per clone) |
| Config change no effect | VM was running | Stop VM first, then configure |
| App won't launch | Not installed | install_apk() first |
"""

    @mcp.prompt()
    def gps_spoofing_guide(vm_index: int = 0) -> str:
        """Guide for GPS location spoofing with popular coordinate presets.

        Args:
            vm_index: VM to set GPS on
        """
        return f"""You are setting up GPS spoofing on MEmu VM {vm_index}.

## How to Set GPS
Call: set_gps_location(vm_index={vm_index}, lat=LATITUDE, lng=LONGITUDE)

## Popular Location Presets
| City | Latitude | Longitude |
|------|----------|-----------|
| San Francisco | 37.7749 | -122.4194 |
| New York | 40.7128 | -74.0060 |
| London | 51.5074 | -0.1278 |
| Tokyo | 35.6762 | 139.6503 |
| Paris | 48.8566 | 2.3522 |
| Sydney | -33.8688 | 151.2093 |
| Mumbai | 19.0760 | 72.8777 |
| Dubai | 25.2048 | 55.2708 |
| Singapore | 1.3521 | 103.8198 |
| Berlin | 52.5200 | 13.4050 |

## Verify GPS was set
Call: get_vm_config(vm_index={vm_index}, key="latitude")
Call: get_vm_config(vm_index={vm_index}, key="longitude")

## IMPORTANT:
- GPS is set via MEMUC (not ADB), so it works even when VM is stopped
- Some apps cache GPS — you may need to restart the app after changing
- Latitude ranges from -90 to 90, Longitude from -180 to 180
- The set_gps_location tool takes (lat, lng) — latitude first, longitude second
"""

    @mcp.prompt()
    def file_transfer_guide(vm_index: int = 0) -> str:
        """Guide for transferring files between host and VM.

        Args:
            vm_index: VM to transfer files to/from
        """
        return f"""You are transferring files to/from MEmu VM {vm_index}.

## Push file (Host → VM)
Call: push_file(vm_index={vm_index}, local_path="C:\\\\path\\\\to\\\\file.txt", remote_path="/sdcard/file.txt")

## Pull file (VM → Host)
Call: pull_file(vm_index={vm_index}, remote_path="/sdcard/file.txt", local_path="C:\\\\path\\\\to\\\\file.txt")

## Common VM Paths
| Path | Description |
|------|-------------|
| /sdcard/ | Main storage (equivalent to internal storage) |
| /sdcard/Download/ | Downloads folder (shared with Windows) |
| /sdcard/Pictures/ | Pictures (shared with Windows) |
| /sdcard/DCIM/ | Camera photos |
| /data/data/PACKAGE/ | App private data (requires root) |
| /system/ | System files (read-only usually) |

## List files on VM
Call: execute_shell(vm_index={vm_index}, command="ls -la /sdcard/")

## Check file size
Call: execute_shell(vm_index={vm_index}, command="stat /sdcard/file.txt")

## Shared Folders (no ADB required)
MEmu maps Windows folders to the VM:
- Pictures: get_vm_config(vm_index={vm_index}, key="picturepath")
- Music: get_vm_config(vm_index={vm_index}, key="musicpath")
- Movies: get_vm_config(vm_index={vm_index}, key="moviepath")
- Downloads: get_vm_config(vm_index={vm_index}, key="downloadpath")

Files placed in these Windows folders appear instantly in the VM.

## IMPORTANT:
- VM must be RUNNING for push/pull to work
- Paths with spaces need quoting in shell commands
- ADB requires WiFi to be enabled in the VM
- Max file size depends on available VM storage
"""
