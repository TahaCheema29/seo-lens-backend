from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import os

from src.config.logger_config import setup_logger
from src.config.settings import settings

logger = setup_logger(__name__)


class EmailServiceError(Exception):
    """Base exception for email service errors"""
    pass


class EmailProvider(ABC):
    """Abstract base class for email providers"""

    @abstractmethod
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
    ) -> bool:
        """Send an email"""
        pass


class SendGridProvider(EmailProvider):
    """SendGrid email provider"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("SENDGRID_API_KEY")
        # Never log raw API keys.
        if self.api_key:
            logger.info("SendGrid API key configured")
        else:
            logger.info("SendGrid API key not configured")
        self.from_email = os.getenv("SENDGRID_FROM_EMAIL", "noreply@seo-lens.com")
        self.from_name = os.getenv("SENDGRID_FROM_NAME", "SEO Lens")

        if not self.api_key:
            logger.warning("SendGrid API key not configured")

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
    ) -> bool:
        """Send email using SendGrid"""
        try:
            # Import here to avoid dependency if not using SendGrid
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail, Email, Content, HtmlContent

            if not self.api_key:
                logger.error("SendGrid API key not configured")
                return False

            sg = SendGridAPIClient(self.api_key)
            logger.info(f"SendGrid API key configured: {self.api_key[:10]}...")

            message = Mail(
                from_email=Email(from_email or self.from_email, from_name or self.from_name),
                to_emails=to_email,
                subject=subject,
                html_content=html_content,
            )

            if text_content:
                message.add_content(Content("text/plain", text_content))

            response = sg.send(message)

            if response.status_code in [200, 201, 202]:
                logger.info(f"Email sent successfully to {to_email}")
                return True
            else:
                logger.error(f"SendGrid error: {response.status_code} - {response.body}")
                return False

        except Exception as e:
            logger.error(f"Error sending email via SendGrid: {e}", exc_info=True)
            return False


class ConsoleEmailProvider(EmailProvider):
    """Console email provider for development/testing"""

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
    ) -> bool:
        """Log email to console instead of sending"""
        logger.info("=" * 60)
        logger.info("EMAIL NOTIFICATION (Console Mode)")
        logger.info("=" * 60)
        logger.info(f"To: {to_email}")
        logger.info(f"From: {from_name} <{from_email or 'noreply@seo-lens.com'}>")
        logger.info(f"Subject: {subject}")
        logger.info("-" * 60)
        logger.info(text_content or html_content[:500])
        logger.info("=" * 60)
        return True


class EmailService:
    """Email service for sending SEO reports"""

    def __init__(self):
        self.logger = logger
        self.provider = self._get_provider()

    def _get_provider(self) -> EmailProvider:
        """Get the configured email provider"""
        provider_type = os.getenv("EMAIL_PROVIDER", "console").lower()
        logger.info("EMAIL_PROVIDER: %s", provider_type)

        if provider_type == "sendgrid":
            return SendGridProvider()
        elif provider_type == "console":
            return ConsoleEmailProvider()
        else:
            logger.warning(f"Unknown email provider: {provider_type}, using console")
            return ConsoleEmailProvider()

    async def send_seo_report_email(
        self,
        to_email: str,
        user_name: str,
        report_data: Dict[str, Any],
        repository: Optional[str] = None,
        pr_number: Optional[int] = None,
        branch: Optional[str] = None,
    ) -> bool:
        """
        Send SEO analysis report via email

        Args:
            to_email: Recipient email address
            user_name: User's name for personalization
            report_data: SEO report data including score, url_results, etc.
            repository: Optional repository name
            pr_number: Optional PR number
            branch: Optional branch name

        Returns:
            True if sent successfully
        """
        try:
            subject = self._generate_subject(report_data, repository, pr_number)
            html_content = self._generate_html_template(
                user_name=user_name,
                report_data=report_data,
                repository=repository,
                pr_number=pr_number,
                branch=branch,
            )
            text_content = self._generate_text_template(
                user_name=user_name,
                report_data=report_data,
                repository=repository,
                pr_number=pr_number,
                branch=branch,
            )

            return await self.provider.send_email(
                to_email=to_email,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
            )

        except Exception as e:
            self.logger.error(f"Error sending SEO report email: {e}", exc_info=True)
            return False

    def _generate_subject(
        self,
        report_data: Dict[str, Any],
        repository: Optional[str] = None,
        pr_number: Optional[int] = None,
    ) -> str:
        """Generate email subject line"""
        score = report_data.get("score", 0)
        url = report_data.get("target_url", "Unknown URL")

        # Score emoji
        if score >= 80:
            emoji = "✅"
        elif score >= 60:
            emoji = "⚠️"
        else:
            emoji = "❌"

        if repository and pr_number:
            return f"{emoji} SEO Report: {repository} PR #{pr_number} - Score: {score}/100"
        else:
            return f"{emoji} SEO Report: {url} - Score: {score}/100"

    def _generate_html_template(
        self,
        user_name: str,
        report_data: Dict[str, Any],
        repository: Optional[str] = None,
        pr_number: Optional[int] = None,
        branch: Optional[str] = None,
    ) -> str:
        """Generate HTML email template"""
        score = report_data.get("score", 0)
        url = report_data.get("target_url", "Unknown URL")
        pages_analyzed = report_data.get("pages_analyzed", 0)

        # Score color
        if score >= 80:
            score_color = "#22c55e"  # Green
            score_label = "Good"
        elif score >= 60:
            score_color = "#eab308"  # Yellow
            score_label = "Needs Improvement"
        else:
            score_color = "#ef4444"  # Red
            score_label = "Poor"

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>SEO Analysis Report</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    background-color: white;
                    border-radius: 8px;
                    padding: 30px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                    padding-bottom: 20px;
                    border-bottom: 2px solid #e5e7eb;
                }}
                .logo {{
                    font-size: 24px;
                    font-weight: bold;
                    color: #4f46e5;
                    margin-bottom: 10px;
                }}
                .score-box {{
                    background-color: {score_color};
                    color: white;
                    border-radius: 12px;
                    padding: 20px;
                    text-align: center;
                    margin: 20px 0;
                }}
                .score-value {{
                    font-size: 48px;
                    font-weight: bold;
                }}
                .score-label {{
                    font-size: 18px;
                    opacity: 0.9;
                }}
                .details {{
                    background-color: #f9fafb;
                    border-radius: 8px;
                    padding: 20px;
                    margin: 20px 0;
                }}
                .detail-row {{
                    display: flex;
                    justify-content: space-between;
                    padding: 8px 0;
                    border-bottom: 1px solid #e5e7eb;
                }}
                .detail-row:last-child {{
                    border-bottom: none;
                }}
                .cta-button {{
                    display: inline-block;
                    background-color: #4f46e5;
                    color: white;
                    text-decoration: none;
                    padding: 12px 30px;
                    border-radius: 6px;
                    margin: 20px 0;
                    font-weight: 600;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #e5e7eb;
                    font-size: 12px;
                    color: #6b7280;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">🔍 SEO Lens</div>
                    <h1>Analysis Complete</h1>
                </div>

                <p>Hi {user_name or "there"},</p>

                <p>Your SEO analysis is complete! Here are the results:</p>

                <div class="score-box">
                    <div class="score-value">{score}/100</div>
                    <div class="score-label">{score_label}</div>
                </div>

                <div class="details">
                    <div class="detail-row">
                        <span><strong>URL Analyzed:</strong></span>
                        <span>{url}</span>
                    </div>
        """

        if repository:
            html += f"""
                    <div class="detail-row">
                        <span><strong>Repository:</strong></span>
                        <span>{repository}</span>
                    </div>
            """

        if pr_number:
            html += f"""
                    <div class="detail-row">
                        <span><strong>Pull Request:</strong></span>
                        <span>#{pr_number}</span>
                    </div>
            """

        if branch:
            html += f"""
                    <div class="detail-row">
                        <span><strong>Branch:</strong></span>
                        <span>{branch}</span>
                    </div>
            """

        html += f"""
                    <div class="detail-row">
                        <span><strong>Pages Crawled:</strong></span>
                        <span>{pages_analyzed}</span>
                    </div>
                </div>

                <p style="text-align: center;">
                    <a href="#" class="cta-button">View Full Report</a>
                </p>

                <p>This analysis was triggered by a {'Pull Request to your repository' if pr_number else 'CI/CD integration'}.</p>

                <div class="footer">
                    <p>SEO Lens - Automated SEO Analysis</p>
                    <p>You're receiving this because you have CI/CD integration enabled.</p>
                </div>
            </div>
        </body>
        </html>
        """

        return html

    def _generate_text_template(
        self,
        user_name: str,
        report_data: Dict[str, Any],
        repository: Optional[str] = None,
        pr_number: Optional[int] = None,
        branch: Optional[str] = None,
    ) -> str:
        """Generate plain text email template"""
        score = report_data.get("score", 0)
        url = report_data.get("target_url", "Unknown URL")
        pages_analyzed = report_data.get("pages_analyzed", 0)

        text = f"""
SEO Lens - Analysis Complete
============================

Hi {user_name or "there"},

Your SEO analysis is complete!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 OVERALL SCORE: {score}/100
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

URL Analyzed: {url}
"""

        if repository:
            text += f"Repository: {repository}\n"

        if pr_number:
            text += f"Pull Request: #{pr_number}\n"

        if branch:
            text += f"Branch: {branch}\n"

        text += f"""Pages Crawled: {pages_analyzed}

View your full report in the SEO Lens dashboard.

---
This analysis was triggered by a {'Pull Request' if pr_number else 'CI/CD integration'}.
SEO Lens - Automated SEO Analysis
"""

        return text


# Global email service instance
email_service = EmailService()
