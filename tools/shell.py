"""Shell & Advanced tools — execute shell, ADB, device info, running apps, file transfer, clipboard."""

from pymemuc import PyMemucError

from utils.memuc_instance import memuc, logger, validate_vm_index, validate_command, audit_log
from utils.adb_helpers import adb_pull, adb_push


def _clean_adb_output(output: str) -> str:
    """Remove 'already connected to ...' prefix from ADB output."""
    if not output:
        return ""
    lines = output.strip().split("\n")
    cleaned = [l for l in lines if not l.startswith("already connected")]
    return "\n".join(cleaned).strip()


def register_tools(mcp):
    """Register all shell and advanced tools with the MCP server."""

    @mcp.tool()
    def execute_shell(vm_index: int, command: str) -> str:
        """Run an arbitrary Android shell command on a VM. VM must be running.

        Uses memuc execcmd internally. For complex commands, prefer send_adb.

        Args:
            vm_index: VM index (0, 1, 2...). Use list_vms to find indices.
            command: Shell command to execute. Examples:
                - 'getprop ro.product.model' — get device model name
                - 'pm list packages' — list all installed packages
                - 'dumpsys battery' — get battery info
                - 'ls /sdcard/' — list files on SD card

        Returns: Command output prefixed with return code [RC=0] for success.
        """
        try:
            validate_vm_index(vm_index)
            validate_command(command)
            audit_log("execute_shell", vm_index, f"cmd={command[:80]}")
            rc, output = memuc.memuc_run(["execcmd", "-i", str(vm_index), command])
            clean = output.strip() if output else ""
            return f"[RC={rc}] {clean}" if clean else f"[RC={rc}] (no output)"
        except ValueError as e:
            return str(e)
        except PyMemucError as e:
            return f"Error executing shell command: {e}"
        except Exception as e:
            return f"Error: {e}"

    @mcp.tool()
    def send_adb(vm_index: int, command: str) -> str:
        """Send a raw ADB command to a VM. VM must be running.

        Args:
            vm_index: VM index (0, 1, 2...). Use list_vms to find indices.
            command: ADB command (without 'adb' prefix). Examples:
                - 'shell dumpsys battery' — battery status
                - 'shell dumpsys wifi' — WiFi info
                - 'shell getprop ro.product.model' — device model
                - 'shell pm list packages -3' — third-party packages only

        Returns: Command output string.
        """
        try:
            validate_vm_index(vm_index)
            validate_command(command)
            audit_log("send_adb", vm_index, f"cmd={command[:80]}")
            output = memuc.send_adb_command_vm(command, vm_index=vm_index)
            result = _clean_adb_output(output)
            return result if result else "(no output)"
        except ValueError as e:
            return str(e)
        except PyMemucError as e:
            return f"Error sending ADB command: {e}"
        except Exception as e:
            return f"Error: {e}"

    @mcp.tool()
    def get_device_info(vm_index: int) -> str:
        """Collect device info: model, Android version, CPU ABI, and language. VM must be running.

        Args:
            vm_index: VM index (0, 1, 2...).

        Returns: Formatted device info with model, Android version, CPU, and language.

        Example output:
            VM 0 Device Info:
              Model: ASUS_I005DA
              Android Version: 9
              CPU ABI: x86_64
              Language: en
        """
        try:
            info = {}
            for prop, label in [
                ("ro.product.model", "Model"),
                ("ro.build.version.release", "Android Version"),
                ("ro.product.cpu.abi", "CPU ABI"),
                ("persist.sys.language", "Language"),
            ]:
                try:
                    # Use memuc_run with execcmd for clean output
                    rc, output = memuc.memuc_run(
                        ["execcmd", "-i", str(vm_index), f"getprop {prop}"]
                    )
                    val = output.strip() if output else ""
                    info[label] = val if val else "N/A"
                except Exception:
                    info[label] = "N/A"
            lines = [f"  {k}: {v}" for k, v in info.items()]
            return f"VM {vm_index} Device Info:\n" + "\n".join(lines)
        except PyMemucError as e:
            return f"Error getting device info: {e}"

    @mcp.tool()
    def get_running_apps(vm_index: int) -> str:
        """List currently running app processes on a VM. VM must be running.

        Args:
            vm_index: VM index (0, 1, 2...).

        Returns: List of running activities/processes.
        """
        try:
            output = memuc.send_adb_command_vm(
                "shell dumpsys activity activities", vm_index=vm_index
            )
            clean = _clean_adb_output(output)
            # Extract just the task/activity lines
            relevant = []
            for line in clean.split("\n"):
                if "TaskRecord" in line or "Run " in line or "ActivityRecord" in line:
                    relevant.append(line.strip())
            if relevant:
                return f"Running apps on VM {vm_index}:\n" + "\n".join(relevant[:30])
            # Fallback: just list running processes
            output2 = memuc.send_adb_command_vm("shell ps", vm_index=vm_index)
            clean2 = _clean_adb_output(output2)
            return f"Processes on VM {vm_index}:\n{clean2[:2000]}"
        except PyMemucError as e:
            return f"Error getting running apps: {e}"

    @mcp.tool()
    def pull_file(vm_index: int, remote_path: str, local_path: str) -> str:
        """Pull (download) a file from the VM to the local host via ADB. VM must be running.

        Args:
            vm_index: VM index (0, 1, 2...).
            remote_path: File path on the VM (e.g. '/sdcard/photo.jpg').
            local_path: Local destination path (e.g. 'C:\\\\downloads\\\\photo.jpg').

        Returns: Success or error message.
        """
        return adb_pull(vm_index, remote_path, local_path)

    @mcp.tool()
    def push_file(vm_index: int, local_path: str, remote_path: str) -> str:
        """Push (upload) a file from the local host to the VM via ADB. VM must be running.

        Args:
            vm_index: VM index (0, 1, 2...).
            local_path: Local file path (e.g. 'C:\\\\files\\\\app.apk').
            remote_path: Destination on VM (e.g. '/sdcard/app.apk').

        Returns: Success or error message.
        """
        return adb_push(vm_index, local_path, remote_path)

    @mcp.tool()
    def set_clipboard(vm_index: int, text: str) -> str:
        """Set the Android clipboard content on a VM. VM must be running.

        Args:
            vm_index: VM index (0, 1, 2...).
            text: Text to copy to clipboard.

        Returns: Confirmation message.
        """
        try:
            memuc.send_adb_command_vm(
                f"shell am broadcast -a clipper.set -e text '{text}'",
                vm_index=vm_index
            )
            return f"Clipboard set on VM {vm_index}"
        except PyMemucError as e:
            return f"Error setting clipboard: {e}"

    @mcp.tool()
    def get_clipboard(vm_index: int) -> str:
        """Read the Android clipboard content from a VM. VM must be running.

        Args:
            vm_index: VM index (0, 1, 2...).

        Returns: Current clipboard content.
        """
        try:
            # Use memuc_run with execcmd (avoid raw adb shell to prevent hangs)
            rc, output = memuc.memuc_run(
                ["execcmd", "-i", str(vm_index), "am broadcast -a clipper.get"], 
                timeout=10
            )
            result = _clean_adb_output(output) if output else ""
            if "TimeoutExpired" in result or not result:
                return f"VM {vm_index} clipboard: (empty or could not read)"
            return f"VM {vm_index} clipboard: {result}"
        except Exception as e:
            return f"Error reading clipboard: {e}"
