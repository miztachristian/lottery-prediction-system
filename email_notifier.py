#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Email Notification System for Lottery Predictions
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Dict, Optional
from datetime import datetime
import os


class EmailNotifier:
    """Send prediction results via email."""

    def __init__(self, smtp_server: str, smtp_port: int, sender_email: str,
                 sender_password: str, use_tls: bool = True):
        """
        Args:
            smtp_server: SMTP server address (e.g., smtp.gmail.com)
            smtp_port: SMTP port (e.g., 587 for TLS)
            sender_email: Sender email address
            sender_password: Sender password (use app-specific password)
            use_tls: Whether to use TLS encryption
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.use_tls = use_tls

    def send_predictions(self, recipient_email: str, tickets: List[Dict],
                        game: str = "xl", subject: Optional[str] = None,
                        attach_csv: Optional[str] = None) -> bool:
        """
        Send lottery predictions via email.

        Args:
            recipient_email: Recipient email address
            tickets: List of ticket dictionaries with main numbers and reserve
            game: Game type ("xl" or "lotto")
            subject: Email subject (optional)
            attach_csv: Path to CSV file to attach (optional)

        Returns:
            True if email sent successfully
        """
        try:
            # Create email
            msg = MIMEMultipart('alternative')
            msg['From'] = self.sender_email
            msg['To'] = recipient_email
            msg['Subject'] = subject or f"🎯 Lottery Predictions - {datetime.now().strftime('%Y-%m-%d')}"

            # Generate email body
            html_body = self._generate_html_body(tickets, game)
            text_body = self._generate_text_body(tickets, game)

            # Attach both plain text and HTML versions
            msg.attach(MIMEText(text_body, 'plain'))
            msg.attach(MIMEText(html_body, 'html'))

            # Attach CSV if provided
            if attach_csv and os.path.exists(attach_csv):
                with open(attach_csv, 'rb') as f:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', 
                                  f'attachment; filename={os.path.basename(attach_csv)}')
                    msg.attach(part)

            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            if self.use_tls:
                server.starttls()
            server.login(self.sender_email, self.sender_password)
            server.send_message(msg)
            server.quit()

            print(f"✅ Predictions sent to {recipient_email}")
            return True

        except Exception as e:
            print(f"❌ Error sending email: {e}")
            return False

    def _generate_html_body(self, tickets: List[Dict], game: str) -> str:
        """Generate HTML email body."""
        game_name = "Lotto XL" if game == "xl" else "Lotto"
        now = datetime.now().strftime('%A, %B %d, %Y at %I:%M %p')
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px; }}
        .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 0 20px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 20px; margin-bottom: 30px; }}
        .header h1 {{ margin: 0; font-size: 28px; }}
        .header p {{ color: #7f8c8d; margin-top: 10px; }}
        .stats {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; margin-bottom: 30px; }}
        .stat-box {{ background: #ecf0f1; padding: 15px; border-radius: 8px; text-align: center; }}
        .stat-box .number {{ font-size: 32px; font-weight: bold; color: #3498db; }}
        .stat-box .label {{ color: #7f8c8d; margin-top: 5px; font-size: 14px; }}
        .ticket-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; margin-bottom: 30px; }}
        .ticket {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.2); }}
        .ticket-header {{ color: white; font-weight: bold; margin-bottom: 15px; font-size: 16px; display: flex; justify-content: space-between; align-items: center; }}
        .ticket-type {{ background: rgba(255,255,255,0.3); padding: 4px 12px; border-radius: 20px; font-size: 12px; }}
        .numbers {{ display: flex; gap: 8px; flex-wrap: wrap; }}
        .ball {{ background: white; color: #667eea; width: 45px; height: 45px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 18px; box-shadow: 0 2px 8px rgba(0,0,0,0.2); }}
        .ball.reserve {{ background: #f39c12; color: white; }}
        .footer {{ text-align: center; color: #7f8c8d; margin-top: 30px; padding-top: 20px; border-top: 2px solid #ecf0f1; font-size: 14px; }}
        .prize-focus {{ background: #2ecc71; color: white; padding: 15px; border-radius: 8px; text-align: center; margin-bottom: 30px; }}
        .prize-focus h3 {{ margin: 0 0 10px 0; }}
        @media (max-width: 768px) {{
            .ticket-grid {{ grid-template-columns: 1fr; }}
            .stats {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 Netherlands {game_name} Predictions</h1>
            <p>Generated on {now}</p>
        </div>
        
        <div class="prize-focus">
            <h3>🏆 TARGET: €100,000+ PRIZE</h3>
            <p>Optimized for Tier 1 (6+1) and Tier 2 (6+0) wins</p>
        </div>
        
        <div class="stats">
            <div class="stat-box">
                <div class="number">{len(tickets)}</div>
                <div class="label">Total Tickets</div>
            </div>
            <div class="stat-box">
                <div class="number">{len([t for t in tickets if t.get('type') == 'coverage'])}</div>
                <div class="label">Coverage</div>
            </div>
            <div class="stat-box">
                <div class="number">{len([t for t in tickets if t.get('type') == 'convergence'])}</div>
                <div class="label">Convergence</div>
            </div>
        </div>
        
        <div class="ticket-grid">
"""

        # Add tickets
        for i, ticket in enumerate(tickets, 1):
            ticket_type = ticket.get('type', 'coverage').capitalize()
            main_numbers = ticket['main_numbers']
            reserve = ticket['reserve']
            
            html += f"""
            <div class="ticket">
                <div class="ticket-header">
                    <span>Ticket #{i}</span>
                    <span class="ticket-type">{ticket_type}</span>
                </div>
                <div class="numbers">
"""
            
            # Main numbers
            for num in sorted(main_numbers):
                html += f'                    <div class="ball">{num}</div>\n'
            
            # Reserve number
            html += f'                    <div class="ball reserve">★{reserve}</div>\n'
            
            html += """
                </div>
            </div>
"""

        html += f"""
        </div>
        
        <div class="footer">
            <p><strong>Strategy:</strong> Anchor-Cluster Framework with Hot/Cold Analysis</p>
            <p><strong>Model:</strong> Transformer-based Sequence Prediction</p>
            <p><strong>Good luck! 🍀</strong></p>
            <p style="font-size: 12px; color: #95a5a6; margin-top: 15px;">
                This is an AI-powered prediction system. Lottery outcomes are random. Play responsibly.
            </p>
        </div>
    </div>
</body>
</html>
"""
        return html

    def _generate_text_body(self, tickets: List[Dict], game: str) -> str:
        """Generate plain text email body."""
        game_name = "Lotto XL" if game == "xl" else "Lotto"
        now = datetime.now().strftime('%A, %B %d, %Y at %I:%M %p')
        
        text = f"""
{'='*70}
    NETHERLANDS {game_name.upper()} PREDICTIONS
{'='*70}

Generated: {now}

TARGET: €100,000+ PRIZE
Optimized for Tier 1 (6+1) and Tier 2 (6+0) wins

Total Tickets: {len(tickets)}
- Coverage: {len([t for t in tickets if t.get('type') == 'coverage'])}
- Convergence: {len([t for t in tickets if t.get('type') == 'convergence'])}

{'='*70}
PREDICTED TICKETS
{'='*70}

"""
        
        for i, ticket in enumerate(tickets, 1):
            ticket_type = ticket.get('type', 'coverage').upper()
            main_numbers = sorted(ticket['main_numbers'])
            reserve = ticket['reserve']
            
            text += f"\nTicket #{i} ({ticket_type})\n"
            text += f"Main:    {' - '.join(f'{n:2d}' for n in main_numbers)}\n"
            text += f"Reserve: ★{reserve}\n"
        
        text += f"""
{'='*70}
STRATEGY NOTES
{'='*70}

✓ Anchor-Cluster Framework
✓ Dynamic Hot/Cold Number Analysis  
✓ Transformer-based ML Predictions
✓ Constraint Enforcement (3 odd/3 even, spread)
✓ Optimized for High-Tier Wins

Good luck! 🍀

---
This is an AI-powered prediction system.
Lottery outcomes are random. Play responsibly.
"""
        
        return text


def send_test_email(config_path: str = "config.yaml") -> bool:
    """Send a test email with sample predictions."""
    import yaml
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    email_config = config['email']
    
    if not email_config['enabled']:
        print("Email is disabled in config")
        return False
    
    notifier = EmailNotifier(
        smtp_server=email_config['smtp_server'],
        smtp_port=email_config['smtp_port'],
        sender_email=email_config['sender_email'],
        sender_password=email_config['sender_password'],
        use_tls=email_config['use_tls']
    )
    
    # Sample tickets
    sample_tickets = [
        {'main_numbers': {9, 10, 20, 28, 35, 42}, 'reserve': 15, 'type': 'coverage'},
        {'main_numbers': {3, 12, 21, 29, 38, 44}, 'reserve': 7, 'type': 'coverage'},
        {'main_numbers': {5, 16, 23, 32, 39, 45}, 'reserve': 11, 'type': 'convergence'},
    ]
    
    return notifier.send_predictions(
        recipient_email=email_config['recipient_email'],
        tickets=sample_tickets,
        game='xl',
        subject=email_config['subject'].format(date=datetime.now().strftime('%Y-%m-%d'))
    )


if __name__ == "__main__":
    print("Testing email notification system...")
    success = send_test_email()
    if success:
        print("✅ Test email sent successfully!")
    else:
        print("❌ Failed to send test email")
