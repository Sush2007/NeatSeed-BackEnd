import os
import sys
from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = None

try:
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("FATAL ERROR: Missing Supabase Credentials", file=sys.stderr)
    else:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("SUCCESS: Supabase client initialized.")
except Exception as e:
    print(f"!!! CRASH DURING SUPABASE SETUP !!! Error: {e}", file=sys.stderr)