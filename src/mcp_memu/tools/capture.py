"""Screenshot & Capture tools — take screenshot, get base64, get screen size."""

import base64
import os
import tempfile

from pymemuc import PyMemucError

from mcp_memu.utils.memuc_instance import memuc, logger
from mcp_memu.utils.adb_helpers import adb_pull


def _clean_adb_output(output: str) -> str:
    """Remove 'already connected to ...' prefix from ADB output."""
    if not output:
        return ""
    lines = output.strip().split("\n")
    cleaned = [l for l in lines if not l.startswith("already connected")]
    return "\n".join(cleaned).strip()


def register_tools(mcp):
    """Register all capture tools with the MCP server."""

    @mcp.tool()
    def take_screenshot(vm_index: int, save_path: str) -> str:
        """Capture the VM screen and save to a local file path. Provide full path like 'C:\\screenshots\\screen.png'.
        Note: If using DirectX rendering mode, the screenshot may be blank.
        """
        try:
            # Capture on device using execcmd (safest method to avoid ADB hangs)
            memuc.memuc_run(
                ["execcmd", "-i", str(vm_index), "screencap -p /sdcard/mcp_screenshot.png"],
                timeout=15
            )
            # Pull to local
            result = adb_pull(vm_index, "/sdcard/mcp_screenshot.png", save_path)
            
            # Clean up on device
            memuc.memuc_run(
                ["execcmd", "-i", str(vm_index), "rm /sdcard/mcp_screenshot.png"],
                timeout=5
            )
            
            # Check for completely blank/black screens (usually < 5KB for 720p/1080p PNGs)
            if os.path.exists(save_path):
                sz = os.path.getsize(save_path)
                if sz > 0 and sz < 10000:
                    return f"Successfully saved to {save_path} (Warning: File is very small ({sz} bytes). If the image is blank, this is a known issue with MEmu's DirectX rendering mode. Switch to OpenGL in VM settings and restart the VM.)"
            return result
        except Exception as e:
            return f"Error taking screenshot: {e}"

    @mcp.tool()
    def screenshot_base64(vm_index: int) -> str:
        """Take a screenshot and return it as a base64-encoded PNG string. Useful for LLM vision analysis."""
        try:
            memuc.memuc_run(
                ["execcmd", "-i", str(vm_index), "screencap -p /sdcard/mcp_screenshot.png"],
                timeout=15
            )
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                tmp_path = f.name
            try:
                pull_result = adb_pull(vm_index, "/sdcard/mcp_screenshot.png", tmp_path)
                memuc.memuc_run(
                    ["execcmd", "-i", str(vm_index), "rm /sdcard/mcp_screenshot.png"],
                    timeout=5
                )
                if "Error" in pull_result or "error" in pull_result:
                    return f"Screenshot capture failed: {pull_result}"
                
                sz = 0
                if os.path.exists(tmp_path):
                    sz = os.path.getsize(tmp_path)
                    
                with open(tmp_path, "rb") as f:
                    b64data = base64.b64encode(f.read()).decode()
                    
                if sz > 0 and sz < 10000:
                    logger.warning(f"Screenshot very small ({sz} bytes). DirectX rendering mode issue likely.")
                    # We still return the base64, but the caller might see a black image.
                return b64data
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
        except Exception as e:
            return f"Error capturing screenshot: {e}"

    @mcp.tool()
    def get_screen_size(vm_index: int) -> str:
        """Get the current screen resolution (width x height) of a VM. VM must be running.

        Args:
            vm_index: VM index (0, 1, 2...).

        Returns: Screen dimensions (e.g. "Physical size: 720x1280").
        """
        try:
            # Try execcmd for clean output
            rc, output = memuc.memuc_run(
                ["execcmd", "-i", str(vm_index), "wm size"]
            )
            result = output.strip() if output else ""
            if result and "not found" not in result:
                return f"VM {vm_index} screen size: {result}"
            # Fallback: read from config
            w = memuc.get_configuration_vm("resolution_width", vm_index=vm_index)
            h = memuc.get_configuration_vm("resolution_height", vm_index=vm_index)
            dpi = memuc.get_configuration_vm("vbox_dpi", vm_index=vm_index)
            return f"VM {vm_index} screen size: {w}x{h} @ {dpi} DPI"
        except PyMemucError as e:
            return f"Error getting screen size: {e}"

