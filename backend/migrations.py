"""数据库迁移登记工具。"""

from datetime import datetime

from extensions import db
from models import MigrationRecord


def ensure_migration_record_table():
    """确保迁移登记表存在，避免启动迁移本身无法留痕。"""
    MigrationRecord.__table__.create(bind=db.engine, checkfirst=True)


def record_migration_applied(migration_key, detail='', logger=None):
    """登记幂等迁移执行结果。"""
    ensure_migration_record_table()
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
        try:
            ensure_migration_record_table()
            record = MigrationRecord.query.filter_by(migration_key=migration_key).first()
            if not record:
                record = MigrationRecord(migration_key=migration_key)
                db.session.add(record)
            record.status = 'applied'
            record.detail = detail or ''
            record.applied_at = datetime.utcnow()
            db.session.commit()
            return record
        except Exception as retry_exc:
            db.session.rollback()
            if logger:
                logger.warning(f"迁移登记失败: {migration_key}: {retry_exc}")
            return None
