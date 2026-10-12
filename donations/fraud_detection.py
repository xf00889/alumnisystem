"""
Fraud Detection System for NORSU Alumni Donations
"""

from django.utils import timezone
from django.db.models import Count, Q
from .models import Donation, FraudAlert, BlacklistedEntity
import hashlib
from datetime import timedelta
import re


class FraudDetectionService:
    """Service class for detecting fraudulent donation activities"""
    
    def __init__(self):
        self.risk_thresholds = {
            'rapid_donations_count': 5,  # More than 5 donations in 1 hour
            'rapid_donations_minutes': 60,
            'suspicious_amount_min': 50000,  # Amounts over 50k PHP
            'duplicate_image_threshold': 0.95,  # Image similarity threshold
            'max_daily_donations': 10,  # Max donations per IP per day
        }
    
    def analyze_donation(self, donation, request=None):
        """
        Analyze a donation for potential fraud
        Returns list of fraud alerts created
        """
        alerts = []
        
        # Get request metadata
        ip_address = self.get_client_ip(request) if request else None
        user_agent = request.META.get('HTTP_USER_AGENT', '') if request else ''
        
        # Check blacklisted entities
        blacklist_alert = self.check_blacklisted_entities(donation, ip_address)
        if blacklist_alert:
            alerts.append(self.create_fraud_alert(
                donation, 'blacklisted_user', 'high',
                blacklist_alert, ip_address, user_agent
            ))
        
        # Check for rapid donations
        rapid_alert = self.check_rapid_donations(donation, ip_address)
        if rapid_alert:
            alerts.append(self.create_fraud_alert(
                donation, 'rapid_donations', 'medium',
                rapid_alert, ip_address, user_agent
            ))
        
        # Check suspicious amounts
        amount_alert = self.check_suspicious_amount(donation)
        if amount_alert:
            alerts.append(self.create_fraud_alert(
                donation, 'suspicious_amount', 'medium',
                amount_alert, ip_address, user_agent
            ))
        
        # Check for duplicate payment images (when proof is uploaded)
        if donation.payment_proof:
            duplicate_alert = self.check_duplicate_images(donation)
            if duplicate_alert:
                alerts.append(self.create_fraud_alert(
                    donation, 'duplicate_image', 'high',
                    duplicate_alert, ip_address, user_agent
                ))
        
        # Check unusual location patterns
        location_alert = self.check_unusual_location(donation, ip_address)
        if location_alert:
            alerts.append(self.create_fraud_alert(
                donation, 'unusual_location', 'low',
                location_alert, ip_address, user_agent
            ))
        
        return alerts
    
    def check_blacklisted_entities(self, donation, ip_address):
        """Check if donation involves blacklisted entities"""
        checks = []
        
        # Guest email or verified account email for registered alumni.
        donor_email = donation.donor_email or (donation.donor.email if donation.donor_id else '')
        if donor_email:
            if BlacklistedEntity.objects.filter(
                entity_type='email',
                value__iexact=donor_email,
                is_active=True
            ).filter(Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())).exists():
                checks.append(f"Email {donor_email} is blacklisted")
        
        # Check IP address
        if ip_address:
            if BlacklistedEntity.objects.filter(
                entity_type='ip',
                value=ip_address,
                is_active=True
            ).filter(Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())).exists():
                checks.append(f"IP address {ip_address} is blacklisted")
        
        # Check exact names (an untrusted regex must not be executed).
        if donation.donor_name:
            blacklisted_names = BlacklistedEntity.objects.filter(
                entity_type='name',
                is_active=True,
                value__iexact=donation.donor_name.strip(),
            ).filter(Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now()))
            for blacklisted in blacklisted_names:
                checks.append(f"Name matches listed name: {blacklisted.value}")
        
        return "; ".join(checks) if checks else None
    
    def check_rapid_donations(self, donation, ip_address):
        """Check for rapid multiple donations"""
        time_threshold = timezone.now() - timedelta(
            minutes=self.risk_thresholds['rapid_donations_minutes']
        )
        
        # Check by email
        donor_email = donation.donor_email or (donation.donor.email if donation.donor_id else '')
        if donor_email:
            email_count = Donation.objects.filter(
                Q(donor_email__iexact=donor_email) | Q(donor__email__iexact=donor_email),
                created_at__gte=time_threshold,
                status__in=('pending_verification', 'completed'),
            ).count()
            
            if email_count >= self.risk_thresholds['rapid_donations_count']:
                return f"Email {donor_email} made {email_count} donations in {self.risk_thresholds['rapid_donations_minutes']} minutes"
        
        # Check by IP (if available)
        if ip_address:
            # This would require storing IP addresses with donations
            # For now, we'll implement a basic check
            pass
        
        return None
    
    def check_suspicious_amount(self, donation):
        """Check for suspicious donation amounts"""
        amount = float(donation.amount)
        
        # Very high amounts
        if amount >= self.risk_thresholds['suspicious_amount_min']:
            return f"Unusually high donation amount: ₱{amount:,.2f}"
        
        # A common rounded amount (such as 100 or 1000 PHP) is not fraud
        # evidence by itself. Exclude abandoned unpaid intents when checking
        # repeated transactions, but retain alerts for large amounts.
        recent_donations = Donation.objects.filter(
            amount=donation.amount,
            status__in=['pending_verification', 'completed'],
            created_at__gte=timezone.now() - timedelta(hours=24)
        ).exclude(id=donation.id)
        
        if recent_donations.count() >= 5:
            return f"Multiple donations of same amount (₱{amount}) in 24 hours"
        
        return None
    
    def check_duplicate_images(self, donation):
        """Check for duplicate payment proof images"""
        if not donation.payment_proof:
            return None
        
        try:
            # Simple hash-based duplicate detection
            with donation.payment_proof.open('rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
            
            # Check for exact duplicates
            duplicate_donations = Donation.objects.filter(
                payment_proof__isnull=False
            ).exclude(id=donation.id)
            
            for other_donation in duplicate_donations:
                try:
                    with other_donation.payment_proof.open('rb') as f:
                        other_hash = hashlib.md5(f.read()).hexdigest()
                    
                    if file_hash == other_hash:
                        identifier = other_donation.reference_number or f"Donation #{other_donation.pk}"
                        return f"Identical payment proof image found in {identifier}"
                except:
                    continue
            
        except Exception:
            # A storage/read failure isn't itself evidence of fraud.
            return None
        
        return None
    
    def check_unusual_location(self, donation, ip_address):
        """No geo evidence is available without a trusted IP intelligence service.

        RFC1918 addresses, reverse proxies and local networks are not evidence
        of a fraudulent donation. Do not raise fabricated location alerts.
        """
        return None

    def create_fraud_alert(self, donation, alert_type, severity, description, ip_address, user_agent):
        """Do not create repeated unresolved alerts on re-screening."""
        alert = FraudAlert.objects.filter(
            donation=donation, alert_type=alert_type,
            status__in=('pending', 'investigating'),
        ).first()
        if alert:
            return alert
        return FraudAlert.objects.create(
            donation=donation,
            alert_type=alert_type,
            severity=severity,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={
                'detection_time': timezone.now().isoformat(),
                'thresholds_used': self.risk_thresholds,
            },
        )

    def get_client_ip(self, request):
        """Never trust client-supplied X-Forwarded-For without proxy validation.

        Deployments with a trusted reverse proxy should configure real-IP
        extraction at that proxy, not accept arbitrary request headers here.
        """
        return request.META.get('REMOTE_ADDR') if request else None

    def calculate_risk_score(self, donation):
        """Calculate overall risk score for a donation"""
        alerts = FraudAlert.objects.filter(donation=donation)
        
        score = 0
        severity_weights = {
            'low': 1,
            'medium': 3,
            'high': 5,
            'critical': 10
        }
        
        for alert in alerts:
            score += severity_weights.get(alert.severity, 1)
        
        return min(score, 100)  # Cap at 100
    
    def get_fraud_summary(self, days=30):
        """Get fraud detection summary for the last N days"""
        cutoff_date = timezone.now() - timedelta(days=days)
        
        alerts = FraudAlert.objects.filter(created_at__gte=cutoff_date)
        
        summary = {
            'total_alerts': alerts.count(),
            'by_type': {},
            'by_severity': {},
            'by_status': {},
            'high_risk_donations': alerts.filter(severity__in=['high', 'critical']).values('donation_id').distinct().count()
        }
        
        # Group by type
        for alert_type, _ in FraudAlert.ALERT_TYPES:
            summary['by_type'][alert_type] = alerts.filter(alert_type=alert_type).count()
        
        # Group by severity
        for severity, _ in FraudAlert.SEVERITY_LEVELS:
            summary['by_severity'][severity] = alerts.filter(severity=severity).count()
        
        # Group by status
        for status, _ in FraudAlert.STATUS_CHOICES:
            summary['by_status'][status] = alerts.filter(status=status).count()
        
        return summary


# Global instance
fraud_detector = FraudDetectionService()
