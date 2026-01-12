import phonenumbers

def format_phone_number(phone_str):
    try:
        # Assuming US numbers for now, as it's a missionary calendar which is often used in US/Canada contexts.
        # We can make this more flexible if needed.
        parsed = phonenumbers.parse(phone_str, "US")
        if phonenumbers.is_valid_number(parsed):
            # If it's a US number, use NATIONAL format
            if parsed.country_code == 1:
                return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL)
            else:
                return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
    except phonenumbers.NumberParseException:
        pass
    return phone_str

def is_valid_phone_number(phone_str):
    try:
        parsed = phonenumbers.parse(phone_str, "US")
        return phonenumbers.is_valid_number(parsed)
    except phonenumbers.NumberParseException:
        return False
