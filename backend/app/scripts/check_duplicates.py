
import asyncio
import os
import sys

# Add the backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from database.db import users_collection

async def main():
    print("Checking for duplicate users...")
    users = await users_collection.find().to_list(length=None)
    
    usernames = {}
    emails = {}
    
    duplicates_found = False
    
    for u in users:
        uname = u.get('username', '').lower()
        uemail = u.get('email', '')
        uemail_low = uemail.lower() if uemail else None
        
        print(f"User: {u.get('username')} | Email: {u.get('email')} | ID: {u.get('user_id')}")

        if uname in usernames:
            print(f"  !! DUPLICATE USERNAME: {uname}")
            duplicates_found = True
        else:
            usernames[uname] = u['user_id']
            
        if uemail_low and uemail_low in emails:
            print(f"  !! DUPLICATE EMAIL: {uemail_low}")
            duplicates_found = True
        elif uemail_low:
            emails[uemail_low] = u['user_id']

    if not duplicates_found:
        print("No duplicates found in database.")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
