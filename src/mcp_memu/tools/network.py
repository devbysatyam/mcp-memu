"""Network & Sensor tools — connect/disconnect, GPS, IP, accelerometer, ADB connection info."""

from pymemuc import PyMemucError

from mcp_memu.utils.memuc_instance import memuc, logger


def register_tools(mcp):
    """Register all network and sensor tools with the MCP server."""

    @mcp.tool()
    def connect_network(vm_index: int) -> str:
        """Enable internet access on a VM."""
        try:
            memuc.connect_internet_vm(vm_index=vm_index)
            return f"Network connected on VM {vm_index}"
        except PyMemucError as e:
            return f"Error connecting network: {e}"

    @mcp.tool()
    def disconnect_network(vm_index: int) -> str:
        """Disable internet access (airplane mode) on a VM."""
        try:
            memuc.disconnect_internet_vm(vm_index=vm_index)
            return f"Network disconnected on VM {vm_index}"
        except PyMemucError as e:
            return f"Error disconnecting network: {e}"

    @mcp.tool()
    def get_public_ip(vm_index: int) -> str:
        """Get the public IP address of a VM."""
        try:
            rc, output = memuc.get_public_ip_vm(vm_index=vm_index)
            return f"VM {vm_index} public IP: {output.strip()}"
        except PyMemucError as e:
            return f"Error getting public IP: {e}"

    @mcp.tool()
    def set_gps_location(vm_index: int, lat: float, lng: float) -> str:
        """Spoof GPS coordinates on a VM. Provide latitude and longitude."""
        try:
            # The memuc command is: setgps -i <index> <lng> <lat>  (longitude first!)
            rc, output = memuc.memuc_run(
                ["setgps", "-i", str(vm_index), str(lng), str(lat)], 
                timeout=10
            )
            if rc == 0:
                return f"GPS set to ({lat}, {lng}) on VM {vm_index}"
            else:
                return f"Failed to set GPS: {output}"
        except Exception as e:
            return f"Error setting GPS: {e}"

    @mcp.tool()
    def set_accelerometer(vm_index: int, x: float, y: float, z: float) -> str:
        """Set accelerometer sensor values on a VM. Default resting: x=0.0, y=9.8, z=0.0."""
        try:
            rc, output = memuc.set_accelerometer_vm((x, y, z), vm_index=vm_index)
            return f"Accelerometer set to ({x}, {y}, {z}) on VM {vm_index}"
        except PyMemucError as e:
            return f"Error setting accelerometer: {e}"

    @mcp.tool()
    def get_adb_connection_info(vm_index: int) -> str:
        """Get the ADB connection host:port for a VM. Useful for direct ADB commands."""
        try:
            host, port = memuc.get_adb_connection(vm_index=vm_index)
            if host and port:
                return f"VM {vm_index} ADB connection: {host}:{port}"
            return f"VM {vm_index} ADB connection not available (VM may not be running)"
        except PyMemucError as e:
            return f"Error getting ADB connection: {e}"

