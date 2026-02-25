from twilio.rest import Client
from ..config.settings import settings
import structlog

logger = structlog.get_logger()

class TwilioService:
    def __init__(self):
        self.client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
        self.service_sid = settings.twilio_verify_service_sid

    async def send_otp(self, phone_number: str) -> bool:
        try:
            # Try sending via WhatsApp first
            logger.info("Sending Twilio OTP via WhatsApp", phone_number=phone_number)
            verification = self.client.verify.v2.services(self.service_sid) \
                .verifications \
                .create(to=phone_number, channel='whatsapp')
            logger.info("Twilio OTP sent via WhatsApp", status=verification.status, phone_number=phone_number)
            return verification.status == "pending"
        except Exception as e:
            error_str = str(e)
            logger.warning("WhatsApp OTP failed, attempting SMS fallback", error=error_str, phone_number=phone_number)
            
            # Error 68008 is "WhatsApp channel not configured". 
            # We fallback to SMS if WhatsApp fails for any reason to ensure user receives the code.
            try:
                logger.info("Sending Twilio OTP via SMS", phone_number=phone_number)
                verification = self.client.verify.v2.services(self.service_sid) \
                    .verifications \
                    .create(to=phone_number, channel='sms')
                logger.info("Twilio OTP sent via SMS", status=verification.status, phone_number=phone_number)
                return verification.status == "pending"
            except Exception as sms_error:
                logger.error("Failed to send Twilio OTP via both WhatsApp and SMS", 
                             whatsapp_error=error_str, 
                             sms_error=str(sms_error), 
                             phone_number=phone_number)
                return False

    async def verify_otp(self, phone_number: str, code: str) -> bool:
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
