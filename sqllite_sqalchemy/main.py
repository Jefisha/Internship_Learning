from database import Base, engine, SessionLocal
from models import Student

Base.metadata.create_all(bind=engine)
db = SessionLocal()

def create_student(name, email):
    s = Student(name=name, email=email)
    db.add(s)
    db.commit()
    db.refresh(s)
    return s

def get_students():
    return db.query(Student).all()


while True:
    name = input("Enter student name (or 'q' to quit): ")
    if name.lower() == "q":
        break
    
    email = input("Enter student email: ")
    create_student(name, email)

print("\nAll students:")
for s in get_students():
    print(s.id, s.name, s.email)
