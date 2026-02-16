
import asyncio
import os
import sys

# Add the backend directory to sys.path to import app modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from database.db import players_collection

async def main():
    player = await players_collection.find_one()
    print(player)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
