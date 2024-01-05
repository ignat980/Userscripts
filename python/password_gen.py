import random
import string

def generate_password(length=16):
    if length < 16:
        raise ValueError("Password length must be at least 16 characters")

    # Defining the characters to be used in the password
    lowercase_letters = string.ascii_lowercase
    uppercase_letters = string.ascii_uppercase
    digits = string.digits
    special_characters = "!@#$%^&*_."
    
    # Ensuring at least one character of each type is included
    password = [
        random.choice(lowercase_letters),
        random.choice(uppercase_letters),
        random.choice(digits),
        random.choice(special_characters)
    ]

    # Filling the rest of the password length
    remaining_length = length - len(password)
    all_characters = lowercase_letters + uppercase_letters + digits + special_characters
    password += random.choices(all_characters, k=remaining_length)

    # Shuffling to avoid predictable patterns
    random.shuffle(password)

    return ''.join(password)

# Generate a random password
print(generate_password())