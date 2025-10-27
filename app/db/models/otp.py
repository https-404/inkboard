from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, DateTime, Boolean, ForeignKey, func
from app.db.base import Base

class OtpCode(Base):
    """
    One-time codes for email verification and password reset.
    """
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), index=True, nullable=False)

    purpose: Mapped[str] = mapped_column(String(32), nullable=False)  # "verify_email" | "password_reset"
    code: Mapped[str] = mapped_column(String(128), nullable=False)    # plaintext or hashed code
    expires_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), nullable=False)

    consumed: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    consumed_at: Mapped["DateTime | None"] = mapped_column(DateTime(timezone=True))

    attempts: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")  # rate-limit attempts
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User")
