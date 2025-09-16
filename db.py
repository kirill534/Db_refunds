# db.py
import psycopg2
from psycopg2 import sql
from config import ENG_FIELDS, ENG_FIELDS_MEMO
from logger import logger

class Database:
    def __init__(self, dsn):
        self.dsn = dsn
        self.conn = None

    def connect(self):
        try:
            self.conn = psycopg2.connect(self.dsn)
            logger.info("БД Подключено")
        except Exception as e:
            logger.exception("Не удалось подключиться к БД")
            raise
    
    def is_connected(self):
        return self.conn and self.conn.closed == 0

    def insert_support_data(self, table, data):
        if table in ['support_data_ton', 'support_data_usdt_(ton)']:
            columns = ENG_FIELDS_MEMO
        else:
            columns = ENG_FIELDS

        columns_identifiers = [sql.Identifier(col) for col in columns]
        placeholders = [sql.Placeholder() for _ in data]

        query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
            sql.Identifier(table),
            sql.SQL(', ').join(columns_identifiers),
            sql.SQL(', ').join(placeholders)
        )
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, list(data.values()))
            self.conn.commit()
            logger.info(f"Данные успешно добавлены {table}")
        except Exception:
            self.conn.rollback()
            logger.exception("Failed to insert data")
            raise

    def update_record(self, table_name, record_id, updated_data):
        """Обновляет запись по id."""
        if not table_name:
            return False
        set_clauses = [sql.SQL("{} = %s").format(sql.Identifier(k)) for k in updated_data.keys()]
        query = sql.SQL("UPDATE {} SET {} WHERE id=%s").format(
            sql.Identifier(table_name),
            sql.SQL(', ').join(set_clauses)
        )
        values = list(updated_data.values()) + [record_id]
        with self.conn.cursor() as conn:
            if not conn:
                return False
            try:
                with conn.cursor() as cur:
                    cur.execute(query, values)
                    conn.commit()
                    logger.info(f"Запись id={record_id} обновлена.")
                    return True
            except psycopg2.Error as e:
                logger.error(f"Ошибка при обновлении записи {record_id}: {e}")
                return False

    def close(self):
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")