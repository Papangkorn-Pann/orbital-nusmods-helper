import os
from dotenv import load_dotenv
load_dotenv()

DATABASE_URL     = os.getenv("DATABASE_URL", "")
GEMINI_API_KEY   = os.getenv("GEMINI_API_KEY", "")
DISQUS_API_KEY   = os.getenv("DISQUS_API_KEY", "")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
