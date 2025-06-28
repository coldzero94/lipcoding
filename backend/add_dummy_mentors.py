from backend_code import SessionLocal, User, get_password_hash

dummy_mentors = [
    {"email": f"mentor{i}@test.com", "name": f"멘토{i}", "skills": "python,fastapi,sqlalchemy", "bio": f"테스트 멘토 {i}번입니다."}
    for i in range(1, 11)
]

db = SessionLocal()
for m in dummy_mentors:
    if not db.query(User).filter(User.email == m["email"]).first():
        user = User(
            email=m["email"],
            hashed_password=get_password_hash("test1234"),
            name=m["name"],
            role="mentor",
            bio=m["bio"],
            skills=m["skills"]
        )
        db.add(user)
db.commit()
db.close()
print("더미 멘토 10명 추가 완료!")
