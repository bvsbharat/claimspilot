"""
Clear MongoDB Database
Deletes all claims and routing history
"""

import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()

from motor.motor_asyncio import AsyncIOMotorClient


async def clear_database():
    """Clear all collections in MongoDB"""

    # Get MongoDB connection string
    mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    database_name = os.getenv("MONGODB_DATABASE", "claims_triage")

    print(f"Connecting to: {mongodb_uri}/{database_name}")

    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(mongodb_uri)
        db = client[database_name]

        # Drop claims collection
        claims_count = await db.claims.count_documents({})
        await db.claims.drop()
        print(f"✅ Deleted claims collection ({claims_count} documents)")

        # Drop routing_history collection
        try:
            history_count = await db.routing_history.count_documents({})
            await db.routing_history.drop()
            print(f"✅ Deleted routing_history collection ({history_count} documents)")
        except:
            pass

        print("\n✅ MongoDB cleared! Adjusters kept intact.")

        # Close connection
        client.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(clear_database())
