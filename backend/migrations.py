"""数据库迁移登记工具。"""

from datetime import datetime

from extensions import db
from models import MigrationRecord


def record_migration_applied(migration_key, detail='', logger=None):
    """登记幂等迁移执行结果。"""
    try:
        record = MigrationRecord.query.filter_by(migration_key=migration_key).first()
        if not record:
            record = MigrationRecord(migration_key=migration_key)
            db.session.add(record)
        record.status = 'applied'
        record.detail = detail or ''
        record.applied_at = datetime.utcnow()
        db.session.commit()
        return record
    except Exception as exc:
        db.session.rollback()
        if logger:
            logger.warning(f"迁移登记失败: {migration_key}: {exc}")
        return None
