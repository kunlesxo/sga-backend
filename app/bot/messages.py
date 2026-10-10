"""All bot text. Edit here to change wording — no code changes needed."""

WELCOME_TEMPLATE = (
    "\U0001F389 <b>Payment verified!</b>\n\n"
    "Welcome to the <b>Sales Growth Academy</b> "
    "Montessori &amp; Learning Resources Masterclass.\n\n"
    "Classroom: <b>tap the button below</b>\n"
    "Discussion &amp; Q&A: <b>tap the button below</b>\n\n"
    "Your access is valid until <b>{expiry}</b>.\n\n"
    "If a link expires before you use it, send /start again to get a fresh one."
)

NO_REFERENCE = (
    "Hi! I am the Sales Growth Academy Student Access bot.\n\n"
    "Please use the <b>Get Telegram Access</b> link from your "
    "payment success page to continue."
)

VERIFY_FAILED = (
    "\u26A0\uFE0F We could not verify your payment yet.\n\n"
    "This can happen if the payment is still processing.\n"
    "Please try again in a few minutes, or contact support if the problem continues.\n\n"
    "Support: {support}"
)

ALREADY_LINKED = (
    "\u26A0\uFE0F This payment reference is already linked to another "
    "Telegram account.\n\n"
    "If you believe this is an error, please contact support:\n{support}"
)

HELP = (
    "For support, contact Sales Growth Academy:\n{support}"
)

INVALID_REFERENCE = (
    "\u26A0\uFE0F We could not find a payment with that reference.\n\n"
    "Please make sure you used the link from your payment success page."
)

ERROR_SENDING_LINKS = (
    "We verified your payment but had a temporary problem sending your "
    "invite links. Please send /start again in a moment."
)
