from sqlalchemy import create_engine
from sqlalchemy.sql import text
from config import DATABASE_URL

def update_user_emails():
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        try:
            # Actualizar el correo electrónico del usuario 'andres10'
            conn.execute(text("""
                UPDATE users 
                SET email = 'andrescardoso2003@gmail.com'
                WHERE username = 'andres10'
            """))
            
            # Actualizar el correo electrónico del usuario 'admin'
            conn.execute(text("""
                UPDATE users 
                SET email = 'andrescardoso2003@gmail.com'
                WHERE username = 'admin'
            """))
            
            conn.commit()
            print("Correos electrónicos actualizados exitosamente")
            
        except Exception as e:
            print(f"Error al actualizar correos electrónicos: {e}")
            conn.rollback()
            raise

if __name__ == '__main__':
    update_user_emails() 