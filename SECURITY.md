# Security

## Security Model

MCP-MEmu is designed for **local-only** operation (stdio transport). It does not expose any network endpoints or accept remote connections by default.

### Protected VM Registry

On first launch, the server snapshots all existing VM instances into `protected_vms.json`. Destructive operations are **blocked** on protected VMs:

| Blocked Operations | Allowed Operations |
|---|---|
| `delete_vm` | `list_vms`, `get_vm_status` |
| `stop_vm`, `stop_all_vms` | `start_vm` |
| `reboot_vm` | `get_vm_config`, `get_all_vm_config` |
| `rename_vm` | `take_screenshot`, `get_device_info` |
| `compress_vm` | `execute_shell`, `send_adb` |
| `full_vm_snapshot` | All read-only operations |

### Input Validation

- **VM Index**: All tools validate that `vm_index` is a non-negative integer
- **Shell Commands**: `execute_shell` and `send_adb` check commands against a blocklist of dangerous patterns:
  - `rm -rf /` — recursive root deletion
  - `mkfs` — filesystem formatting
  - `dd if=` — raw disk writes
  - `reboot` / `shutdown` — use MCP tools instead
  - `format` / `wipe` — data destruction

### Audit Logging

All destructive operations are logged to stderr with timestamps:
```
[INFO] mcp-memu.audit: [AUDIT 2026-03-17 11:00:00] delete_vm vm_index=1
[INFO] mcp-memu.audit: [AUDIT 2026-03-17 11:00:05] BLOCKED vm_index=0 operation=delete_vm (protected VM)
```

## MCP Protocol Security (OAuth 2.1)

For **remote deployments** (HTTP/SSE transport), the MCP specification recommends:

1. **OAuth 2.1** with PKCE for authentication
2. **HTTPS** with TLS 1.2+ for all endpoints
3. **Per-client consent** to prevent confused deputy attacks
4. **Short-lived access tokens** with least-privilege scopes
5. **No session-based auth** — token validation on every request

This server currently uses **stdio transport** (local only), which does not require OAuth. If deploying remotely, implement an OAuth 2.1 proxy layer.

## Reporting Vulnerabilities

If you find a security issue, please open a GitHub issue or contact the maintainer directly.
