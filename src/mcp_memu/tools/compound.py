"""Compound / Smart tools — high-level operations that combine multiple low-level actions."""

import time

from pymemuc import PyMemucError

from mcp_memu.utils.memuc_instance import memuc, logger, assert_not_protected


def register_tools(mcp):
    """Register all compound tools with the MCP server."""

    @mcp.tool()
    def wait_for_boot(vm_index: int, timeout: int = 60) -> str:
        """Wait until Android has fully booted in a VM. Polls every 2 seconds.
        Use this after start_vm to ensure the VM is ready for interaction.

        Args:
            vm_index: VM index (0, 1, 2...).
            timeout: Maximum seconds to wait (default 60).

        Returns: "boot completed in Xs" or "boot timed out after Xs".
        """
        start = time.time()
        while time.time() - start < timeout:
            try:
                rc, result = memuc.execute_command_vm(
                    "getprop sys.boot_completed", vm_index=vm_index
                )
                if result.strip() == "1":
                    elapsed = int(time.time() - start)
                    return f"VM {vm_index} boot completed in {elapsed}s"
            except PyMemucError:
                pass
            time.sleep(2)
        return f"VM {vm_index} boot timed out after {timeout}s"

    @mcp.tool()
    def boot_and_ready(vm_index: int, timeout: int = 120) -> str:
        """Start a VM and wait until Android is fully booted and ready.
        Combines start_vm + boot polling into a single operation.

        Args:
            vm_index: VM index (0, 1, 2...).
            timeout: Maximum seconds to wait for boot after starting (default 120).

        Returns: "started and ready in Xs" or timeout message.
        """
        try:
            memuc.start_vm(vm_index=vm_index)
        except PyMemucError as e:
            return f"Error starting VM {vm_index}: {e}"

        start = time.time()
        while time.time() - start < timeout:
            try:
                rc, result = memuc.execute_command_vm(
                    "getprop sys.boot_completed", vm_index=vm_index
                )
                if result.strip() == "1":
                    elapsed = int(time.time() - start)
                    return f"VM {vm_index} started and ready in {elapsed}s"
            except PyMemucError:
                pass
            time.sleep(2)
        return f"VM {vm_index} started but boot timed out after {timeout}s"

    @mcp.tool()
    def fresh_start_app(vm_index: int, package: str) -> str:
        """Clean-slate start: force stop app → clear its data/cache → relaunch it.
        Useful for testing apps from a fresh state. VM must be running.

        Args:
            vm_index: VM index (0, 1, 2...).
            package: Android package name (e.g. 'com.android.chrome').

        Returns: Step-by-step result like "stopped → data cleared → launched".
        """
        results = []
        try:
            memuc.stop_app_vm(package, vm_index=vm_index)
            results.append("stopped")
        except PyMemucError:
            results.append("stop skipped")

        try:
            memuc.execute_command_vm(f"pm clear {package}", vm_index=vm_index)
            results.append("data cleared")
        except PyMemucError:
            results.append("clear failed")

        try:
            memuc.start_app_vm(package, vm_index=vm_index)
            results.append("launched")
        except PyMemucError as e:
            results.append(f"launch failed: {e}")

        return f"fresh_start_app '{package}' on VM {vm_index}: {' → '.join(results)}"

    @mcp.tool()
    def install_and_launch(vm_index: int, apk_path: str, package: str) -> str:
        """Install an APK and immediately launch the app. VM must be running.

        Args:
            vm_index: VM index (0, 1, 2...).
            apk_path: Full local path to the .apk file (e.g. 'C:\\\\Downloads\\\\app.apk').
            package: Android package name of the app (e.g. 'com.example.myapp').
                     This must match the package inside the APK.

        Returns: Success or error message.
        """
        try:
            memuc.install_apk_vm(apk_path, vm_index=vm_index)
        except PyMemucError as e:
            return f"Install failed: {e}"

        try:
            memuc.start_app_vm(package, vm_index=vm_index)
            return f"Installed '{apk_path}' and launched '{package}' on VM {vm_index}"
        except PyMemucError as e:
            return f"Installed but launch failed: {e}"

    @mcp.tool()
    def clone_and_configure(
        source_vm: int, cpu: int = 2, memory: int = 2048,
        width: int = 720, height: int = 1280, dpi: int = 240
    ) -> str:
        """Clone a VM and configure the clone with custom hardware settings.

        Args:
            source_vm: Index of the VM to clone from.
            cpu: Number of CPU cores for the clone (default 2). Valid: 1, 2, 4, 8.
            memory: RAM in MB for the clone (default 2048).
            width: Screen width in pixels (default 720).
            height: Screen height in pixels (default 1280).
            dpi: Screen DPI (default 240).

        Returns: New VM index and configuration summary.
        """
        try:
            result = memuc.clone_vm(vm_index=source_vm)
            vms = memuc.list_vm_info()
            new_index = max(vm["index"] for vm in vms)
        except PyMemucError as e:
            return f"Error cloning VM: {e}"

        configs = [
            ("cpus", str(cpu)),
            ("memory", str(memory)),
            ("is_customed_resolution", "1"),
            ("resolution_width", str(width)),
            ("resolution_height", str(height)),
            ("vbox_dpi", str(dpi)),
        ]
        for key, value in configs:
            try:
                memuc.set_configuration_vm(key, value, vm_index=new_index)
            except PyMemucError as e:
                logger.warning("Config %s=%s failed on VM %d: %s", key, value, new_index, e)

        return (
            f"Cloned VM {source_vm} → VM {new_index} with "
            f"{cpu} CPUs, {memory}MB RAM, {width}x{height}@{dpi}dpi"
        )

    @mcp.tool()
    def batch_install(vm_index: int, apk_paths: str) -> str:
        """Install multiple APKs into a VM in one operation. VM must be running.

        Args:
            vm_index: VM index (0, 1, 2...).
            apk_paths: APK file paths separated by semicolons (;).
                       Example: 'C:\\\\apks\\\\app1.apk;C:\\\\apks\\\\app2.apk'

        Returns: Per-file success/failure report.
        """
        paths = [p.strip() for p in apk_paths.split(";") if p.strip()]
        results = []
        for path in paths:
            try:
                memuc.install_apk_vm(path, vm_index=vm_index)
                results.append(f"✓ {path}")
            except PyMemucError as e:
                results.append(f"✗ {path}: {e}")
        return f"Batch install on VM {vm_index}:\n" + "\n".join(results)

    @mcp.tool()
    def full_vm_snapshot(vm_index: int, backup_dir: str) -> str:
        """Create a full snapshot: stop VM → export to timestamped .ova → restart VM.
        Cannot snapshot protected VMs.

        Args:
            vm_index: VM index. Must NOT be a protected VM.
            backup_dir: Local directory to store the .ova backup file
                        (e.g. 'C:\\\\backups\\\\memu').

        Returns: Path to the exported .ova file.
        """
        import os
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        ova_path = os.path.join(backup_dir, f"vm{vm_index}_backup_{timestamp}.ova")

        try:
            assert_not_protected(vm_index, "full_vm_snapshot")
        except RuntimeError as e:
            return str(e)

        was_running = False
        try:
            was_running = memuc.vm_is_running(vm_index=vm_index)
            if was_running:
                memuc.stop_vm(vm_index=vm_index)
        except PyMemucError as e:
            return f"Error stopping VM for snapshot: {e}"

        try:
            os.makedirs(backup_dir, exist_ok=True)
            memuc.export_vm(vm_index=vm_index, file_name=ova_path)
        except PyMemucError as e:
            return f"Error exporting VM: {e}"

        if was_running:
            try:
                memuc.start_vm(vm_index=vm_index)
            except PyMemucError:
                pass

        return f"VM {vm_index} snapshot saved to {ova_path}"

    @mcp.tool()
    def run_monkey_test(vm_index: int, package: str, events: int = 500) -> str:
        """Run Android's monkey stress test on an app. Generates random UI events
        (taps, swipes, key presses) to test app stability. VM must be running.

        Args:
            vm_index: VM index (0, 1, 2...).
            package: Android package name to test (e.g. 'com.example.myapp').
            events: Number of random events to generate (default 500).

        Returns: Monkey test output with event count and any crashes detected.
        """
        try:
            memuc.start_app_vm(package, vm_index=vm_index)
            time.sleep(2)
            rc, output = memuc.execute_command_vm(
                f"monkey -p {package} -v {events}", vm_index=vm_index
            )
            return f"Monkey test on '{package}' ({events} events) on VM {vm_index}:\n{output.strip()}"
        except PyMemucError as e:
            return f"Error running monkey test: {e}"
