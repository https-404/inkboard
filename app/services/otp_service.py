
import logging
import uuid
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status
from app.db.models.otp import OtpCode
from app.services.email_service import send_email
from email_validator import validate_email, EmailNotValidError

logger = logging.getLogger(__name__)

class OtpService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_otp(self, length: int = 6) -> str:
        """
        Generate a numeric OTP of specified length.
        """
        from random import choices
        from string import digits

        otp = ''.join(choices(digits, k=length))
        return otp
    
    async def is_valid_email(self, email: str) -> bool:
        """
        Validate email format and deliverability.
        """
        try:
            validation = validate_email(email, check_deliverability=True)
            return True
        except EmailNotValidError:
            return False
    
    async def store_and_send_otp(self, user_id: uuid.UUID, email: str, purpose: str = "email_verification") -> bool:
        """
        Generate OTP, store it in DB, and send via email.
        Returns True if successful, False if email is invalid.
        """
        try:
            # First validate the email
            if not await self.is_valid_email(email):
                return False

            # Generate new OTP
            otp = await self.generate_otp()
            expires_at = datetime.utcnow() + timedelta(minutes=10)  # OTP valid for 10 minutes

            # Create OTP record
            otp_record = OtpCode(
                user_id=user_id,
                code=otp,
                purpose=purpose,
                expires_at=expires_at
            )
            
            # Save to database
            self.db.add(otp_record)
            await self.db.commit()
            await self.db.refresh(otp_record)

            # Send OTP via email
            await send_email(
                subject="InkBoard - Your Verification Code",
                recipients=[email],
                template_name="send_otp.html",
                context={
                    "otp": otp,
                    "expires_in_minutes": "10",  # Convert to string for template
                    "app_name": "InkBoard"
                }
            )

            return True

        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Database error while storing OTP: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate and store OTP"
            )
        except Exception as e:
            logger.error(f"Error in OTP service: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process OTP request"
            )

    async def verify_otp(self, user_id: uuid.UUID, input_otp: str, purpose: str = "email_verification") -> bool:
        """
        Verify if the input OTP matches the stored OTP for the given user and purpose.
        """
        try:
            # Find the latest non-expired OTP for this user and purpose
            stmt = select(OtpCode).where(
                and_(
                    OtpCode.user_id == user_id,
                    OtpCode.purpose == purpose,
                    OtpCode.expires_at > datetime.utcnow(),
                    OtpCode.consumed.is_(False)  # using consumed instead of used
                )
            ).order_by(OtpCode.created_at.desc())
            
            result = await self.db.execute(stmt)
            otp_record = result.scalar_one_or_none()

            if not otp_record:
                return False

            # Increment attempts
            otp_record.attempts += 1
            await self.db.commit()

            # Verify OTP
            if otp_record.code == input_otp:
                # Mark OTP as consumed
                otp_record.consumed = True
                otp_record.consumed_at = datetime.utcnow()
                await self.db.commit()
                return True

            # If we reach here, the OTP was invalid
            if otp_record.attempts >= 3:  # Limit attempts
                otp_record.consumed = True
                otp_record.consumed_at = datetime.utcnow()
                await self.db.commit()

            return False

        except SQLAlchemyError as e:
            logger.error(f"Database error while verifying OTP: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to verify OTP"
            )