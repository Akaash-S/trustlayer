import asyncio
from app.core.database import init_db
from app.modules.audit import AuditLog # Important: Register model

async def main():
    print("Initializing Database...")
    try:
        await init_db()
        print("Database tables created successfully!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
