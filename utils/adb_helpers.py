import os
import subprocess
import time

from utils.memuc_instance import memuc, logger

def _ensure_adb_connection(host: str, port: int) -> bool:
    """Attempt to connect and wake up adb if it's offline."""
    target = f"{host}:{port}"
    try:
        # First check if it's already connected and NOT offline
        res = subprocess.run([memuc.memuc_path, "adb", "devices"], capture_output=True, text=True)
        if target in res.stdout and "offline" not in res.stdout.split(target)[1].split("\n")[0]:
            return True
        
        # If offline or missing, disconnect and reconnect using memuc adb
        subprocess.run([memuc.memuc_path, "adb", "disconnect", target], capture_output=True)
        res = subprocess.run([memuc.memuc_path, "adb", "connect", target], capture_output=True, text=True)
        return "connected to" in res.stdout.lower()
    except Exception:
        return False

def adb_pull(vm_index: int, remote_path: str, local_path: str) -> str:
    """Pull a file from a VM to the local host via ADB."""
    try:
        host, port = memuc.get_adb_connection(vm_index=vm_index)
        if host and port:
            _ensure_adb_connection(host, port)
        
        rc, out = memuc.memuc_run(
            ["adb", "-i", str(vm_index), "pull", remote_path, local_path],
            timeout=30
        )
        if rc == 0:
            return f"Successfully pulled {remote_path} to {local_path}"
        return f"ADB pull failed: {out.strip()}"
    except Exception as e:
        return f"Error: {e}"

def adb_push(vm_index: int, local_path: str, remote_path: str) -> str:
    """Push a file from the local host to a VM via ADB."""
    try:
        host, port = memuc.get_adb_connection(vm_index=vm_index)
        if host and port:
            _ensure_adb_connection(host, port)
        
        rc, out = memuc.memuc_run(
            ["adb", "-i", str(vm_index), "push", local_path, remote_path],
            timeout=30
        )
        if rc == 0:
            return f"Successfully pushed {local_path} to {remote_path}"
        return f"ADB push failed: {out.strip()}"
    except Exception as e:
        return f"Error: {e}"
