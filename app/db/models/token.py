from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, DateTime, Boolean, ForeignKey, Index, func
from app.db.base import Base

class Token(Base):
    """
    Stores refresh tokens (or their JTI) server-side so we can revoke/rotate.
    """
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), index=True, nullable=False)

    jti: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)  # unique token id
    token: Mapped[str] = mapped_column(String(2048), nullable=False)  # optional: store whole token (or hash)
    user_agent: Mapped[str | None] = mapped_column(String(255))
    ip_address: Mapped[str | None] = mapped_column(String(64))

    expires_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    revoked_at: Mapped["DateTime | None"] = mapped_column(DateTime(timezone=True))

    user = relationship("User")

Index("ix_token_user_expires", Token.user_id, Token.expires_at.desc())
