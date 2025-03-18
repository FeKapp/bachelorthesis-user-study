# supabase_client.py
import os
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables from .env file
load_dotenv()

def init_supabase():
    client = create_client(
        os.getenv('SUPABASE_URL'), 
        os.getenv('SUPABASE_KEY')
    )
    # Force schema refresh by making a simple query
    try:
        client.table('sessions').select('*').limit(1).execute()
    except:
        pass
    return client