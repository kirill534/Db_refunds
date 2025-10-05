# db.py
import psycopg2
from sqlalchemy import create_engine
from psycopg2 import sql
from config import CONN_DB, ENG_FIELDS, ENG_FIELDS_MEMO
from logger import logger
from telegram_sender import send_telegram_message, send_telegram_photo_with_message

class Database:
    def __init__(self, dsn):
        self.dsn = dsn
        self.conn = None
        self.engine = None  # Добавляем атрибут engine

    def connect(self):
        try:
            self.conn = psycopg2.connect(self.dsn)
            # Создаем SQLAlchemy engine
            url = self._dsn_to_url(self.dsn)
            self.engine = create_engine(url)
            logger.info("БД Подключено")
        except Exception as e:
            logger.exception("Не удалось подключиться к БД")
            raise

    def _dsn_to_url(self, dsn):
        # Преобразование строки DSN в URL
        # Например, "dbname=test user=postgres password=secret host=localhost port=5432"
        params = {}
        for item in dsn.split():
            key, value = item.split('=')
            params[key] = value
        user = params.get('user')
        password = params.get('password')
        host = params.get('host')
        port = params.get('port')
        dbname = params.get('dbname')
        return f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
    
    def is_connected(self):
        return self.conn and self.conn.closed == 0
    
    def execute(self, query, params=None):
        """Выполняет произвольный запрос."""
        db = Database(self.dsn)
        try:
            db.connect()
            with self.conn.cursor() as cur:
                try:
                    cur.execute(query, params)
                    if query.strip().upper().startswith("SELECT"):
                        return cur.fetchall()
                    else:
                        self.conn.commit()
                except psycopg2.Error:
                    self.conn.rollback()
                    raise
        except Exception as e:
            print("Ошибка:", e)
        finally:
            db.close()

    def insert_support_data(self, photo_paths, video_paths, table, data, manual_send_var):
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

            # После успешной вставки — подготовить сообщение и отправить файлы
            if not manual_send_var.get():
                user_id = data.get('ID Клиента')
                token = data.get('Токен')
                return_address = data.get('Адрес возврата')
                receipt_amount = data.get('Сумма поступления')
                return_reason = data.get('Причина возврата')
                memo = data.get('Мемо', '')

                if data.get('Адрес отправителя') == return_address:
                    message = (
                        "Возврат на исходный адрес ❌:\n"
                        f"ID клиента: {user_id}\n"
                        f"Токен: {token}\n"
                        f"Адрес возврата: {return_address}\n"
                        f"Сумма поступления: {receipt_amount}\n"
                        f"Причина возврата: {return_reason}"
                    )
                else:
                    message = (
                        "Возврат на ДРУГОЙ адрес ❌:\n"
                        f"ID клиента: {user_id}\n"
                        f"Токен: {token}\n"
                        f"Адрес возврата: {return_address}\n"
                        f"Сумма поступления: {receipt_amount}\n"
                        f"Причина возврата: {return_reason}"
                    )
                if memo:
                    message += f"\nМемо: {memo}"

                # Отправляем все файлы одним вызовом
                send_telegram_photo_with_message(photo_paths, video_paths, message)

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
            
    def check_record_exists(self, table_name, field1, value1, field2, value2, field3, value3):
        query = sql.SQL("""
            SELECT 1 FROM {} WHERE {} = %s AND {} = %s AND {} = %s LIMIT 1
        """).format(
            sql.Identifier(table_name),
            sql.Identifier(field1),
            sql.Identifier(field2),
            sql.Identifier(field3),
        )
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (value1, value2, value3))
                return cur.fetchone() is not None
        except psycopg2.Error as e:
            logger.exception(f"Ошибка при проверке существования записи: {e}")
            return False

    def close(self):
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
