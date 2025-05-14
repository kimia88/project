import pyodbc

class SQLServerDatabase:
    def __init__(self, server, database, username, password):
        self.connection_string = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={server};DATABASE={database};UID={username};PWD={password}"
        )
        self.connection = None

    def connect(self):
        """ایجاد اتصال به دیتابیس"""
        try:
            self.connection = pyodbc.connect(self.connection_string)
            print("✅ Database connection established.")
        except Exception as e:
            print(f"❌ Failed to connect to database: {e}")
            raise

    def disconnect(self):
        """قطع اتصال از دیتابیس"""
        if self.connection:
            try:
                self.connection.close()
                print("✅ Database connection closed.")
            except Exception as e:
                print(f"⚠️ Failed to close connection: {e}")
        else:
            print("⚠️ No active connection to close.")

    def _execute_query(self, query, params=None, fetch=False):
        """اجرای کوئری با پارامترهای ورودی"""
        if not self.connection:
            print("⚠️ Cannot execute query, connection is not established.")
            return None
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params or [])
                if fetch:
                    rows = cursor.fetchall()
                    return rows if rows else []
                else:
                    self.connection.commit()
        except Exception as e:
            print(f"❌ Failed to execute query: {e}")
            self.connection.rollback()
            raise

    def select(self, query, params=None):
        """اجرای کوئری SELECT و دریافت نتایج"""
        result = self._execute_query(query, params=params, fetch=True)
        if result is None:
            print("❌ No data found or query failed.")
        return result

    def test_table_exists(self, table_name):
        """تست وجود جدول در دیتابیس"""
        try:
            query = f"SELECT TOP 1 * FROM dbo.{table_name}"
            result = self.select(query)
            return bool(result)
        except Exception as e:
            print(f"❌ Error checking table '{table_name}': {e}")
            return False

    def get_purecontent_with_null_title(self):
        """دریافت محتواهایی که عنوان ندارند"""
        query = """
            SELECT Id, Description, ContentLanguageId
            FROM dbo.TblPureContent
            WHERE Title IS NULL OR Title = ''
        """
        return self.select(query)

    def get_all_purecontents(self):
        """دریافت تمام محتواها"""
        query = """
            SELECT Id, Title, Description, ContentCategoryId, ContentLanguageId
            FROM dbo.TblPureContent
        """
        return self.select(query)

    def update_pure_content(self, content_id, title):
        """به‌روزرسانی عنوان محتوا در دیتابیس"""
        query = """
            UPDATE dbo.TblPureContent
            SET Title = ?
            WHERE Id = ?
        """
        self._execute_query(query, params=[title, content_id])
