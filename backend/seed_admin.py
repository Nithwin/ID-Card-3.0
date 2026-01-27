
from database_config import User, get_session, engine, create_db_and_tables
from sqlmodel import Session, select
from passlib.context import CryptContext

# Fix for passlib if bcrypt is still weird, but downgrade should fix it.
# Setup Auth
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def seed_admin():
    create_db_and_tables()
    with Session(engine) as session:
        statement = select(User).where(User.username == "admin")
        user = session.exec(statement).first()
        if user:
            print("Admin already exists.")
            return
        
        admin_user = User(
            username="admin",
            hashed_password=get_password_hash("admin"),
            full_name="System Administrator",
            role="admin"
        )
        session.add(admin_user)
        session.commit()
        print("Admin user created: admin / admin")

if __name__ == "__main__":
    seed_admin()
