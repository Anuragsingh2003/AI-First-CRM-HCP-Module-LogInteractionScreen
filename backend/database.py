import aiomysql
import asyncio

# Global connection pool
pool = None

async def init_pool():
    global pool
    try:
        pool = await aiomysql.create_pool(
            host='localhost',
            port=3306,
            user='root',
            password='',  # Empty password
            db='patient_db',
            autocommit=True,
            minsize=1,
            maxsize=10
        )
        print("Database connection pool initialized successfully")
        return pool
    except aiomysql.Error as e:
        print(f"MySQL pool initialization error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error in pool initialization: {e}")
        return None

async def get_db_connection():
    global pool
    if pool is None:
        pool = await init_pool()
        if pool is None:
            print("Failed to initialize connection pool")
            return None
    try:
        conn = await pool.acquire()
        print("Database connection acquired from pool")
        return conn
    except aiomysql.Error as e:
        print(f"MySQL connection error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error in database connection: {e}")
        return None

async def close_pool():
    global pool
    if pool is not None:
        pool.close()
        await pool.wait_closed()
        print("Database connection pool closed")
        pool = None
