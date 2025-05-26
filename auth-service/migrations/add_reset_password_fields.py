from sqlalchemy import create_engine, String, DateTime
from sqlalchemy.sql import text
import sys
import os

# Agregar el directorio padre al path para poder importar config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATABASE_URL

def check_column_exists(conn, table_name, column_name):
    """Verifica si una columna existe en una tabla"""
    result = conn.execute(text(f"""
        SELECT COUNT(*)
        FROM information_schema.columns 
        WHERE table_name = '{table_name}' 
        AND column_name = '{column_name}'
    """))
    return result.scalar() > 0

def upgrade():
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        try:
            # Verificar y agregar columna email si no existe
            if not check_column_exists(conn, 'users', 'email'):
                print("Agregando columna email...")
                conn.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN email VARCHAR(120) UNIQUE
                """))
            
            # Verificar y agregar columna reset_token si no existe
            if not check_column_exists(conn, 'users', 'reset_token'):
                print("Agregando columna reset_token...")
                conn.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN reset_token VARCHAR(100) UNIQUE
                """))
            
            # Verificar y agregar columna reset_token_expires si no existe
            if not check_column_exists(conn, 'users', 'reset_token_expires'):
                print("Agregando columna reset_token_expires...")
                conn.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN reset_token_expires DATETIME
                """))
            
            conn.commit()
            print("Migración completada exitosamente")
            
        except Exception as e:
            print(f"Error durante la migración: {e}")
            conn.rollback()
            raise

def downgrade():
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        try:
            # Eliminar columnas en orden inverso
            if check_column_exists(conn, 'users', 'reset_token_expires'):
                print("Eliminando columna reset_token_expires...")
                conn.execute(text("""
                    ALTER TABLE users 
                    DROP COLUMN reset_token_expires
                """))
            
            if check_column_exists(conn, 'users', 'reset_token'):
                print("Eliminando columna reset_token...")
                conn.execute(text("""
                    ALTER TABLE users 
                    DROP COLUMN reset_token
                """))
            
            if check_column_exists(conn, 'users', 'email'):
                print("Eliminando columna email...")
                conn.execute(text("""
                    ALTER TABLE users 
                    DROP COLUMN email
                """))
            
            conn.commit()
            print("Rollback completado exitosamente")
            
        except Exception as e:
            print(f"Error durante el rollback: {e}")
            conn.rollback()
            raise

if __name__ == '__main__':
    upgrade() 