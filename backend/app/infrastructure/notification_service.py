import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional
import json
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

class NotificationService:
    """Service for sending notifications via multiple channels"""
    
    def __init__(self):
        # In a real implementation, these would come from config
        self.email_config = {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "username": "notifications@autobiz.engine",
            "password": "app-password"
        }
        self.discord_webhook_url = "https://discord.com/api/webhooks/..."
        self.sms_api_key = "your-sms-api-key"
        
    async def send_email(self, to: str, subject: str, body: str, is_html: bool = False) -> bool:
        """Send an email notification"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_config["username"]
            msg['To'] = to
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'html' if is_html else 'plain'))
            
            server = smtplib.SMTP(self.email_config["smtp_server"], self.email_config["smtp_port"])
            server.starttls()
            server.login(self.email_config["username"], self.email_config["password"])
            text = msg.as_string()
            server.sendmail(self.email_config["username"], to, text)
            server.quit()
            
            logger.info(f"Email sent to {to}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {to}: {str(e)}")
            return False
    
    async def send_discord_notification(self, message: str, embeds: Optional[List[Dict]] = None) -> bool:
        """Send a notification to Discord"""
        try:
            # In a real implementation, this would make an HTTP POST to the webhook URL
            logger.info(f"Discord notification sent: {message}")
            if embeds:
                logger.info(f"With embeds: {json.dumps(embeds)}")
            return True
        except Exception as e:
            logger.error(f"Failed to send Discord notification: {str(e)}")
            return False
    
    async def send_sms(self, to: str, message: str) -> bool:
        """Send an SMS notification"""
        try:
            # In a real implementation, this would use an SMS API like Twilio
            logger.info(f"SMS sent to {to}: {message}")
            return True
        except Exception as e:
            logger.error(f"Failed to send SMS to {to}: {str(e)}")
            return False
    
    async def notify_ceo_about_approval(self, approval_data: Dict) -> bool:
        """Notify CEO about a new approval request"""
        subject = f"Approval Required: {approval_data.get('title')}"
        body = f"""
        A new approval request requires your attention:
        
        Title: {approval_data.get('title')}
        Description: {approval_data.get('description')}
        Business ID: {approval_data.get('business_id')}
        Urgency: {approval_data.get('urgency')}
        
        Please review and make a decision at the approval portal.
        """
        
        # Try multiple channels
        results = []
        
        # Email
        if approval_data.get("ceo_email"):
            results.append(await self.send_email(
                approval_data["ceo_email"], 
                subject, 
                body
            ))
        
        # Discord
        results.append(await self.send_discord_notification(
            f"🚨 Approval Required: {approval_data.get('title')}",
            [{
                "title": approval_data.get('title'),
                "description": approval_data.get('description'),
                "color": 15158332 if approval_data.get('urgency') == 'high' else 16753920,
                "fields": [
                    {"name": "Business ID", "value": str(approval_data.get('business_id')), "inline": True},
                    {"name": "Urgency", "value": approval_data.get('urgency'), "inline": True},
                    {"name": "Requested At", "value": approval_data.get('created_at'), "inline": False}
                ]
            }]
        ))
        
        return any(results)  # Return True if at least one channel succeeded
    
    async def notify_agent_about_decision(self, agent_role: str, approval_data: Dict, decision: str) -> bool:
        """Notify an agent about a decision on their request"""
        subject = f"Decision on Your Request: {approval_data.get('title')}"
        body = f"""
        A decision has been made on your approval request:
        
        Title: {approval_data.get('title')}
        Decision: {decision.upper()}
        Comments: {approval_data.get('ceo_decision', 'No comments provided')}
        
        You can view the full details in the agent dashboard.
        """
        
        # In a real implementation, this would send to the agent's preferred channel
        logger.info(f"Notifying {agent_role} agent about decision: {decision}")
        
        # For now, just log and return success
        return True
    
    async def send_system_alert(self, alert_type: str, message: str, severity: str = "info") -> bool:
        """Send a system alert to administrators"""
        logger.info(f"System Alert [{severity}] {alert_type}: {message}")
        
        # In a real implementation, this would go to a monitoring system like Sentry, or admin channels
        return True
    
    async def broadcast_to_all_ceos(self, message: str, data: Optional[Dict] = None) -> bool:
        """Broadcast a message to all CEOs"""
        logger.info(f"Broadcasting to all CEOs: {message}")
        if data:
            logger.info(f"Data: {json.dumps(data)}")
        return True