"""
Testing authentication functions - password hashing and verification.

These are UNIT TESTS - they test individual functions in isolation.
"""
from app.auth import hash_password, verify_password


def test_hash_password_creates_hash():
    """
    Test that hash_password() returns a hashed string (not the original password).
    """
    password = "mysecretpassword"
    hashed = hash_password(password)
    
    # The hash should NOT be the same as the original password
    assert hashed != password
    
    # Bcrypt hashes start with "$2b$" 
    assert hashed.startswith("$2b$")
    
    # Hashes should be long (bcrypt creates ~60 character hashes)
    assert len(hashed) > 50


def test_hash_password_creates_different_hashes():
    """
    Test that hashing the same password twice creates DIFFERENT hashes.
    
    This is important for security - bcrypt adds random "salt" each time.
    """
    password = "samepassword"
    hash1 = hash_password(password)
    hash2 = hash_password(password)
    
    # Same password, but different hashes (because of salt)
    assert hash1 != hash2


def test_verify_password_with_correct_password():
    """
    Test that verify_password() returns True for the correct password.
    """
    password = "correctpassword"
    hashed = hash_password(password)
    
    # Verifying with the correct password should return True
    result = verify_password(password, hashed)
    assert result == True


def test_verify_password_with_wrong_password():
    """
    Test that verify_password() returns False for incorrect password.
    """
    password = "correctpassword"
    hashed = hash_password(password)
    
    # Verifying with wrong password should return False
    result = verify_password("wrongpassword", hashed)
    assert result == False


def test_verify_password_case_sensitive():
    """
    Test that password verification is case-sensitive.
    """
    password = "MyPassword"
    hashed = hash_password(password)
    
    # Different case should fail
    assert verify_password("mypassword", hashed) == False
    assert verify_password("MYPASSWORD", hashed) == False
    
    # Exact match should work
    assert verify_password("MyPassword", hashed) == True
