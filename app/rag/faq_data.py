"""
Sample FAQ / Q&A knowledge base for the Access Resolver Agent.

Each entry has:
  - question : canonical question text (used for embedding)
  - answer   : resolution steps / explanation
  - category : tag for optional filtering
"""

FAQ_DATA = [
    # ── Account / Login ──────────────────────────────────────────────────────
    {
        "question": "Why can't I log in to the application?",
        "answer": (
            "Common causes: (1) Your password has expired — reset it via the "
            "self-service portal. (2) Your account may be locked after too many "
            "failed attempts — contact the helpdesk to unlock it. (3) MFA device "
            "is not registered — enrol a new device in the identity portal."
        ),
        "category": "login",
    },
    {
        "question": "My account is locked. How do I unlock it?",
        "answer": (
            "Accounts are auto-locked after 5 failed login attempts. To unlock: "
            "(1) Wait 30 minutes for auto-unlock, OR (2) use the 'Forgot Password' "
            "link on the login page, OR (3) raise a ticket and the helpdesk will "
            "unlock it within 1 business hour."
        ),
        "category": "account",
    },
    {
        "question": "How do I reset my password?",
        "answer": (
            "Visit the self-service password reset portal at /password-reset. "
            "Enter your employee ID and registered email. You will receive a "
            "one-time link valid for 15 minutes. If you do not receive the email, "
            "check your spam folder or raise a ticket."
        ),
        "category": "account",
    },
    {
        "question": "I forgot my username. How do I find it?",
        "answer": (
            "Your username is typically your employee ID (e.g. EMP12345) or "
            "your work email address. Check your onboarding email or contact HR. "
            "The helpdesk can also look it up given your full name and department."
        ),
        "category": "account",
    },

    # ── Access / Permissions ─────────────────────────────────────────────────
    {
        "question": "How do I request access to a new application?",
        "answer": (
            "Submit an access request through the IT Service Portal: "
            "(1) Navigate to 'Request Access', (2) search for the application, "
            "(3) select the required role, (4) provide a business justification. "
            "Your manager will be notified for approval. Standard SLA is 2 business days."
        ),
        "category": "access",
    },
    {
        "question": "I have access but keep getting ACCESS_DENIED errors.",
        "answer": (
            "ACCESS_DENIED despite having access usually means a role/permission "
            "is missing within the app. Steps: (1) Log out and log back in to "
            "refresh your token. (2) Check the app's role assignment page — you may "
            "need a specific sub-role (e.g. ROLE_EDITOR vs ROLE_VIEWER). "
            "(3) If the issue persists, raise a ticket with a screenshot."
        ),
        "category": "access",
    },
    {
        "question": "Why was my access revoked?",
        "answer": (
            "Access is automatically revoked in these scenarios: (1) Role change "
            "or department transfer — re-request access via the Service Portal. "
            "(2) Access not used for 90 days (auto-expiry policy). (3) Compliance "
            "audit triggered a review. Check your email for a revocation notice."
        ),
        "category": "access",
    },
    {
        "question": "How long does access provisioning take?",
        "answer": (
            "Standard applications: up to 2 business days after manager approval. "
            "High-security applications (finance, HR, infra): up to 5 business days "
            "and require a second approval from the data owner. "
            "Urgent requests can be expedited by raising a Priority-1 ticket."
        ),
        "category": "access",
    },

    # ── MFA / SSO ────────────────────────────────────────────────────────────
    {
        "question": "My MFA code is not working.",
        "answer": (
            "Check these first: (1) Ensure your phone's time is synced (TOTP codes "
            "are time-sensitive). (2) Use the current code — they expire every 30 s. "
            "(3) If using SMS, check signal strength. If none of these help, "
            "re-enrol your MFA device in the identity portal or raise a ticket."
        ),
        "category": "mfa",
    },
    {
        "question": "How do I set up MFA on a new device?",
        "answer": (
            "Go to the Identity Portal → Security → MFA Devices → Add Device. "
            "Scan the QR code with an authenticator app (e.g. Google Authenticator, "
            "Microsoft Authenticator). Enter the 6-digit code to confirm. "
            "Remove the old device if it is lost or stolen."
        ),
        "category": "mfa",
    },
    {
        "question": "SSO is not working and I keep getting redirected in a loop.",
        "answer": (
            "SSO redirect loops are usually caused by: (1) Stale browser cookies — "
            "clear cookies and try in an incognito window. (2) The app's SSO "
            "configuration has changed — contact the app owner. (3) Your browser "
            "is blocking third-party cookies — allow them for the identity provider domain."
        ),
        "category": "sso",
    },

    # ── VPN / Remote Access ───────────────────────────────────────────────────
    {
        "question": "I cannot connect to the VPN.",
        "answer": (
            "Troubleshooting steps: (1) Ensure the VPN client is up to date. "
            "(2) Check your internet connection. (3) Confirm your VPN account is "
            "active — it may have expired if unused for 60+ days. "
            "(4) Try a different VPN gateway. If all else fails, raise a ticket "
            "and attach the VPN client log."
        ),
        "category": "vpn",
    },
    {
        "question": "VPN connected but I cannot reach internal resources.",
        "answer": (
            "Being connected to VPN but unable to reach resources suggests a "
            "routing or firewall issue: (1) Check that you are on the correct "
            "VPN profile (Full-Tunnel vs Split-Tunnel). (2) Verify the resource "
            "hostname resolves via internal DNS. (3) Raise a network team ticket "
            "with the target IP/hostname and error message."
        ),
        "category": "vpn",
    },

    # ── Ticketing / Escalation ────────────────────────────────────────────────
    {
        "question": "How do I escalate my ticket?",
        "answer": (
            "To escalate: (1) Open your ticket in the Service Portal and click "
            "'Escalate'. (2) Select a reason (e.g. business impact, SLA breach). "
            "(3) The ticket will be reassigned to a senior engineer within 1 hour. "
            "For critical business impact, call the helpdesk hotline directly."
        ),
        "category": "ticketing",
    },
    {
        "question": "What is the SLA for access-related tickets?",
        "answer": (
            "P1 (Critical — production blocked): 2 hours response, 4 hours resolution. "
            "P2 (High — significant business impact): 4 hours response, 8 hours resolution. "
            "P3 (Medium — workaround available): 8 hours response, 2 business days resolution. "
            "P4 (Low — general query): 1 business day response, 5 business days resolution."
        ),
        "category": "ticketing",
    },
]
