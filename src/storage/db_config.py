from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker, scoped_session
from src.storage.models import Base
import logging

logger = logging.getLogger("DB_Manager")

# PostgreSQL 连接串 (根据你的 docker-compose.yml)
DATABASE_URL = "postgresql+psycopg://postgres:postgres123@localhost:5432/newspilot"

class DatabaseManager:
    def __init__(self, connection_string=DATABASE_URL):
        self.engine = create_engine(
            connection_string,
            pool_size=10,
            max_overflow=20,
            echo=False 
        )
        self.SessionFactory = sessionmaker(bind=self.engine)
        self.ScopedSession = scoped_session(self.SessionFactory)

    def verify_and_create_tables(self):
        """
        核心方法：检查表是否存在，不存在则创建。
        符合你要求的 '每次运行前检查'
        """
        try:
            inspector = inspect(self.engine)
            existing_tables = inspector.get_table_names()
            
            # 获取模型中定义的所有表名
            expected_tables = Base.metadata.tables.keys()
            
            missing_tables = [t for t in expected_tables if t not in existing_tables]
            
            if missing_tables:
                logger.info(f"Detecting missing tables: {missing_tables}. Creating them now...")
                # create_all只会创建不存在的表，不会影响已有表数据
                Base.metadata.create_all(self.engine)
                logger.info("Tables created successfully.")
            else:
                logger.info(f"All expected tables {existing_tables} exist. Skipping creation.")
                
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise e

    def get_session(self):
        return self.ScopedSession()

# 实例化单例
db_manager = DatabaseManager()
