import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending notifications via multiple channels"""

    def __init__(self):
        from app.config import settings

        self.email_config = {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "username": settings.RESEND_API_KEY or "",
            "password": settings.SENDGRID_API_KEY or "",
        }
        self.discord_webhook_url = settings.DISCORD_WEBHOOK_URL or ""
        self._http_client = httpx.AsyncClient(timeout=10)

    async def send_email(self, to: str, subject: str, body: str, is_html: bool = False) -> bool:
        try:
            msg = MIMEMultipart()
            msg["From"] = self.email_config["username"] or "noreply@autobiz.ai"
            msg["To"] = to
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "html" if is_html else "plain"))

            if self.email_config["username"] and self.email_config["password"]:
                server = smtplib.SMTP(
                    self.email_config["smtp_server"], self.email_config["smtp_port"]
                )
                server.starttls()
                server.login(self.email_config["username"], self.email_config["password"])
                server.sendmail(self.email_config["username"], to, msg.as_string())
                server.quit()
                logger.info(f"Email sent to {to}")
                return True

            logger.info(f"[Email] Would send to {to}: {subject}")
            return True
        except Exception as e:
            logger.error(f"Email failed: {e}")
            return False

    async def send_discord_notification(
        self, message: str, embeds: Optional[List[Dict]] = None
    ) -> bool:
        if not self.discord_webhook_url:
            logger.info(f"[Discord] Would notify: {message}")
            return True
        try:
            payload = {"content": message}
            if embeds:
                payload["embeds"] = embeds
            resp = await self._http_client.post(self.discord_webhook_url, json=payload)
            success = resp.status_code in (200, 204)
            logger.info(
                f"Discord notification {'sent' if success else f'failed ({resp.status_code})'}"
            )
            return success
        except Exception as e:
            logger.error(f"Discord notification failed: {e}")
            return False

    async def send_sms(self, to: str, message: str) -> bool:
        logger.info(f"[SMS] Would send to {to}: {message}")
        return True

    async def notify_ceo_about_approval(self, approval_data: Dict) -> bool:
        results = []

        if approval_data.get("ceo_email"):
            results.append(
                await self.send_email(
                    approval_data["ceo_email"],
                    f"Approval Required: {approval_data.get('title')}",
                    f"Title: {approval_data.get('title')}\nDescription: {approval_data.get('description')}\nBusiness: {approval_data.get('business_id')}\nUrgency: {approval_data.get('urgency')}",
                )
            )

        results.append(
            await self.send_discord_notification(
                f"Approval Required: {approval_data.get('title')}",
                [
                    {
                        "title": approval_data.get("title"),
                        "description": approval_data.get("description", ""),
                        "color": 15158332 if approval_data.get("urgency") == "high" else 16753920,
                        "fields": [
                            {
                                "name": "Business ID",
                                "value": str(approval_data.get("business_id", "")),
                                "inline": True,
                            },
                            {
                                "name": "Urgency",
                                "value": approval_data.get("urgency", "normal"),
                                "inline": True,
                            },
                        ],
                    }
                ],
            )
        )

        return any(results)

    async def notify_agent_about_decision(
        self, agent_role: str, approval_data: Dict, decision: str
    ) -> bool:
        logger.info(
            f"Agent {agent_role} notified about decision: {decision} on {approval_data.get('title', '')}"
        )
        return True

    async def send_system_alert(
        self, alert_type: str, message: str, severity: str = "info"
    ) -> bool:
        logger.info(f"System Alert [{severity}] {alert_type}: {message}")
        if self.discord_webhook_url:
            await self.send_discord_notification(f"[{severity.upper()}] {alert_type}: {message}")
        return True

    async def broadcast_to_all_ceos(self, message: str, data: Optional[Dict] = None) -> bool:
        logger.info(f"Broadcast: {message}")
        return True
