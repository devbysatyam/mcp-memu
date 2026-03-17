"""VM Configuration tools — get/set CPU, RAM, resolution, GPS, randomize device."""

from pymemuc import PyMemucError

from mcp_memu.utils.memuc_instance import memuc, logger

# Complete list of valid ConfigKeys from PyMEMUC
_ALL_CONFIG_KEYS = [
    "name", "cpus", "cpucap", "memory",
    "is_full_screen", "is_hide_toolbar", "turbo_mode",
    "graphics_render_mode", "enable_su", "enable_audio",
    "fps", "vkeyboard_mode", "sync_time", "phone_layout",
    "start_window_mode", "win_x", "win_y", "win_scaling_percent2",
    "is_customed_resolution", "resolution_width", "resolution_height",
    "vbox_dpi", "linenum", "imei", "imsi", "simserial",
    "microvirt_vm_brand", "microvirt_vm_model", "microvirt_vm_manufacturer",
    "selected_map", "latitude", "longitude",
    "picturepath", "musicpath", "moviepath", "downloadpath",
    "macaddress", "cache_mode", "geometry", "custom_resolution",
    "disable_resize", "ssid",
]

# Most useful keys for quick overview
_DISPLAY_KEYS = [
    "cpus", "memory", "resolution_width", "resolution_height",
    "vbox_dpi", "fps", "macaddress", "imei", "imsi",
    "enable_su", "turbo_mode", "cache_mode",
    "microvirt_vm_brand", "microvirt_vm_model",
    "latitude", "longitude",
]


def register_tools(mcp):
    """Register all configuration tools with the MCP server."""

    @mcp.tool()
    def get_all_vm_config(vm_index: int) -> str:
        """Get ALL common configuration values for a VM in a single call.
        Returns CPU, memory, resolution, DPI, MAC, IMEI, device model/brand,
        root status, GPS coordinates, and more.

        Args:
            vm_index: VM index (0, 1, 2...). Use list_vms to find indices.

        Returns: All config values in key=value format.

        Example output:
            VM 0 configuration:
              cpus = 2
              memory = 2048
              resolution_width = 720
              resolution_height = 1280
              vbox_dpi = 240
              enable_su = 1
              macaddress = ...
        """
        results = []
        for k in _DISPLAY_KEYS:
            try:
                value = memuc.get_configuration_vm(k, vm_index=vm_index)
                results.append(f"  {k} = {value}")
            except Exception:
                pass
        if results:
            return f"VM {vm_index} configuration:\n" + "\n".join(results)
        return f"VM {vm_index}: Could not read config keys."

    @mcp.tool()
    def get_vm_config(vm_index: int, key: str) -> str:
        """Get a single VM configuration value.

        Args:
            vm_index: VM index (0, 1, 2...). Use list_vms to find indices.
            key: Configuration key. Must be one of these valid keys:

                Hardware:
                  cpus (1/2/4/8), cpucap (0-100), memory (MB)

                Display:
                  is_full_screen (0/1), is_hide_toolbar (0/1),
                  is_customed_resolution (0/1), resolution_width, resolution_height,
                  vbox_dpi, fps (0-100), graphics_render_mode (0=OpenGL, 1=DirectX),
                  start_window_mode (0=Default, 1=Last, 2=Custom),
                  win_x, win_y, win_scaling_percent2, disable_resize (0/1)

                Device identity:
                  name, imei, imsi, simserial, linenum (phone number),
                  microvirt_vm_brand, microvirt_vm_model, microvirt_vm_manufacturer,
                  macaddress, ssid (WiFi name)

                Performance:
                  turbo_mode (0/1), cache_mode (0=stable, 1=fast),
                  enable_su (0/1), enable_audio (0/1), sync_time (0/1)

                GPS:
                  latitude, longitude, selected_map (0=Google, 1=Baidu)

                Shared folders:
                  picturepath, musicpath, moviepath, downloadpath

                Other:
                  phone_layout (0=Bottom, 1=Right, 2=Toolbar),
                  vkeyboard_mode (0/1), geometry (x y w h),
                  custom_resolution (w h dpi)

        Returns: The config value string.

        Example: get_vm_config(vm_index=0, key="cpus") → "VM 0 config 'cpus' = 2"
        """
        if not key or not key.strip():
            return ("Error: key is required. Use get_all_vm_config to see all configs, "
                    "or provide a specific key like 'cpus', 'memory', 'imei', etc.")
        try:
            value = memuc.get_configuration_vm(key, vm_index=vm_index)
            return f"VM {vm_index} config '{key}' = {value}"
        except PyMemucError as e:
            return f"Error getting config '{key}': {e}"

    @mcp.tool()
    def set_vm_config(vm_index: int, key: str, value: str) -> str:
        """Set a VM configuration value. VM must be stopped for most settings.

        Args:
            vm_index: VM index (0, 1, 2...).
            key: Config key (see get_vm_config for the full list of valid keys).
            value: New value as a string (e.g. "2", "4096", "1").

        Returns: Confirmation message.

        Example: set_vm_config(vm_index=0, key="cpus", value="4")
        """
        try:
            memuc.set_configuration_vm(key, value, vm_index=vm_index)
            return f"VM {vm_index} config '{key}' set to '{value}'"
        except PyMemucError as e:
            return f"Error setting config: {e}"

    @mcp.tool()
    def set_vm_cpu(vm_index: int, cores: int) -> str:
        """Set the number of CPU cores for a VM. VM must be stopped.

        Args:
            vm_index: VM index (0, 1, 2...).
            cores: Number of CPU cores. Valid: 1, 2, 4, or 8.

        Returns: Confirmation message.
        """
        try:
            memuc.set_configuration_vm("cpus", str(cores), vm_index=vm_index)
            return f"VM {vm_index} CPU cores set to {cores}"
        except PyMemucError as e:
            return f"Error setting CPU: {e}"

    @mcp.tool()
    def set_vm_memory(vm_index: int, mb: int) -> str:
        """Set the RAM for a VM in megabytes. VM must be stopped.

        Args:
            vm_index: VM index (0, 1, 2...).
            mb: RAM in megabytes. Common values: 1024, 2048, 4096, 8192.

        Returns: Confirmation message.
        """
        try:
            memuc.set_configuration_vm("memory", str(mb), vm_index=vm_index)
            return f"VM {vm_index} memory set to {mb} MB"
        except PyMemucError as e:
            return f"Error setting memory: {e}"

    @mcp.tool()
    def set_vm_resolution(vm_index: int, width: int, height: int, dpi: int) -> str:
        """Set custom screen resolution for a VM. VM must be stopped.

        Args:
            vm_index: VM index.
            width: Screen width in pixels (e.g. 720, 1080).
            height: Screen height in pixels (e.g. 1280, 1920).
            dpi: Dots per inch (e.g. 240 for 720p, 480 for 1080p).

        Common presets:
            Phone HD: 720x1280 @ 240 DPI
            Phone FHD: 1080x1920 @ 480 DPI
            Tablet: 1920x1080 @ 240 DPI

        Returns: Confirmation message.
        """
        try:
            memuc.set_configuration_vm("is_customed_resolution", "1", vm_index=vm_index)
            memuc.set_configuration_vm("resolution_width", str(width), vm_index=vm_index)
            memuc.set_configuration_vm("resolution_height", str(height), vm_index=vm_index)
            memuc.set_configuration_vm("vbox_dpi", str(dpi), vm_index=vm_index)
            return f"VM {vm_index} resolution set to {width}x{height} @ {dpi} DPI"
        except PyMemucError as e:
            return f"Error setting resolution: {e}"

    @mcp.tool()
    def set_vm_gps(vm_index: int, lat: float, lng: float) -> str:
        """Set spoofed GPS coordinates for a VM.

        Args:
            vm_index: VM index.
            lat: Latitude in degrees (e.g. 37.7749 for San Francisco).
            lng: Longitude in degrees (e.g. -122.4194 for San Francisco).

        Returns: Confirmation message.
        """
        try:
            memuc.change_gps_vm(lat, lng, vm_index=vm_index)
            return f"VM {vm_index} GPS set to ({lat}, {lng})"
        except PyMemucError as e:
            return f"Error setting GPS: {e}"

    @mcp.tool()
    def randomize_vm_device(vm_index: int) -> str:
        """Randomize the device fingerprint of a VM (MAC, IMEI, model, manufacturer, etc.).
        Makes the VM appear as a different physical device.

        Args:
            vm_index: VM index.

        Returns: Confirmation message.
        """
        try:
            memuc.randomize_vm(vm_index=vm_index)
            return f"VM {vm_index} device fingerprint randomized"
        except PyMemucError as e:
            return f"Error randomizing device: {e}"

