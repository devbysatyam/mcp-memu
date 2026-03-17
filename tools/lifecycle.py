"""VM Lifecycle tools — list, start, stop, reboot, create, delete, clone, rename, export, import."""

from pymemuc import PyMemucError

from utils.memuc_instance import memuc, logger, assert_not_protected, is_protected, get_protected_vms, audit_log, validate_vm_index


def register_tools(mcp):
    """Register all lifecycle tools with the MCP server."""

    @mcp.tool()
    def list_vms() -> str:
        """List all MEmu VM instances with their index, name, running status, and PID."""
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
                    f"  Index: {vm['index']} | Name: {vm['title']} | "
                    f"Status: {status} | PID: {vm['pid']}{tag}"
                )
            return "VMs:\n" + "\n".join(lines)
        except PyMemucError as e:
            return f"Error listing VMs: {e}"

    @mcp.tool()
    def get_vm_status(vm_index: int) -> str:
        """Check whether a specific VM is running or stopped."""
        try:
            running = memuc.vm_is_running(vm_index=vm_index)
            return f"VM {vm_index} is {'running' if running else 'stopped'}"
        except PyMemucError as e:
            return f"Error checking VM status: {e}"

    @mcp.tool()
    def start_vm(vm_index: int) -> str:
        """Boot a VM and wait for Android to fully load."""
        try:
            validate_vm_index(vm_index)
            audit_log("start_vm", vm_index)
            memuc.start_vm(vm_index=vm_index)
            return f"VM {vm_index} started successfully"
        except (PyMemucError, ValueError) as e:
            return f"Error starting VM {vm_index}: {e}"

    @mcp.tool()
    def stop_vm(vm_index: int) -> str:
        """Gracefully shut down a VM. Cannot stop protected (pre-existing) VMs."""
        try:
            validate_vm_index(vm_index)
            assert_not_protected(vm_index, "stop_vm")
            audit_log("stop_vm", vm_index)
            memuc.stop_vm(vm_index=vm_index)
            return f"VM {vm_index} stopped successfully"
        except RuntimeError as e:
            return str(e)
        except (PyMemucError, ValueError) as e:
            return f"Error stopping VM {vm_index}: {e}"

    @mcp.tool()
    def stop_all_vms() -> str:
        """Stop all running VMs that are NOT protected (pre-existing). Protected VMs are skipped."""
        try:
            vms = memuc.list_vm_info()
            stopped = []
            skipped = []
            for vm in vms:
                if not vm["running"]:
                    continue
                if is_protected(vm["index"]):
                    skipped.append(f"{vm['title']} (index {vm['index']})")
                else:
                    memuc.stop_vm(vm_index=vm["index"])
                    stopped.append(f"{vm['title']} (index {vm['index']})")
            parts = []
            if stopped:
                parts.append(f"Stopped: {', '.join(stopped)}")
            if skipped:
                parts.append(f"Skipped (protected): {', '.join(skipped)}")
            if not parts:
                return "No running non-protected VMs to stop."
            return "; ".join(parts)
        except PyMemucError as e:
            return f"Error stopping VMs: {e}"

    @mcp.tool()
    def reboot_vm(vm_index: int) -> str:
        """Reboot a VM. Cannot reboot protected (pre-existing) VMs."""
        try:
            assert_not_protected(vm_index, "reboot_vm")
            memuc.reboot_vm(vm_index=vm_index)
            return f"VM {vm_index} rebooted successfully"
        except RuntimeError as e:
            return str(e)
        except PyMemucError as e:
            return f"Error rebooting VM {vm_index}: {e}"

    @mcp.tool()
    def create_vm(vm_version: str = "96") -> str:
        """Create a new VM. Version options: '76'=Android 7.1-64bit, '96'=Android 9-64bit. Default is '96'."""
        try:
            vm_index = memuc.create_vm(vm_version=vm_version)
            return f"Created new VM with index {vm_index} (version {vm_version})"
        except PyMemucError as e:
            return f"Error creating VM: {e}"

    @mcp.tool()
    def delete_vm(vm_index: int) -> str:
        """Permanently delete a VM. Cannot delete protected (pre-existing) VMs."""
        try:
            validate_vm_index(vm_index)
            assert_not_protected(vm_index, "delete_vm")
            audit_log("delete_vm", vm_index)
            memuc.delete_vm(vm_index=vm_index)
            return f"VM {vm_index} deleted successfully"
        except RuntimeError as e:
            return str(e)
        except (PyMemucError, ValueError) as e:
            return f"Error deleting VM {vm_index}: {e}"

    @mcp.tool()
    def clone_vm(vm_index: int, new_name: str = None) -> str:
        """Clone an existing VM into a new instance. Optionally provide a name for the clone."""
        try:
            if new_name:
                result = memuc.clone_vm(vm_index=vm_index, new_name=new_name)
            else:
                result = memuc.clone_vm(vm_index=vm_index)
            return f"VM {vm_index} cloned successfully. Result: {result}"
        except PyMemucError as e:
            return f"Error cloning VM {vm_index}: {e}"

    @mcp.tool()
    def rename_vm(vm_index: int, new_name: str) -> str:
        """Rename a VM. Cannot rename protected (pre-existing) VMs."""
        try:
            assert_not_protected(vm_index, "rename_vm")
            memuc.rename_vm(vm_index=vm_index, new_name=new_name)
            return f"VM {vm_index} renamed to '{new_name}'"
        except RuntimeError as e:
            return str(e)
        except PyMemucError as e:
            return f"Error renaming VM {vm_index}: {e}"

    @mcp.tool()
    def export_vm(vm_index: int, output_path: str) -> str:
        """Export a VM snapshot to an .ova file at the specified local path."""
        try:
            memuc.export_vm(vm_index=vm_index, file_name=output_path)
            return f"VM {vm_index} exported to {output_path}"
        except PyMemucError as e:
            return f"Error exporting VM {vm_index}: {e}"

    @mcp.tool()
    def import_vm(ova_path: str) -> str:
        """Import a VM from an .ova file."""
        try:
            memuc.import_vm(file_name=ova_path)
            # Get the new VM index from the list
            vms = memuc.list_vm_info()
            new_index = max(vm["index"] for vm in vms) if vms else 0
            return f"VM imported successfully with index {new_index}"
        except PyMemucError as e:
            return f"Error importing VM: {e}"

    @mcp.tool()
    def compress_vm(vm_index: int) -> str:
        """Compress a VM's disk image to reclaim space. VM must be stopped."""
        try:
            assert_not_protected(vm_index, "compress_vm")
            memuc.compress_vm(vm_index=vm_index)
            return f"VM {vm_index} disk compressed successfully"
        except RuntimeError as e:
            return str(e)
        except PyMemucError as e:
            return f"Error compressing VM {vm_index}: {e}"

    @mcp.tool()
    def check_task_status(task_id: str) -> str:
        """Check the status of an async MEMUC task (returned by non-blocking operations). Returns success/running/failed."""
        try:
            rc, output = memuc.check_task_status(task_id)
            return f"Task {task_id}: [RC={rc}] {output.strip()}"
        except PyMemucError as e:
            return f"Error checking task: {e}"

    @mcp.tool()
    def sort_out_all_vms() -> str:
        """Re-tile all VM windows on the screen for a neat layout."""
        try:
            memuc.sort_out_all_vm()
            return "All VM windows re-tiled"
        except PyMemucError as e:
            return f"Error sorting VM windows: {e}"
