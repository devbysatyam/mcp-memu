"""App Management tools — install, uninstall, launch, stop, list apps, clear data."""

from pymemuc import PyMemucError

from utils.memuc_instance import memuc, logger


def register_tools(mcp):
    """Register all app management tools with the MCP server."""

    @mcp.tool()
    def list_apps(vm_index: int) -> str:
        """List all installed app packages on a VM."""
        try:
            apps = memuc.get_app_info_list_vm(vm_index=vm_index)
            if not apps:
                return f"No apps found on VM {vm_index}"
            return f"Apps on VM {vm_index} ({len(apps)} total):\n" + "\n".join(f"  {a}" for a in apps)
        except PyMemucError as e:
            return f"Error listing apps: {e}"

    @mcp.tool()
    def install_apk(vm_index: int, apk_path: str, create_shortcut: bool = False) -> str:
        """Install an APK file into a VM. Provide the full local path to the .apk file."""
        try:
            memuc.install_apk_vm(apk_path, vm_index=vm_index, create_shortcut=create_shortcut)
            return f"APK '{apk_path}' installed on VM {vm_index}"
        except PyMemucError as e:
            return f"Error installing APK: {e}"

    @mcp.tool()
    def uninstall_app(vm_index: int, package: str) -> str:
        """Uninstall an app from a VM by its package name (e.g. 'com.example.app')."""
        try:
            memuc.uninstall_apk_vm(package, vm_index=vm_index)
            return f"Package '{package}' uninstalled from VM {vm_index}"
        except PyMemucError as e:
            return f"Error uninstalling app: {e}"

    @mcp.tool()
    def launch_app(vm_index: int, package: str) -> str:
        """Launch an app on a VM by its package name (e.g. 'com.android.settings')."""
        try:
            memuc.start_app_vm(package, vm_index=vm_index)
            return f"App '{package}' launched on VM {vm_index}"
        except PyMemucError as e:
            return f"Error launching app: {e}"

    @mcp.tool()
    def stop_app(vm_index: int, package: str) -> str:
        """Force stop a running app on a VM by its package name."""
        try:
            memuc.stop_app_vm(package, vm_index=vm_index)
            return f"App '{package}' stopped on VM {vm_index}"
        except PyMemucError as e:
            return f"Error stopping app: {e}"

    @mcp.tool()
    def clear_app_data(vm_index: int, package: str) -> str:
        """Clear app data and cache via ADB shell command."""
        try:
            rc, output = memuc.execute_command_vm(f"pm clear {package}", vm_index=vm_index)
            return f"Clear data for '{package}' on VM {vm_index}: {output.strip()}"
        except PyMemucError as e:
            return f"Error clearing app data: {e}"

    @mcp.tool()
    def create_app_shortcut(vm_index: int, package: str) -> str:
        """Create a desktop shortcut for an app on a VM."""
        try:
            memuc.create_app_shortcut_vm(package, vm_index=vm_index)
            return f"Shortcut created for '{package}' on VM {vm_index}"
        except PyMemucError as e:
            return f"Error creating shortcut: {e}"

