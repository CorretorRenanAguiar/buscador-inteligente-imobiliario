from supabase import create_client

from dotenv import load_dotenv

import os



# =========================================
# LOAD ENV
# =========================================

load_dotenv()



# =========================================
# VARIÁVEIS
# =========================================

SUPABASE_URL = os.getenv(

    "SUPABASE_URL"

)



SUPABASE_KEY = os.getenv(

    "SUPABASE_KEY"

)



# =========================================
# CLIENT SUPABASE
# =========================================

supabase = create_client(

    SUPABASE_URL,

    SUPABASE_KEY

)