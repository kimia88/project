import pyodbc

class SQLServerDatabase:
    def __init__(self, server, database, username, password):
        self.connection_string = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={server};DATABASE={database};UID={username};PWD={password}"
        )
        self.connection = None

    def connect(self):
        try:
            self.connection = pyodbc.connect(self.connection_string)
            print("✅ Database connection established.")
        except Exception as e:
            print(f"❌ Failed to connect to database: {e}")
            raise

    def disconnect(self):
        if self.connection:
            try:
                self.connection.close()
                print("✅ Database connection closed.")
            except Exception as e:
                print(f"⚠️ Failed to close connection: {e}")
        else:
            print("⚠️ No active connection to close.")

    def _execute_query(self, query, params=None, fetch=False):
        if not self.connection:
            print("⚠️ Cannot execute query, connection is not established.")
            return None
        
        try:
            cursor = self.connection.cursor()
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
        finally:
            cursor.close()

    def select(self, query, params=None):
        result = self._execute_query(query, params=params, fetch=True)
        if result is None:
            print("❌ No data found or query failed.")
        return result

    def test_table_exists(self, table_name):
        try:
            query = f"SELECT TOP 1 * FROM dbo.{table_name}"
            result = self.select(query)
            return bool(result)
        except Exception as e:
            print(f"❌ Error checking table '{table_name}': {e}")
            return False

    def get_purecontent_with_null_title(self):
        """
        رکوردهایی را برمی‌گرداند که عنوان ندارند (null یا رشته خالی)
        """
        query = """
            SELECT Id, Description, ContentLanguageId
            FROM dbo.TblPureContent
            WHERE Title IS NULL OR Title = ''
        """
        return self.select(query)

    def get_all_purecontents(self):
        """
        برمی‌گرداند تمام رکوردهای TblPureContent با Id، Title، Description، ContentCategoryId و ContentLanguageId
        """
        query = """
            SELECT Id, Title, Description, ContentCategoryId, ContentLanguageId
            FROM dbo.TblPureContent
        """
        return self.select(query)

    def update_pure_content(self, content_id, title):
        """
        به‌روزرسانی عنوان برای محتوای مشخص‌شده با Id
        """
        query = """
            UPDATE dbo.TblPureContent
            SET Title = ?
            WHERE Id = ?
        """
        self._execute_query(query, params=[title, content_id])
