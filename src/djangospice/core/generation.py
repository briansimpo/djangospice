import uuid
import base64
import random
import string
from random import randint
from django.utils import timezone

def random_number(length):
    return str(randint(0, 10**length-1)).zfill(length)

def random_string(length):
    letters = string.ascii_uppercase
    return ''.join(random.choice(letters) for i in range(length))

def reference_number(length=16, date_format='%Y%m%d'):
    unique_id = uuid.uuid4()
    ref_number = base64.urlsafe_b64encode(unique_id.bytes).decode('utf-8').rstrip('=\n').replace('-', '').replace('_', '')
    date_str = timezone.now().strftime(date_format)
    return (date_str + ref_number.upper())[:length]


def generate_years(start_year=1950):
    current_year = timezone.now().year
    return [(y, y) for y in range(current_year, start_year - 1, -1)]


def generate_checksum(bban: str) -> str:
    """
    Calculate ISO 7064 mod-97-10 checksum (IBAN style).
    Accepts BBAN with letters or digits.
    A=10, ..., Z=35 before calculating.
    """
    # Step 1: Add placeholder check digits "00"
    temp = bban.upper() + "00"

    # Step 2: Convert letters to numbers (A=10...Z=35)
    converted = []
    for ch in temp:
        if ch.isalpha():
            converted.append(str(ord(ch) - 55))  # ord('A')=65 → 10
        else:
            converted.append(ch)
    numeric_str = "".join(converted)

    # Step 3: Mod 97
    remainder = int(numeric_str) % 97
    check_digits = 98 - remainder

    # Step 4: Return two-digit checksum
    return str(check_digits).zfill(2)

