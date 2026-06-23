import os
from cryptography.fernet import Fernet
from flask import current_app

def get_cipher():
    key = current_app.config['ENCRYPTION_KEY']
    return Fernet(key)

def encrypt_bytes(data: bytes) -> bytes:
    return get_cipher().encrypt(data)

def decrypt_bytes(data: bytes) -> bytes:
    return get_cipher().decrypt(data)

def encrypt_file(input_path, output_path):
    with open(input_path, 'rb') as f:
        plain = f.read()
    encrypted = encrypt_bytes(plain)
    with open(output_path, 'wb') as f:
        f.write(encrypted)

def decrypt_file(input_path, output_path):
    with open(input_path, 'rb') as f:
        encrypted = f.read()
    plain = decrypt_bytes(encrypted)
    with open(output_path, 'wb') as f:
        f.write(plain)
