from fastapi import APIRouter, HTTPException, status

from app.services.email_service import send_verification_email

test_router = APIRouter(prefix="/test", tags=["test"])

@test_router.post(
    "/send-verification-email",
    summary="Send Test Verification Email",
    status_code=status.HTTP_200_OK
)
async def test_send_verification_email(
):
    """
    Test endpoint to send a verification email.
    
    Args:
        email: Recipient email address
        username: Username to include in the email
        token: Verification token to include in the email link
        
    Returns:
        Success message if email is sent
    """
    try:
        await send_verification_email("test@gmail.com", "test@gmail.com", "sample_token")
        return {"message": f"Verification email sent to test@gmail.com"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {e}"
        )