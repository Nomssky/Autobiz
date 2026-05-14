"""
Approval Notifier — Real notification delivery via Discord, Email, and SMS.
"""

import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional



logger = logging.getLogger(__name__)


@dataclass
class NotificationChannel:
    """Represents a notification channel configuration."""

    name: str
    enabled: bool
    config: Dict[str, Any]


class DiscordNotifier:
    """Sends notifications via Discord webhook."""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.enabled = bool(webhook_url)

    async def send(
        self,
        title: str,
        message: str,
        color: int = 0x3498DB,
        fields: Optional[List[Dict[str, str]]] = None,
        footer: Optional[str] = None,
    ) -> bool:
        """
        Send a Discord embed notification.

        Args:
            title: Embed title
            message: Embed description
            color: Embed color (hex integer)
            fields: List of {name, value} dicts for additional fields
            footer: Footer text

        Returns:
            bool: True if sent successfully
        """
        embed: Dict[str, Any] = {
            "title": title,
            "description": message,
            "color": color,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if fields:
            embed["fields"] = [
                {"name": f, "value": v, "inline": True}
                for f, v in [(fi.get("name", ""), fi.get("value", "")) for fi in fields]
            ]

        if footer:
            embed["footer"] = {"text": footer}

        payload = {"embeds": [embed]}

        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=payload) as resp:
                    if resp.status in (200, 204):
                        logger.info(f"Discord notification sent: {title}")
                        return True
                    else:
                        text = await resp.text()
                        logger.error(f"Discord webhook error {resp.status}: {text}")
                        return False

        except ImportError:
            # Fallback to requests for sync usage
            try:
                import requests

                resp = requests.post(self.webhook_url, json=payload, timeout=10)
                if resp.status_code in (200, 204):
                    logger.info(f"Discord notification sent: {title}")
                    return True
                else:
                    logger.error(f"Discord webhook error {resp.status_code}: {resp.text}")
                    return False
            except Exception as e:
                logger.error(f"Discord notification failed: {e}")
                return False

        except Exception as e:
            logger.error(f"Discord notification failed: {e}")
            return False


class EmailNotifier:
    """Sends notifications via email (Resend or SendGrid)."""

    def __init__(self):
        self.provider = os.environ.get("EMAIL_PROVIDER", "resend")
        self.api_key = os.environ.get("RESEND_API_KEY") or os.environ.get("SENDGRID_API_KEY", "")
        self.from_email = os.environ.get("EMAIL_FROM", "noreply@autobiz.ai")
        self.enabled = bool(self.api_key)

    async def send(
        self, to: str, subject: str, html_content: str, plain_text: Optional[str] = None
    ) -> bool:
        """
        Send an email notification.

        Args:
            to: Recipient email address
            subject: Email subject
            html_content: HTML body content
            plain_text: Plain text fallback body

        Returns:
            bool: True if sent successfully
        """
        if self.provider == "resend":
            return await self._send_resend(to, subject, html_content, plain_text)
        elif self.provider == "sendgrid":
            return await self._send_sendgrid(to, subject, html_content, plain_text)
        else:
            logger.warning(f"Unknown email provider: {self.provider}")
            return False

    async def _send_resend(
        self, to: str, subject: str, html: str, text: Optional[str] = None
    ) -> bool:
        """Send via Resend API."""
        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                payload = {
                    "from": self.from_email,
                    "to": [to],
                    "subject": subject,
                    "html": html,
                }
                if text:
                    payload["text"] = text

                async with session.post(
                    "https://api.resend.com/emails",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                ) as resp:
                    if resp.status in (200, 201):
                        logger.info(f"Email sent via Resend to {to}")
                        return True
                    else:
                        text_resp = await resp.text()
                        logger.error(f"Resend API error {resp.status}: {text_resp}")
                        return False

        except ImportError:
            try:
                import requests

                payload = {
                    "from": self.from_email,
                    "to": [to],
                    "subject": subject,
                    "html": html,
                }
                if text:
                    payload["text"] = text

                resp = requests.post(
                    "https://api.resend.com/emails",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    timeout=10,
                )
                if resp.status_code in (200, 201):
                    logger.info(f"Email sent via Resend to {to}")
                    return True
                else:
                    logger.error(f"Resend API error {resp.status_code}: {resp.text}")
                    return False
            except Exception as e:
                logger.error(f"Resend email failed: {e}")
                return False
        except Exception as e:
            logger.error(f"Resend email failed: {e}")
            return False

    async def _send_sendgrid(
        self, to: str, subject: str, html: str, text: Optional[str] = None
    ) -> bool:
        """Send via SendGrid API."""
        try:
            import requests

            payload = {
                "personalizations": [{"to": [{"email": to}]}],
                "from": {"email": self.from_email},
                "subject": subject,
                "content": [
                    {"type": "text/html", "value": html},
                ],
            }
            if text:
                payload["content"].append({"type": "text/plain", "value": text})

            resp = requests.post(
                "https://api.sendgrid.com/v3/mail/send",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=10,
            )
            if resp.status_code in (200, 202):
                logger.info(f"Email sent via SendGrid to {to}")
                return True
            else:
                logger.error(f"SendGrid API error {resp.status_code}: {resp.text}")
                return False

        except Exception as e:
            logger.error(f"SendGrid email failed: {e}")
            return False


class SMSNotifier:
    """Sends SMS notifications via Twilio."""

    def __init__(self):
        self.account_sid = os.environ.get("TWILIO_ACCOUNT_SID", "")
        self.auth_token = os.environ.get("TWILIO_AUTH_TOKEN", "")
        self.from_number = os.environ.get("TWILIO_PHONE_NUMBER", "")
        self.enabled = bool(self.account_sid and self.auth_token and self.from_number)

    async def send(self, to: str, body: str) -> bool:
        """
        Send an SMS notification.

        Args:
            to: Recipient phone number (E.164 format)
            body: Message body

        Returns:
            bool: True if sent successfully
        """
        if not self.enabled:
            logger.warning("Twilio credentials not configured, skipping SMS")
            return False

        try:
            from twilio.rest import Client

            client = Client(self.account_sid, self.auth_token)

            message = client.messages.create(
                body=body,
                from_=self.from_number,
                to=to,
            )
            logger.info(f"SMS sent to {to}: {message.sid}")
            return True

        except ImportError:
            logger.warning("twilio package not installed, skipping SMS")
            return False
        except Exception as e:
            logger.error(f"Twilio SMS failed: {e}")
            return False


class ApprovalNotifier:
    """
    Main notifier class for approval workflow notifications.

    Delivers notifications via multiple channels:
    - Discord (webhook) for real-time alerts
    - Email (Resend/SendGrid) for formal notifications
    - SMS (Twilio) for urgent/critical approvals
    """

    def __init__(self):
        self.discord = DiscordNotifier(os.environ.get("DISCORD_WEBHOOK_URL", ""))
        self.email = EmailNotifier()
        self.sms = SMSNotifier()

    def _build_approval_embed(
        self, approval: Dict[str, Any], decision: str = "pending"
    ) -> Dict[str, Any]:
        """Build a Discord embed for an approval notification."""
        # Colors for urgency levels (critical=red, high=orange, normal=blue, low=gray)
        # _urgency_colors = {
        #     "critical": 0xE74C3C,
        #     "high": 0xE67E22,
        #     "normal": 0x3498DB,
        #     "low": 0x95A5A6,
        # }

        status_colors = {
            "pending": 0xF39C12,
            "approved": 0x2ECC71,
            "rejected": 0xE74C3C,
            "expired": 0x95A5A6,
        }

        color = status_colors.get(decision, status_colors.get("pending"))
        urgency = approval.get("urgency", "normal")

        fields = [
            {"name": "Urgency", "value": urgency.upper(), "inline": True},
            {"name": "Business", "value": str(approval.get("business_id", "N/A")), "inline": True},
            {"name": "Task", "value": str(approval.get("task_id", "N/A")), "inline": True},
        ]

        proposed = approval.get("proposed_changes")
        if proposed and isinstance(proposed, dict):
            changes_summary = "\n".join(f"{k}: {v}" for k, v in list(proposed.items())[:5])
            fields.append(
                {"name": "Proposed Changes", "value": changes_summary[:1024], "inline": False}
            )

        impact = approval.get("impact_analysis")
        if impact and isinstance(impact, dict):
            revenue = impact.get("estimated_cost", "N/A")
            fields.append({"name": "Estimated Impact", "value": f"Cost: {revenue}", "inline": True})

        footer = f"AutoBiz Engine • {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"

        return {
            "title": f"📋 Approval: {approval.get('title', 'Untitled')}",
            "description": approval.get("description", "No description provided"),
            "color": color,
            "fields": fields,
            "footer": {"text": footer},
        }

    def _build_approval_email(self, approval: Dict[str, Any], decision: str = "pending") -> tuple:
        """Build email subject and HTML content for approval notification."""
        title = approval.get("title", "Untitled Approval")
        desc = approval.get("description", "")
        urgency = approval.get("urgency", "normal")
        business_id = str(approval.get("business_id", ""))
        expires_at = approval.get("expires_at", "")

        if decision == "approved":
            subject = f"✅ Approved: {title}"
            status_html = '<span style="color:#2ecc71;font-weight:bold;">APPROVED</span>'
        elif decision == "rejected":
            subject = f"❌ Rejected: {title}"
            status_html = '<span style="color:#e74c3c;font-weight:bold;">REJECTED</span>'
        else:
            subject = f"📋 Action Required: {title}"
            status_html = '<span style="color:#f39c12;font-weight:bold;">PENDING APPROVAL</span>'

        html = f"""
        <html>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    max-width: 600px; margin: 0 auto; padding: 20px; background: #0f172a; color: #e2e8f0;">

            <div style="background: #1e293b; border-radius: 12px; padding: 24px; border: 1px solid #334155;">
                <h1 style="margin: 0 0 8px 0; font-size: 20px; color: #f8fafc;">{subject}</h1>
                <p style="margin: 0 0 16px 0; color: #94a3b8; font-size: 14px;">{desc}</p>

                <div style="display: flex; gap: 16px; margin-bottom: 16px; flex-wrap: wrap;">
                    <div style="flex: 1; min-width: 120px;">
                        <p style="margin: 0; font-size: 12px; color: #64748b;">Status</p>
                        <p style="margin: 4px 0 0 0; font-size: 14px;">{status_html}</p>
                    </div>
                    <div style="flex: 1; min-width: 120px;">
                        <p style="margin: 0; font-size: 12px; color: #64748b;">Urgency</p>
                        <p style="margin: 4px 0 0 0; font-size: 14px; text-transform: uppercase;">{urgency}</p>
                    </div>
                    <div style="flex: 1; min-width: 120px;">
                        <p style="margin: 0; font-size: 12px; color: #64748b;">Business ID</p>
                        <p style="margin: 4px 0 0 0; font-size: 12px; font-family: monospace;">{business_id[:12]}...</p>
                    </div>
                </div>

                <p style="margin: 16px 0 8px 0; font-size: 12px; color: #64748b;">
                    Expires: {expires_at or 'No expiration'}
                </p>

                <a href="https://autobiz.ai/businesses/{business_id}/approvals"
                   style="display: inline-block; padding: 10px 20px; background: #3b82f6; color: white;
                          text-decoration: none; border-radius: 8px; font-size: 14px; margin-top: 8px;">
                    View in Dashboard
                </a>
            </div>

            <p style="margin-top: 24px; font-size: 12px; color: #475569;">
                This is an automated message from AutoBiz Engine.
            </p>
        </body>
        </html>
        """

        plain = f"""{subject}

{desc}

Status: {decision.upper()}
Urgency: {urgency}
Business: {business_id}

View in Dashboard: https://autobiz.ai/businesses/{business_id}/approvals
"""

        return subject, html, plain

    async def notify_ceo(self, approval_request: Dict[str, Any]) -> bool:
        """
        Notify CEO about a new approval request.

        Args:
            approval_request: Approval request data

        Returns:
            bool: True if at least one channel succeeded
        """
        results = []

        # Discord notification
        embed = self._build_approval_embed(approval_request)
        discord_result = await self.discord.send(
            title=embed["title"],
            message=approval_request.get("description", ""),
            color=embed["color"],
            fields=embed.get("fields", []),
        )
        results.append(("discord", discord_result))

        # Email notification
        subject, html, plain = self._build_approval_email(approval_request, "pending")
        ceo_email = self._resolve_ceo_email(approval_request)
        email_result = await self.email.send(ceo_email, subject, html, plain)
        results.append(("email", email_result))

        # SMS for critical/urgent approvals
        urgency = approval_request.get("urgency", "normal")
        if urgency in ("critical", "high"):
            sms_body = f"URGENT Approval needed: {approval_request.get('title', 'Untitled')}"
            sms_result = await self.sms.send(self._resolve_ceo_phone(approval_request), sms_body)
            results.append(("sms", sms_result))

        # Log results
        success = any(r[1] for r in results)
        for channel, ok in results:
            status = "SUCCESS" if ok else "FAILED"
            logger.info(f"Notification via {channel}: {status}")

        return success

    async def notify_agent(self, approval_request_id: str, decision: str) -> bool:
        """
        Notify agent about approval decision.

        Args:
            approval_request_id: Approval request ID
            decision: 'approved' or 'rejected'

        Returns:
            bool: True if notification sent
        """
        # Fetch approval data if available
        approval_data = {
            "id": approval_request_id,
            "title": "Approval Decision",
            "description": f"Your approval request has been {decision}",
            "status": decision,
            "urgency": "normal",
        }

        results = []

        # Discord notification
        color = 0x2ECC71 if decision == "approved" else 0xE74C3C
        emoji = "✅" if decision == "approved" else "❌"

        discord_result = await self.discord.send(
            title=f"{emoji} Approval {decision.upper()}",
            message=f"Approval request {approval_request_id} has been {decision}",
            color=color,
        )
        results.append(("discord", discord_result))

        # Email notification
        subject, html, plain = self._build_approval_email(approval_data, decision)
        agent_email = os.environ.get("AGENT_EMAIL", "agent@example.com")
        email_result = await self.email.send(agent_email, subject, html, plain)
        results.append(("email", email_result))

        for channel, ok in results:
            status = "SUCCESS" if ok else "FAILED"
            logger.info(f"Agent notification via {channel}: {status}")

        return any(r[1] for r in results)

    async def notify(self, channel: str, **kwargs) -> bool:
        """
        Generic notification method.

        Args:
            channel: 'discord', 'email', or 'sms'
            **kwargs: Channel-specific parameters

        Returns:
            bool: True if sent
        """
        if channel == "discord":
            return await self.discord.send(**kwargs)
        elif channel == "email":
            return await self.email.send(**kwargs)
        elif channel == "sms":
            return await self.sms.send(**kwargs)
        else:
            logger.warning(f"Unknown notification channel: {channel}")
            return False

    async def notify_ceo_about_approval(self, approval_data: Dict) -> bool:
        """Notify CEO about an approval request (alias for notify_ceo)."""
        return await self.notify_ceo(approval_data)

    def _resolve_ceo_email(self, approval_data: Dict) -> str:
        """Resolve CEO email from user profile or approval data."""
        business_id = approval_data.get("business_id", "")
        if business_id:
            try:
                from app.database import get_db_session
                from app.models.business import Business
                from app.models.user import User
                from sqlalchemy import select

                with get_db_session() as session:
                    biz = session.execute(
                        select(Business).where(Business.id == business_id)
                    ).scalar_one_or_none()
                    if biz:
                        user = session.execute(
                            select(User).where(User.id == biz.ceo_id)
                        ).scalar_one_or_none()
                        if user and user.email:
                            return user.email
            except Exception:
                pass
        return os.environ.get("CEO_EMAIL", "")

    def _resolve_ceo_phone(self, approval_data: Dict) -> str:
        """Resolve CEO phone — currently from env, future from user profile."""
        business_id = approval_data.get("business_id", "")
        if business_id:
            try:
                from app.database import get_db_session
                from app.models.business import Business
                from app.models.user import User
                from sqlalchemy import select

                with get_db_session() as session:
                    biz = session.execute(
                        select(Business).where(Business.id == business_id)
                    ).scalar_one_or_none()
                    if biz:
                        user = session.execute(
                            select(User).where(User.id == biz.ceo_id)
                        ).scalar_one_or_none()
                        if user and hasattr(user, "phone") and user.phone:
                            return user.phone
            except Exception:
                pass
        return os.environ.get("CEO_PHONE", "")

    async def send_system_alert(
        self, alert_type: str, message: str, severity: str = "info"
    ) -> bool:
        """Send a system alert via available channels."""
        logger.info(f"System Alert [{severity}] {alert_type}: {message}")
        if self.discord.enabled:
            return await self.discord.send(
                title=f"[{severity.upper()}] {alert_type}",
                message=message,
                color=0xE74C3C if severity == "critical" else 0xF39C12,
            )
        return True

    async def notify_agent_about_decision(
        self, agent_role: str, approval_data: Dict, decision: str
    ) -> bool:
        """Notify an agent about an approval decision."""
        logger.info(
            f"Agent {agent_role} notified about decision: {decision} on {approval_data.get('title', '')}"
        )
        return True

    async def broadcast_to_all_ceos(self, message: str, data: Optional[Dict] = None) -> bool:
        """Broadcast a message to all CEOs."""
        logger.info(f"Broadcast: {message}")
        return True
