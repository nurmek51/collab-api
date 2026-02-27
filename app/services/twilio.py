from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from ..config.settings import settings
import structlog

logger = structlog.get_logger()

class TwilioService:
    def __init__(self):
        if settings.twilio_account_sid and settings.twilio_auth_token and settings.twilio_verify_service_sid:
            self.client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
            self.service_sid = settings.twilio_verify_service_sid
        else:
            self.client = None
            self.service_sid = None
            logger.warning("Twilio credentials missing. OTP service will not function.")

    async def send_otp(self, phone_number: str) -> bool:
        if not self.client or not self.service_sid:
            logger.error("Twilio not configured", phone_number=phone_number)
            return False

        try:
            # Try sending via WhatsApp first
            logger.info(
                "Attempting to send Twilio OTP via WhatsApp", 
                phone_number=phone_number, 
                service_sid=self.service_sid[:4] + "..." if self.service_sid else None
            )
            verification = self.client.verify.v2.services(self.service_sid) \
                .verifications \
                .create(to=phone_number, channel='whatsapp', locale='en')
                
            logger.info("Twilio OTP successfully sent via WhatsApp", status=verification.status, phone_number=phone_number)
            return verification.status == "pending"
            
        except TwilioRestException as e:
            # Enhanced logging for Twilio specific errors
            logger.warning(
                "Twilio WhatsApp OTP failed (TwilioRestException)", 
                error_code=e.code,
                error_msg=e.msg,
                http_status=e.status,
                phone_number=phone_number
            )
            
            # Error 60200: Invalid parameter (e.g. invalid phone number format)
            # Error 68008: WhatsApp channel not configured
            # Continue to SMS fallback
            
        except Exception as e:
            logger.warning(
                "Twilio WhatsApp OTP failed (Generic Exception)", 
                error=str(e), 
                error_type=type(e).__name__,
                phone_number=phone_number
            )
            
        # Fallback to SMS
        try:
            logger.info("Attempting SMS fallback", phone_number=phone_number)
            verification = self.client.verify.v2.services(self.service_sid) \
                .verifications \
                .create(to=phone_number, channel='sms')
            logger.info("Twilio OTP sent via SMS", status=verification.status, phone_number=phone_number)
            return verification.status == "pending"
        except Exception as sms_error:
            logger.error("Failed to send Twilio OTP via both WhatsApp and SMS", 
                         sms_error=str(sms_error), 
                         phone_number=phone_number)
            return False

    async def verify_otp(self, phone_number: str, code: str) -> bool:
        if not self.client or not self.service_sid:
            logger.error("Twilio not configured for verification", phone_number=phone_number)
            return False

        try:
            logger.info("Verifying Twilio OTP", phone_number=phone_number)
            verification_check = self.client.verify.v2.services(self.service_sid) \
                .verification_checks \
                .create(to=phone_number, code=code)
            logger.info("Twilio OTP verification check", status=verification_check.status, phone_number=phone_number)
            return verification_check.status == "approved"
        except Exception as e:
            logger.error("Failed to verify Twilio OTP", error=str(e), phone_number=phone_number)
            return False
