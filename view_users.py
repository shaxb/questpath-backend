import asyncio
import sys
import os

# Add the current directory to the path so we can import app modules
sys.path.append(os.getcwd())

from sqlalchemy import select
from app.db import async_session
from app.models import User

async def view_users():
    async with async_session() as session:
        # Query all users
        result = await session.execute(select(User).order_by(User.id))
        users = result.scalars().all()
        
        print("-" * 120)
        print(f"{'ID':<5} | {'Email':<30} | {'Display Name':<20} | {'XP':<10} | {'Google ID':<25}")
        print("-" * 120)
        
        for user in users:
            display_name = user.display_name if user.display_name else "N/A"
            google_id = user.google_id if user.google_id else "N/A"
            
            print(f"{user.id:<5} | {user.email:<30} | {display_name:<20} | {user.total_exp:<10} | {google_id:<25}")
        
        print("-" * 120)
        print(f"Total Users: {len(users)}")

if __name__ == "__main__":
    asyncio.run(view_users())
