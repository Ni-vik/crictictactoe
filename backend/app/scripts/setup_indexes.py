
import asyncio
import os
import sys

# Add the backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from database.db import users_collection

async def setup_indexes():
    print("Setting up unique indexes...")
    
    # Unique index for username (case-insensitive)
    # Note: Since we store as lowercase, we don't strictly need a case-insensitive collation index,
    # but it's more robust.
    await users_collection.create_index("username", unique=True)
    print("Created unique index for 'username'")
    
    # Unique sparse index for email
    # Sparse means it won't index documents where 'email' is missing/null,
    # allowing multiple users with no email.
    await users_collection.create_index("email", unique=True, sparse=True)
    print("Created unique sparse index for 'email'")
    
    print("Index setup complete!")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(setup_indexes())
