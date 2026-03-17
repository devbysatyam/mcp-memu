"""UI Interaction tools — tap, swipe, long press, type text, keys, scroll, shake, rotate, zoom."""

from pymemuc import PyMemucError

from utils.memuc_instance import memuc, logger


def register_tools(mcp):
    """Register all UI interaction tools with the MCP server."""

    @mcp.tool()
    def tap(vm_index: int, x: int, y: int) -> str:
        """Tap at specific screen coordinates (x, y) on a VM."""
        try:
            rc, output = memuc.execute_command_vm(f"input tap {x} {y}", vm_index=vm_index)
            return f"Tapped at ({x}, {y}) on VM {vm_index}"
        except PyMemucError as e:
            return f"Error tapping: {e}"

    @mcp.tool()
    def swipe(vm_index: int, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300) -> str:
        """Swipe gesture from (x1,y1) to (x2,y2) over duration_ms milliseconds."""
        try:
            rc, output = memuc.execute_command_vm(
                f"input swipe {x1} {y1} {x2} {y2} {duration_ms}", vm_index=vm_index
            )
            return f"Swiped from ({x1},{y1}) to ({x2},{y2}) on VM {vm_index}"
        except PyMemucError as e:
            return f"Error swiping: {e}"

    @mcp.tool()
    def long_press(vm_index: int, x: int, y: int, duration_ms: int = 1000) -> str:
        """Long press at coordinates (x, y) for duration_ms milliseconds."""
        try:
            rc, output = memuc.execute_command_vm(
                f"input swipe {x} {y} {x} {y} {duration_ms}", vm_index=vm_index
            )
            return f"Long pressed at ({x}, {y}) for {duration_ms}ms on VM {vm_index}"
        except PyMemucError as e:
            return f"Error long pressing: {e}"

    @mcp.tool()
    def input_text(vm_index: int, text: str) -> str:
        """Type text into the currently focused field on a VM. Supports Unicode."""
        try:
            memuc.input_text_vm(text, vm_index=vm_index)
            return f"Text typed on VM {vm_index}: '{text}'"
        except PyMemucError as e:
            return f"Error typing text: {e}"

    @mcp.tool()
    def send_key(vm_index: int, key: str) -> str:
        """Send a key press. Keys: home, back, menu, volumeup, volumedown."""
        try:
            memuc.trigger_keystroke_vm(key, vm_index=vm_index)
            return f"Key '{key}' sent to VM {vm_index}"
        except PyMemucError as e:
            return f"Error sending key: {e}"

    @mcp.tool()
    def press_enter(vm_index: int) -> str:
        """Press the Enter/OK key on a VM (keyevent 66)."""
        try:
            rc, output = memuc.execute_command_vm("input keyevent 66", vm_index=vm_index)
            return f"Enter key pressed on VM {vm_index}"
        except PyMemucError as e:
            return f"Error pressing enter: {e}"

    @mcp.tool()
    def press_back(vm_index: int) -> str:
        """Press the Android back button on a VM."""
        try:
            memuc.trigger_keystroke_vm("back", vm_index=vm_index)
            return f"Back button pressed on VM {vm_index}"
        except PyMemucError as e:
            return f"Error pressing back: {e}"

    @mcp.tool()
    def press_home(vm_index: int) -> str:
        """Press the Android home button on a VM."""
        try:
            memuc.trigger_keystroke_vm("home", vm_index=vm_index)
            return f"Home button pressed on VM {vm_index}"
        except PyMemucError as e:
            return f"Error pressing home: {e}"

    @mcp.tool()
    def shake_device(vm_index: int) -> str:
        """Trigger a shake gesture on a VM."""
        try:
            memuc.trigger_shake_vm(vm_index=vm_index)
            return f"Shake triggered on VM {vm_index}"
        except PyMemucError as e:
            return f"Error shaking: {e}"

    @mcp.tool()
    def rotate_screen(vm_index: int) -> str:
        """Toggle screen orientation (portrait/landscape) on a VM."""
        try:
            memuc.rotate_window_vm(vm_index=vm_index)
            return f"Screen rotated on VM {vm_index}"
        except PyMemucError as e:
            return f"Error rotating: {e}"

    @mcp.tool()
    def zoom_in(vm_index: int) -> str:
        """Pinch zoom in on a VM."""
        try:
            memuc.zoom_in_vm(vm_index=vm_index)
            return f"Zoomed in on VM {vm_index}"
        except PyMemucError as e:
            return f"Error zooming in: {e}"

    @mcp.tool()
    def zoom_out(vm_index: int) -> str:
        """Pinch zoom out on a VM."""
        try:
            memuc.zoom_out_vm(vm_index=vm_index)
            return f"Zoomed out on VM {vm_index}"
        except PyMemucError as e:
            return f"Error zooming out: {e}"

    @mcp.tool()
    def scroll_up(vm_index: int, x: int = 540) -> str:
        """Scroll upward at the given x position on a VM screen."""
        try:
            memuc.memuc_run(
                ["execcmd", "-i", str(vm_index), f"input swipe {x} 500 {x} 1500 300"]
            )
            return f"Scrolled up on VM {vm_index}"
        except PyMemucError as e:
            return f"Error scrolling up: {e}"

    @mcp.tool()
    def scroll_down(vm_index: int, x: int = 540) -> str:
        """Scroll downward at the given x position on a VM screen."""
        try:
            memuc.memuc_run(
                ["execcmd", "-i", str(vm_index), f"input swipe {x} 1500 {x} 500 300"]
            )
            return f"Scrolled down on VM {vm_index}"
        except PyMemucError as e:
            return f"Error scrolling down: {e}"
