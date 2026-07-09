"""
Email Template Service
======================
Generates professional HTML and plain-text bodies for notifications and notices.
"""
from typing import Dict, Any, Tuple


class EmailTemplateService:
    """
    Renders standardized HTML and text email templates.
    """

    def render_notice(self, context: Dict[str, Any]) -> Tuple[str, str]:
        """
        Renders a Traffic Violation Notice email.
        Expected context keys: plate, violation_type, timestamp, location, confidence, evidence_id
        """
        plate = context.get("plate", "UNKNOWN")
        violation_type = context.get("violation_type", "Traffic Violation")
        timestamp = context.get("timestamp", "N/A")
        location = context.get("location", "Unknown Location")
        confidence = context.get("confidence", 0.0)
        evidence_id = context.get("evidence_id", "N/A")

        subject = f"Official Traffic Violation Notice: {violation_type} ({plate})"

        html_body = f"""<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333333; margin: 0; padding: 20px; background-color: #f9f9f9; }}
        .card {{ max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 8px; border: 1px solid #e0e0e0; box-shadow: 0 4px 6px rgba(0,0,0,0.05); overflow: hidden; }}
        .header {{ background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); color: #ffffff; padding: 24px; text-align: center; }}
        .header h1 {{ margin: 0; font-size: 24px; font-weight: 600; letter-spacing: 0.5px; }}
        .content {{ padding: 24px; }}
        .details-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        .details-table th, .details-table td {{ padding: 12px; text-align: left; border-bottom: 1px solid #eeeeee; }}
        .details-table th {{ color: #666666; font-weight: 500; width: 40%; }}
        .details-table td {{ color: #111111; font-weight: 600; }}
        .badge {{ display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 12px; background: #ffebee; color: #c62828; }}
        .footer {{ background: #f5f5f5; padding: 16px; text-align: center; font-size: 12px; color: #777777; border-top: 1px solid #eeeeee; }}
    </style>
</head>
<body>
    <div class="card">
        <div class="header">
            <h1>TRAFFIC VIOLATION NOTICE</h1>
        </div>
        <div class="content">
            <p>Dear Vehicle Owner/Operator,</p>
            <p>An automated traffic enforcement system has detected a violation associated with your vehicle. The details are recorded below:</p>
            
            <table class="details-table">
                <tr>
                    <th>Evidence ID</th>
                    <td><code>{evidence_id}</code></td>
                </tr>
                <tr>
                    <th>Vehicle Plate</th>
                    <td><span class="badge" style="background: #e8f5e9; color: #2e7d32; font-size: 14px; font-family: monospace;">{plate}</span></td>
                </tr>
                <tr>
                    <th>Violation Type</th>
                    <td><span class="badge">{violation_type}</span></td>
                </tr>
                <tr>
                    <th>Date & Time</th>
                    <td>{timestamp}</td>
                </tr>
                <tr>
                    <th>Location</th>
                    <td>{location}</td>
                </tr>
                <tr>
                    <th>Confidence Score</th>
                    <td>{confidence:.2%}</td>
                </tr>
            </table>

            <p>Please find the official original and annotated camera crops attached to this email as evidence package. For inquiries, please contact the traffic support helpline.</p>
        </div>
        <div class="footer">
            This is an automated notification. Please do not reply directly to this email.<br>
            Smart Traffic Enforcement Division &copy; 2026. All rights reserved.
        </div>
    </div>
</body>
</html>
"""

        text_body = f"""=== OFFICIAL TRAFFIC VIOLATION NOTICE ===

Dear Vehicle Owner/Operator,

An automated traffic enforcement system has detected a violation associated with your vehicle.

Details:
- Evidence ID: {evidence_id}
- Vehicle Plate: {plate}
- Violation Type: {violation_type}
- Date & Time: {timestamp}
- Location: {location}
- Confidence Score: {confidence:.2%}

Please review the attached original and annotated crop files for evidence.
For inquiries, please contact the traffic support helpline.

Smart Traffic Enforcement Division © 2026. All rights reserved.
"""
        return html_body, text_body

    def render_test(self, context: Dict[str, Any]) -> Tuple[str, str]:
        """Renders a simple test email."""
        name = context.get("name", "User")
        html_body = f"""<html><body><h2>SMTP Connection Test</h2><p>Hello {name},</p><p>This is a test email asserting connection reuse, secure TLS, and queue delivery status.</p></body></html>"""
        text_body = f"""SMTP Connection Test\n\nHello {name},\n\nThis is a test email asserting connection reuse, secure TLS, and queue delivery status."""
        return html_body, text_body

    def render_notification(self, context: Dict[str, Any]) -> Tuple[str, str]:
        """Renders a system notification."""
        title = context.get("title", "System Notification")
        message = context.get("message", "")
        html_body = f"""<html><body><h2>{title}</h2><p>{message}</p></body></html>"""
        text_body = f"""{title}\n\n{message}"""
        return html_body, text_body

    def render_failure(self, context: Dict[str, Any]) -> Tuple[str, str]:
        """Renders a delivery failure notification."""
        failed_id = context.get("failed_id", "Unknown")
        error_msg = context.get("error_message", "N/A")
        html_body = f"""<html><body><h2>Email Delivery Failure Alert</h2><p>Failed to deliver evidence notice {failed_id}.</p><p>Error detail: {error_msg}</p></body></html>"""
        text_body = f"""Email Delivery Failure Alert\n\nFailed to deliver evidence notice {failed_id}.\n\nError detail: {error_msg}"""
        return html_body, text_body

    def render(self, template_name: str, context: Dict[str, Any]) -> Tuple[str, str]:
        """Generic render selector."""
        name = template_name.lower().strip()
        if name == "notice":
            return self.render_notice(context)
        elif name == "test":
            return self.render_test(context)
        elif name == "notification":
            return self.render_notification(context)
        elif name == "failure":
            return self.render_failure(context)
        else:
            # Fallback
            return self.render_notification(context)


# Singleton instance
email_template_service = EmailTemplateService()
