from fastapi import HTTPException
import re 


class PasswordValidationError(ValueError):
    pass


def validate_password(password: str) -> None:
    """
Checks password validity by criteria:
    - at least 8 characters
    - contains at least one uppercase letter
    - contains at least one lowercase letter
    - contains at least one number
    """
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="The password must contain a minimum of 8 characters.")
    if not re.search(r"[A-Z]", password):
        raise HTTPException(status_code=400, detail="The password must contain at least one capital letter.")
    if not re.search(r"[a-z]", password):
        raise HTTPException(status_code=400, detail="The password must contain at least one lowercase letter.")
    if not re.search(r"[0-9]", password):
        raise HTTPException(status_code=400, detail="The password must contain at least one digit.")
    return password