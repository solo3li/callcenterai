from inngest import Inngest

import os
os.environ.setdefault("INNGEST_SIGNING_KEY", "test")

# Initialize the Inngest client
inngest_client = Inngest(app_id="callcenter-app")
