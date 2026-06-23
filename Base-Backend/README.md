# FindMeWriter Backend

This is the backend for FindMeWriter, an accessibility-first platform connecting visually impaired students with volunteer writers.

## Setup

1. Create a virtual environment and activate it.
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and set the required environment variables (especially `ENCRYPTION_KEY`). Generate a Fernet key with:
   ```python
   from cryptography.fernet import Fernet
   print(Fernet.generate_key().decode())
   ```
4. Run the app: `python wsgi.py`

## API Endpoints

See the route files for details. Authentication uses JWT Bearer tokens.

## License

GPL v3.0
