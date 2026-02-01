from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from app.core.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    entity_type = Column(String, index=True)
    count = Column(Integer)
    request_id = Column(String, index=True)

# CRUD Ops
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

async def create_audit_log(db: AsyncSession, entity_type: str, count: int, request_id: str):
    db_log = AuditLog(entity_type=entity_type, count=count, request_id=request_id)
    db.add(db_log)
    await db.commit()
    await db.refresh(db_log)
    print(f"[AUDIT] Logged: {entity_type} ({count}) -> ID: {db_log.id}")
    return db_log

async def get_audit_stats(db: AsyncSession):
    # This is a simple aggregation for the dashboard
    # Returns list of tuples (entity_type, count)
    result = await db.execute(select(AuditLog)) # In prod, use GROUP BY
    logs = result.scalars().all()
    
    # Manual aggregation for simplicity with async
    stats = {}
    for log in logs:
        stats[log.entity_type] = stats.get(log.entity_type, 0) + log.count
    return stats
