"""App Management tools — install, uninstall, launch, stop, list apps, clear data."""

from pymemuc import PyMemucError

from mcp_memu.utils.memuc_instance import memuc, logger


def register_tools(mcp):
    """Register all app management tools with the MCP server."""

    @mcp.tool()
    def list_apps(vm_index: int) -> str:
        """List all installed app packages on a VM. VM must be running.

        Args:
            vm_index: VM index (0, 1, 2...). The VM must be running.

        Returns: List of package names (e.g. com.android.settings, com.android.chrome).

        Example output:
            Apps on VM 0 (25 total):
              com.android.settings
              com.android.chrome
              ...
        """
        try:
            apps = memuc.get_app_info_list_vm(vm_index=vm_index)
            if not apps:
                return f"No apps found on VM {vm_index}"
            return f"Apps on VM {vm_index} ({len(apps)} total):\n" + "\n".join(f"  {a}" for a in apps)
        except PyMemucError as e:
            return f"Error listing apps: {e}"

    @mcp.tool()
    def install_apk(vm_index: int, apk_path: str, create_shortcut: bool = False) -> str:
        """Install an APK file into a VM. VM must be running.

        Args:
            vm_index: VM index (0, 1, 2...).
            apk_path: Full local file path to the .apk file (e.g. 'C:\\\\Downloads\\\\app.apk').
            create_shortcut: If true, creates a desktop shortcut after install.

        Returns: Success or error message.
        """
        try:
            memuc.install_apk_vm(apk_path, vm_index=vm_index, create_shortcut=create_shortcut)
            return f"APK '{apk_path}' installed on VM {vm_index}"
        except PyMemucError as e:
            return f"Error installing APK: {e}"

    @mcp.tool()
    def uninstall_app(vm_index: int, package: str) -> str:
        """Uninstall an app from a VM by its package name.

        Args:
            vm_index: VM index (0, 1, 2...).
            package: Android package name (e.g. 'com.example.app'). Use list_apps to find package names.

        Returns: Success or error message.
        """
        try:
            memuc.uninstall_apk_vm(package, vm_index=vm_index)
            return f"Package '{package}' uninstalled from VM {vm_index}"
        except PyMemucError as e:
            return f"Error uninstalling app: {e}"

    @mcp.tool()
    def launch_app(vm_index: int, package: str) -> str:
        """Launch an app on a VM by its package name. VM must be running.

        Args:
            vm_index: VM index (0, 1, 2...).
            package: Android package name (e.g. 'com.android.settings', 'com.android.chrome').

        Returns: Success or error message.
        """
        try:
            memuc.start_app_vm(package, vm_index=vm_index)
            return f"App '{package}' launched on VM {vm_index}"
        except PyMemucError as e:
            return f"Error launching app: {e}"

    @mcp.tool()
    def stop_app(vm_index: int, package: str) -> str:
        """Force stop a running app on a VM by its package name.

        Args:
            vm_index: VM index (0, 1, 2...).
            package: Android package name (e.g. 'com.android.chrome').

        Returns: Success or error message.
        """
        try:
            memuc.stop_app_vm(package, vm_index=vm_index)
            return f"App '{package}' stopped on VM {vm_index}"
        except PyMemucError as e:
            return f"Error stopping app: {e}"

    @mcp.tool()
    def clear_app_data(vm_index: int, package: str) -> str:
        """Clear app data and cache via ADB shell command. VM must be running.

        Args:
            vm_index: VM index (0, 1, 2...).
            package: Android package name (e.g. 'com.android.chrome').

        Returns: "Success" or error message.
        """
        try:
            rc, output = memuc.execute_command_vm(f"pm clear {package}", vm_index=vm_index)
            return f"Clear data for '{package}' on VM {vm_index}: {output.strip()}"
        except PyMemucError as e:
            return f"Error clearing app data: {e}"

    @mcp.tool()
    def create_app_shortcut(vm_index: int, package: str) -> str:
        """Create a desktop shortcut for an app on a VM.

        Args:
            vm_index: VM index (0, 1, 2...).
            package: Android package name (e.g. 'com.android.chrome').

        Returns: Success or error message.
        """
        try:
            memuc.create_app_shortcut_vm(package, vm_index=vm_index)
            return f"Shortcut created for '{package}' on VM {vm_index}"
        except PyMemucError as e:
            return f"Error creating shortcut: {e}"
