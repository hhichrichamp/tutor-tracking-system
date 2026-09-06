import json


def load_users():
    with open("data/users.json", "r", encoding="utf-8") as file:
        return json.load(file)


def authenticate_tutor(user_id, password):
    users = load_users()

    for tutor in users["tutors"]:
        if tutor["id"] == user_id and tutor["password"] == password:
            return tutor

    return None


def find_student(student_id):
    users = load_users()

    for student in users["students"]:
        if student["id"] == student_id:
            return student

    return None