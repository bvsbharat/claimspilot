"""
Seed demo adjusters into MongoDB
"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
backend_dir = Path(__file__).parent.parent
sys.path.append(str(backend_dir))

# Load environment variables
load_dotenv(backend_dir / ".env")

from services.mongodb_service import get_mongodb_service


async def seed_adjusters():
    """Seed demo adjusters"""
    print("Seeding demo adjusters...")

    mongodb = await get_mongodb_service()

    adjusters = [
        {
            "adjuster_id": "adj_mike_001",
            "name": "Mike Johnson",
            "email": "mike.johnson@insurance.com",
            "phone": "555-0101",
            "specializations": ["auto", "property"],
            "experience_level": "junior",
            "years_experience": 2,
            "max_claim_amount": 50000.0,
            "max_concurrent_claims": 15,
            "current_workload": 0,
            "territories": ["CA", "NV"],
            "available": True,
        },
        {
            "adjuster_id": "adj_lisa_002",
            "name": "Lisa Chen",
            "email": "lisa.chen@insurance.com",
            "phone": "555-0102",
            "specializations": ["commercial", "property", "liability"],
            "experience_level": "senior",
            "years_experience": 12,
            "max_claim_amount": 5000000.0,
            "max_concurrent_claims": 10,
            "current_workload": 0,
            "territories": ["CA", "OR", "WA"],
            "available": True,
        },
        {
            "adjuster_id": "adj_david_003",
            "name": "David Martinez",
            "email": "david.martinez@insurance.com",
            "phone": "555-0103",
            "specializations": ["siu", "liability"],
            "experience_level": "expert",
            "years_experience": 18,
            "max_claim_amount": 10000000.0,
            "max_concurrent_claims": 8,
            "current_workload": 0,
            "territories": ["CA", "NV", "AZ"],
            "available": True,
        },
        {
            "adjuster_id": "adj_sarah_004",
            "name": "Sarah Williams",
            "email": "sarah.williams@insurance.com",
            "phone": "555-0104",
            "specializations": ["injury", "auto"],
            "experience_level": "mid",
            "years_experience": 6,
            "max_claim_amount": 250000.0,
            "max_concurrent_claims": 12,
            "current_workload": 0,
            "territories": ["CA"],
            "available": True,
        },
    ]

    for adjuster in adjusters:
        success = await mongodb.save_adjuster(adjuster)
        if success:
            print(f"✅ Created adjuster: {adjuster['name']} ({adjuster['adjuster_id']})")
        else:
            print(f"❌ Failed to create adjuster: {adjuster['name']}")

    print(f"\nSeeded {len(adjusters)} adjusters successfully!")
    print("\nAdjusters:")
    for adj in adjusters:
        print(f"  - {adj['name']}: {', '.join(adj['specializations'])} ({adj['experience_level']})")


if __name__ == "__main__":
    asyncio.run(seed_adjusters())
