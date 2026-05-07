"""
Investigation tools for the InvestigationAgent.

Covers:
  - RDP session diagnostics
  - Server reachability / health checks
  - Web URL / HTTP endpoint checks
  - Database session diagnostics
  - Port connectivity checks
  - Process / service status checks
  - Network latency / traceroute
  - SSL certificate validation
  - Disk / memory / CPU resource checks

All functions are stubbed with realistic synthetic responses.
Replace the stub bodies with real API / SSH / monitoring calls.
"""

import random
from langchain_core.tools import tool
from app.data.infra_data import SERVER_NAMES, APPS, DB_INSTANCES, ENDPOINTS


# ── RDP ───────────────────────────────────────────────────────────────────────

@tool
def check_rdp_session(user_id: str, server: str) -> dict:
    """
    Diagnose why an RDP session is failing for a user on a given server.

    Checks: RDP service status, port 3389 availability, concurrent session
    limit, user's RDP permission, and firewall rules.

    Args:
        user_id: The user attempting the RDP connection.
        server:  The target server hostname or IP.

    Returns:
        Dict with keys: rdp_service_running, port_3389_open,
        session_limit_reached, user_has_rdp_permission,
        firewall_blocking, error_code, recommendation.
    """
    rdp_issues = [
        {"rdp_service_running": False, "port_3389_open": False,
         "session_limit_reached": False, "user_has_rdp_permission": True,
         "firewall_blocking": False,
         "error_code": "RDP_SERVICE_STOPPED",
         "recommendation": "RDP service (TermService) is stopped on the server. Start it via Services or run: sc start TermService"},

        {"rdp_service_running": True, "port_3389_open": False,
         "session_limit_reached": False, "user_has_rdp_permission": True,
         "firewall_blocking": True,
         "error_code": "FIREWALL_BLOCKING_3389",
         "recommendation": "Firewall rule is blocking port 3389. Add an inbound rule to allow TCP 3389 from the user's IP range."},

        {"rdp_service_running": True, "port_3389_open": True,
         "session_limit_reached": True, "user_has_rdp_permission": True,
         "firewall_blocking": False,
         "error_code": "SESSION_LIMIT_REACHED",
         "recommendation": "Max concurrent RDP sessions reached. An admin must disconnect an idle session or increase the session limit."},

        {"rdp_service_running": True, "port_3389_open": True,
         "session_limit_reached": False, "user_has_rdp_permission": False,
         "firewall_blocking": False,
         "error_code": "USER_NOT_IN_RDP_GROUP",
         "recommendation": f"User {user_id} is not in the 'Remote Desktop Users' group on {server}. Add via: Computer Management > Local Users and Groups."},

        {"rdp_service_running": True, "port_3389_open": True,
         "session_limit_reached": False, "user_has_rdp_permission": True,
         "firewall_blocking": False,
         "error_code": "CREDENTIAL_ERROR",
         "recommendation": "RDP infrastructure is healthy. The issue is likely an expired password or wrong credentials. Ask the user to reset their password."},
    ]
    result = random.choice(rdp_issues)
    result["server"] = server
    result["user_id"] = user_id
    return result


# ── Server health ─────────────────────────────────────────────────────────────

@tool
def check_server_health(server: str) -> dict:
    """
    Check if a server is reachable and assess its overall health.

    Checks: ICMP ping, CPU usage, memory usage, disk usage, and uptime.

    Args:
        server: The server hostname or IP to check.

    Returns:
        Dict with keys: reachable, ping_latency_ms, cpu_usage_pct,
        memory_usage_pct, disk_usage_pct, uptime_hours,
        status, issues.
    """
    reachable = random.choices([True, False], weights=[75, 25])[0]
    if not reachable:
        return {
            "server": server,
            "reachable": False,
            "ping_latency_ms": None,
            "cpu_usage_pct": None,
            "memory_usage_pct": None,
            "disk_usage_pct": None,
            "uptime_hours": None,
            "status": "UNREACHABLE",
            "issues": ["Server is not responding to ping. It may be down, or ICMP is blocked."],
        }

    cpu   = random.randint(5, 99)
    mem   = random.randint(20, 98)
    disk  = random.randint(10, 97)
    ping  = random.randint(1, 250)
    uptime = random.randint(1, 8760)

    issues = []
    if cpu  > 90: issues.append(f"HIGH CPU: {cpu}% — server may be under heavy load.")
    if mem  > 90: issues.append(f"HIGH MEMORY: {mem}% — risk of OOM; consider restarting services.")
    if disk > 85: issues.append(f"HIGH DISK: {disk}% — low disk space may cause service failures.")
    if ping > 150: issues.append(f"HIGH LATENCY: {ping}ms — network path to server is slow.")

    return {
        "server": server,
        "reachable": True,
        "ping_latency_ms": ping,
        "cpu_usage_pct": cpu,
        "memory_usage_pct": mem,
        "disk_usage_pct": disk,
        "uptime_hours": uptime,
        "status": "DEGRADED" if issues else "HEALTHY",
        "issues": issues,
    }


# ── Web URL ───────────────────────────────────────────────────────────────────

@tool
def check_web_url(url: str) -> dict:
    """
    Check if a web URL / HTTP endpoint is reachable and returning expected responses.

    Checks: DNS resolution, HTTP response code, SSL certificate validity,
    response time, and redirect chains.

    Args:
        url: The full URL to probe (e.g. 'https://app1.internal/health').

    Returns:
        Dict with keys: dns_resolved, http_status, response_time_ms,
        ssl_valid, ssl_expiry_days, redirect_count, error_code, recommendation.
    """
    scenarios = [
        {"dns_resolved": False, "http_status": None, "response_time_ms": None,
         "ssl_valid": None, "ssl_expiry_days": None, "redirect_count": 0,
         "error_code": "DNS_RESOLUTION_FAILED",
         "recommendation": "DNS lookup failed. Check DNS records for the domain or verify the URL is correct."},

        {"dns_resolved": True, "http_status": 502, "response_time_ms": 120,
         "ssl_valid": True, "ssl_expiry_days": 45, "redirect_count": 0,
         "error_code": "BAD_GATEWAY",
         "recommendation": "502 Bad Gateway — the upstream application server is not responding. Check app server health."},

        {"dns_resolved": True, "http_status": 503, "response_time_ms": 90,
         "ssl_valid": True, "ssl_expiry_days": 45, "redirect_count": 0,
         "error_code": "SERVICE_UNAVAILABLE",
         "recommendation": "503 Service Unavailable — the app is under maintenance or overloaded. Check deployment status."},

        {"dns_resolved": True, "http_status": 200, "response_time_ms": random.randint(2000, 8000),
         "ssl_valid": True, "ssl_expiry_days": 45, "redirect_count": 1,
         "error_code": "SLOW_RESPONSE",
         "recommendation": "URL is reachable but response time is very high. Check backend performance and database query times."},

        {"dns_resolved": True, "http_status": 200, "response_time_ms": 95,
         "ssl_valid": False, "ssl_expiry_days": -3, "redirect_count": 0,
         "error_code": "SSL_CERTIFICATE_EXPIRED",
         "recommendation": "SSL certificate expired 3 days ago. Renew the certificate immediately to restore HTTPS access."},

        {"dns_resolved": True, "http_status": 200, "response_time_ms": 88,
         "ssl_valid": True, "ssl_expiry_days": 4, "redirect_count": 0,
         "error_code": "SSL_EXPIRY_WARNING",
         "recommendation": "SSL certificate expires in 4 days. Renew urgently to prevent browser warnings and downtime."},

        {"dns_resolved": True, "http_status": 200, "response_time_ms": 102,
         "ssl_valid": True, "ssl_expiry_days": 120, "redirect_count": 0,
         "error_code": None,
         "recommendation": "URL is healthy and fully operational."},
    ]
    result = random.choice(scenarios)
    result["url"] = url
    return result


# ── Database session ──────────────────────────────────────────────────────────

@tool
def check_db_session(user_id: str, db_instance: str) -> dict:
    """
    Diagnose a failing database session for a user on a given DB instance.

    Checks: DB service status, port connectivity, connection pool usage,
    user credentials/permissions, and active locks.

    Args:
        user_id:     The user or service account attempting the DB connection.
        db_instance: The database instance name or host (e.g. 'db-prod-01').

    Returns:
        Dict with keys: db_service_running, port_open, connection_pool_exhausted,
        user_has_db_access, active_locks, max_connections, current_connections,
        error_code, recommendation.
    """
    scenarios = [
        {"db_service_running": False, "port_open": False,
         "connection_pool_exhausted": False, "user_has_db_access": True,
         "active_locks": 0, "max_connections": 200, "current_connections": 0,
         "error_code": "DB_SERVICE_DOWN",
         "recommendation": f"Database service on {db_instance} is not running. Restart the DB service or check with the DBA team."},

        {"db_service_running": True, "port_open": True,
         "connection_pool_exhausted": True, "user_has_db_access": True,
         "active_locks": 0, "max_connections": 200, "current_connections": 200,
         "error_code": "CONNECTION_POOL_EXHAUSTED",
         "recommendation": "Connection pool is full (200/200). Increase max_connections or kill idle connections: SELECT pg_terminate_backend(pid) WHERE state='idle'."},

        {"db_service_running": True, "port_open": True,
         "connection_pool_exhausted": False, "user_has_db_access": False,
         "active_locks": 0, "max_connections": 200, "current_connections": 45,
         "error_code": "DB_ACCESS_DENIED",
         "recommendation": f"User {user_id} does not have CONNECT privilege on {db_instance}. Grant access: GRANT CONNECT ON DATABASE <db> TO {user_id};"},

        {"db_service_running": True, "port_open": True,
         "connection_pool_exhausted": False, "user_has_db_access": True,
         "active_locks": 12, "max_connections": 200, "current_connections": 80,
         "error_code": "LOCK_CONTENTION",
         "recommendation": "High lock contention detected (12 active locks). A long-running transaction may be blocking sessions. Identify and kill the blocking query."},

        {"db_service_running": True, "port_open": False,
         "connection_pool_exhausted": False, "user_has_db_access": True,
         "active_locks": 0, "max_connections": 200, "current_connections": 0,
         "error_code": "DB_PORT_BLOCKED",
         "recommendation": "DB port is not reachable. Check firewall/security-group rules between the app server and the DB instance."},
    ]
    result = random.choice(scenarios)
    result["db_instance"] = db_instance
    result["user_id"] = user_id
    return result


# ── Port connectivity ─────────────────────────────────────────────────────────

@tool
def check_port_connectivity(server: str, port: int) -> dict:
    """
    Check whether a specific TCP port is open and reachable on a server.

    Useful for confirming that a service port (e.g. 443, 8080, 5432, 3306)
    is accessible before deeper diagnostics.

    Args:
        server: The server hostname or IP.
        port:   The TCP port number to check (e.g. 443, 3389, 5432).

    Returns:
        Dict with keys: server, port, is_open, latency_ms, error_code.
    """
    is_open   = random.choices([True, False], weights=[70, 30])[0]
    latency   = random.randint(1, 300) if is_open else None
    error     = None if is_open else random.choice([
        "CONNECTION_REFUSED", "CONNECTION_TIMEOUT", "NO_ROUTE_TO_HOST"
    ])
    return {
        "server": server,
        "port": port,
        "is_open": is_open,
        "latency_ms": latency,
        "error_code": error,
    }


# ── Service / process status ──────────────────────────────────────────────────

@tool
def check_service_status(server: str, service_name: str) -> dict:
    """
    Check if a named OS service or process is running on a server.

    Use when a specific service (e.g. 'nginx', 'sshd', 'mssql', 'tomcat')
    needs to be verified as part of troubleshooting.

    Args:
        server:       The server to check.
        service_name: The service or process name (e.g. 'nginx', 'tomcat').

    Returns:
        Dict with keys: server, service_name, is_running, pid,
        restart_count, last_exit_code, recommendation.
    """
    is_running    = random.choices([True, False], weights=[70, 30])[0]
    restart_count = random.randint(0, 15) if not is_running else random.randint(0, 2)
    last_exit     = 0 if is_running else random.choice([1, 127, 137, 143, 255])
    pid           = random.randint(1000, 60000) if is_running else None

    recs = {
        True:  f"Service '{service_name}' is running normally (PID {pid}).",
        False: f"Service '{service_name}' is stopped. Restart it: systemctl start {service_name}. Check logs: journalctl -u {service_name} -n 50",
    }
    return {
        "server": server,
        "service_name": service_name,
        "is_running": is_running,
        "pid": pid,
        "restart_count_24h": restart_count,
        "last_exit_code": last_exit,
        "recommendation": recs[is_running],
    }


# ── Network latency ───────────────────────────────────────────────────────────

@tool
def check_network_latency(source_server: str, target: str) -> dict:
    """
    Measure network latency and check for packet loss between two endpoints.

    Use when slow or dropped connections are suspected to be a network issue.

    Args:
        source_server: The originating server or 'client'.
        target:        The target server or IP to measure latency to.

    Returns:
        Dict with keys: avg_latency_ms, min_latency_ms, max_latency_ms,
        packet_loss_pct, hops, status, recommendation.
    """
    avg   = random.randint(1, 400)
    pkt_loss = random.choices([0, random.randint(1, 50)], weights=[70, 30])[0]
    hops  = random.randint(1, 20)
    status = "NORMAL" if avg < 100 and pkt_loss == 0 else \
             "DEGRADED" if avg < 200 or pkt_loss < 20 else "POOR"

    recs = {
        "NORMAL":   "Network path is healthy.",
        "DEGRADED": f"Elevated latency ({avg}ms) or minor packet loss ({pkt_loss}%). Check intermediate network hops.",
        "POOR":     f"Severe latency ({avg}ms) and packet loss ({pkt_loss}%). Likely a network fault. Escalate to network team.",
    }
    return {
        "source": source_server,
        "target": target,
        "avg_latency_ms": avg,
        "min_latency_ms": max(1, avg - random.randint(5, 30)),
        "max_latency_ms": avg + random.randint(10, 100),
        "packet_loss_pct": pkt_loss,
        "hops": hops,
        "status": status,
        "recommendation": recs[status],
    }
