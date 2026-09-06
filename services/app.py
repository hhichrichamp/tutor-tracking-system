import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
from datetime import datetime, date, time, timedelta
import json
import uuid


# ============================================================
# CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Tutor Attendance",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown("""
<style>

    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }

    .subtitle {
        color: #6b7280;
        margin-bottom: 2rem;
    }

    .metric-card {
        background-color: #f8fafc;
        border-radius: 12px;
        padding: 20px;
        border: 1px solid #e5e7eb;
    }

    .session-card {
        background-color: white;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 12px;
    }

    .status-active {
        color: #15803d;
        font-weight: 700;
    }

    .status-scheduled {
        color: #2563eb;
        font-weight: 700;
    }

    .status-completed {
        color: #6b7280;
        font-weight: 700;
    }

    .qr-box {
        text-align: center;
        padding: 20px;
    }

</style>
""", unsafe_allow_html=True)


# ============================================================
# USER DATA
# ============================================================

@st.cache_data
def load_users():

    with open("data/users.json", "r", encoding="utf-8") as f:
        return json.load(f)


USERS = load_users()


# ============================================================
# SAMPLE DATA
# ============================================================

def create_sample_sessions():

    today = date.today()

    return [
        {
            "id": "SES001",
            "tutor_id": "T001",
            "student_ids": ["S001"],
            "date": today,
            "start_time": time(14, 0),
            "expected_minutes": 60,
            "status": "Scheduled",
            "actual_start": None,
            "actual_end": None,
            "qr_token": None
        },
        {
            "id": "SES002",
            "tutor_id": "T001",
            "student_ids": ["S002"],
            "date": today,
            "start_time": time(16, 0),
            "expected_minutes": 90,
            "status": "Active",
            "actual_start": datetime.now() - timedelta(minutes=20),
            "actual_end": None,
            "qr_token": "DEMO-SES002"
        },
        {
            "id": "SES003",
            "tutor_id": "T002",
            "student_ids": ["S003", "S004"],
            "date": today - timedelta(days=1),
            "start_time": time(15, 0),
            "expected_minutes": 60,
            "status": "Completed",
            "actual_start": datetime.combine(
                today - timedelta(days=1),
                time(15, 2)
            ),
            "actual_end": datetime.combine(
                today - timedelta(days=1),
                time(16, 3)
            ),
            "qr_token": "DEMO-SES003"
        },
        {
            "id": "SES004",
            "tutor_id": "T003",
            "student_ids": ["S005"],
            "date": today - timedelta(days=2),
            "start_time": time(17, 0),
            "expected_minutes": 120,
            "status": "Completed",
            "actual_start": datetime.combine(
                today - timedelta(days=2),
                time(17, 1)
            ),
            "actual_end": datetime.combine(
                today - timedelta(days=2),
                time(18, 55)
            ),
            "qr_token": "DEMO-SES004"
        }
    ]


if "sessions" not in st.session_state:
    st.session_state.sessions = create_sample_sessions()


if "attendance" not in st.session_state:

    st.session_state.attendance = [
        {
            "id": "ATT001",
            "session_id": "SES003",
            "student_id": "S003",
            "check_in": datetime.combine(
                date.today() - timedelta(days=1),
                time(15, 3)
            ),
            "check_out": datetime.combine(
                date.today() - timedelta(days=1),
                time(16, 2)
            )
        },
        {
            "id": "ATT002",
            "session_id": "SES003",
            "student_id": "S004",
            "check_in": datetime.combine(
                date.today() - timedelta(days=1),
                time(15, 4)
            ),
            "check_out": datetime.combine(
                date.today() - timedelta(days=1),
                time(16, 1)
            )
        }
    ]


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_tutor(tutor_id):

    for tutor in USERS["tutors"]:
        if tutor["id"] == tutor_id:
            return tutor

    return None


def get_student(student_id):

    for student in USERS["students"]:
        if student["id"] == student_id:
            return student

    return None


def get_user_name(user_id):

    tutor = get_tutor(user_id)

    if tutor:
        return tutor["name"]

    student = get_student(user_id)

    if student:
        return student["name"]

    for admin in USERS["admins"]:
        if admin["id"] == user_id:
            return admin["name"]

    return user_id


def format_duration(minutes):

    if minutes is None:
        return "-"

    hours = int(minutes // 60)
    mins = int(minutes % 60)

    if hours == 0:
        return f"{mins} min"

    return f"{hours}h {mins}m"


def session_duration(session):

    if not session["actual_start"]:
        return 0

    end = session["actual_end"]

    if not end:
        end = datetime.now()

    return (end - session["actual_start"]).total_seconds() / 60


def generate_qr(token):

    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=4
    )

    qr.add_data(token)
    qr.make(fit=True)

    image = qr.make_image()

    buffer = BytesIO()
    image.save(buffer, format="PNG")

    return buffer.getvalue()


def logout():

    st.session_state.user = None
    st.session_state.role = None
    st.rerun()


# ============================================================
# LOGIN
# ============================================================

def authenticate(user_id, password, role):

    if role == "Admin":

        for user in USERS["admins"]:
            if user["id"] == user_id and user["password"] == password:
                return user

    elif role == "Tutor":

        for user in USERS["tutors"]:
            if user["id"] == user_id and user["password"] == password:
                return user

    elif role == "Student":

        for user in USERS["students"]:
            if user["id"] == user_id:
                return user

    return None


def login_page():

    st.markdown(
        '<div class="main-title">📚 Tutor Attendance</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">'
        'Tutoring session and attendance management'
        '</div>',
        unsafe_allow_html=True
    )

    left, center, right = st.columns([1, 2, 1])

    with center:

        st.subheader("Sign in")

        role = st.selectbox(
            "I am a",
            ["Tutor", "Student", "Admin"]
        )

        user_id = st.text_input(
            "ID",
            placeholder="Enter your ID"
        )

        if role == "Student":

            st.caption(
                "Students do not need a password."
            )

            password = ""

        else:

            password = st.text_input(
                "Password",
                type="password"
            )

        if st.button(
            "Continue",
            type="primary",
            use_container_width=True
        ):

            user = authenticate(
                user_id,
                password,
                role
            )

            if user:

                st.session_state.user = user
                st.session_state.role = role.lower()

                st.rerun()

            else:

                st.error(
                    "ID or password is incorrect."
                )

    st.divider()

    st.caption(
        "Prototype version — users are authorized "
        "through data/users.json."
    )


# ============================================================
# SIDEBAR
# ============================================================

def sidebar():

    user = st.session_state.user
    role = st.session_state.role

    with st.sidebar:

        st.markdown("## 📚 Tutor Attendance")

        st.divider()

        st.write(
            f"**{user['name']}**"
        )

        st.caption(
            role.capitalize()
        )

        st.divider()

        if role == "admin":

            pages = [
                "Dashboard",
                "Tutors",
                "Students",
                "Sessions",
                "Reports"
            ]

        elif role == "tutor":

            pages = [
                "Dashboard",
                "My Sessions",
                "Create Session"
            ]

        else:

            pages = [
                "Dashboard",
                "Available Sessions",
                "My Attendance"
            ]

        page = st.radio(
            "Navigation",
            pages,
            label_visibility="collapsed"
        )

        st.divider()

        if st.button(
            "Logout",
            use_container_width=True
        ):
            logout()

    return page


# ============================================================
# ADMIN DASHBOARD
# ============================================================

def admin_dashboard():

    st.markdown(
        '<div class="main-title">Admin Dashboard</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">'
        'Overview of the tutoring program'
        '</div>',
        unsafe_allow_html=True
    )

    total_tutors = len(USERS["tutors"])
    total_students = len(USERS["students"])
    total_sessions = len(st.session_state.sessions)

    completed_hours = sum(
        session_duration(s) / 60
        for s in st.session_state.sessions
        if s["status"] == "Completed"
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Tutors",
        total_tutors
    )

    c2.metric(
        "Students",
        total_students
    )

    c3.metric(
        "Sessions",
        total_sessions
    )

    c4.metric(
        "Tutor Hours",
        f"{completed_hours:.1f}"
    )

    st.divider()

    st.subheader("Recent Sessions")

    display_sessions(
        st.session_state.sessions
    )


# ============================================================
# ADMIN — TUTORS
# ============================================================

def admin_tutors():

    st.title("Tutors")

    st.write(
        f"{len(USERS['tutors'])} tutors registered"
    )

    rows = []

    for tutor in USERS["tutors"]:

        sessions = [
            s for s in st.session_state.sessions
            if s["tutor_id"] == tutor["id"]
        ]

        hours = sum(
            session_duration(s) / 60
            for s in sessions
            if s["status"] == "Completed"
        )

        rows.append({
            "ID": tutor["id"],
            "Tutor": tutor["name"],
            "Sessions": len(sessions),
            "Hours": round(hours, 2)
        })

    st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True,
        hide_index=True
    )

    st.info(
        "Tutor management will be connected to "
        "Google Sheets in the next phase."
    )


# ============================================================
# ADMIN — STUDENTS
# ============================================================

def admin_students():

    st.title("Students")

    rows = []

    for student in USERS["students"]:

        attendance = [
            a for a in st.session_state.attendance
            if a["student_id"] == student["id"]
        ]

        minutes = 0

        for a in attendance:

            if a["check_in"] and a["check_out"]:

                minutes += (
                    a["check_out"] -
                    a["check_in"]
                ).total_seconds() / 60

        rows.append({
            "ID": student["id"],
            "Student": student["name"],
            "Sessions": len(attendance),
            "Hours": round(minutes / 60, 2)
        })

    st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# ADMIN — SESSIONS
# ============================================================

def admin_sessions():

    st.title("All Sessions")

    display_sessions(
        st.session_state.sessions
    )


# ============================================================
# SESSION DISPLAY
# ============================================================

def display_sessions(sessions):

    if not sessions:

        st.info("No sessions found.")
        return

    for session in sessions:

        tutor = get_tutor(
            session["tutor_id"]
        )

        student_names = [
            get_student(s)["name"]
            for s in session["student_ids"]
        ]

        with st.container(border=True):

            c1, c2, c3, c4 = st.columns(
                [2, 2, 2, 1]
            )

            c1.write(
                f"**{session['id']}**"
            )

            c1.caption(
                tutor["name"]
            )

            c2.write(
                session["date"].strftime("%b %d, %Y")
            )

            c2.caption(
                session["start_time"].strftime("%I:%M %p")
            )

            c3.write(
                ", ".join(student_names)
            )

            c3.caption(
                f"Expected: "
                f"{format_duration(session['expected_minutes'])}"
            )

            if session["status"] == "Active":

                c4.markdown(
                    '<span class="status-active">'
                    '● ACTIVE'
                    '</span>',
                    unsafe_allow_html=True
                )

            elif session["status"] == "Completed":

                c4.markdown(
                    '<span class="status-completed">'
                    '● COMPLETED'
                    '</span>',
                    unsafe_allow_html=True
                )

            else:

                c4.markdown(
                    '<span class="status-scheduled">'
                    '● SCHEDULED'
                    '</span>',
                    unsafe_allow_html=True
                )


# ============================================================
# TUTOR DASHBOARD
# ============================================================

def tutor_dashboard():

    tutor = st.session_state.user

    st.title(
        f"Welcome, {tutor['name']}"
    )

    tutor_sessions = [
        s for s in st.session_state.sessions
        if s["tutor_id"] == tutor["id"]
    ]

    active = [
        s for s in tutor_sessions
        if s["status"] == "Active"
    ]

    completed = [
        s for s in tutor_sessions
        if s["status"] == "Completed"
    ]

    hours = sum(
        session_duration(s) / 60
        for s in completed
    )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "My Sessions",
        len(tutor_sessions)
    )

    c2.metric(
        "Active",
        len(active)
    )

    c3.metric(
        "Completed Hours",
        f"{hours:.1f}"
    )

    st.divider()

    st.subheader("Today's Sessions")

    today_sessions = [
        s for s in tutor_sessions
        if s["date"] == date.today()
    ]

    display_sessions(today_sessions)


# ============================================================
# TUTOR — MY SESSIONS
# ============================================================

def tutor_sessions_page():

    tutor = st.session_state.user

    st.title("My Sessions")

    sessions = [
        s for s in st.session_state.sessions
        if s["tutor_id"] == tutor["id"]
    ]

    display_sessions(sessions)

    st.divider()

    st.subheader("Manage Session")

    if sessions:

        selected = st.selectbox(
            "Select session",
            sessions,
            format_func=lambda s:
                f"{s['id']} — "
                f"{s['date']} — "
                f"{s['start_time'].strftime('%I:%M %p')}"
        )

        if selected["status"] == "Scheduled":

            if st.button(
                "▶ Start Session",
                type="primary"
            ):

                selected["status"] = "Active"
                selected["actual_start"] = datetime.now()
                selected["qr_token"] = (
                    selected["id"] + "-" +
                    uuid.uuid4().hex[:10]
                )

                st.success(
                    "Session started."
                )

                st.rerun()

        elif selected["status"] == "Active":

            st.success(
                "This session is currently active."
            )

            token = selected["qr_token"]

            st.subheader(
                "Student Attendance QR Code"
            )

            st.write(
                "Ask the student to scan this QR code."
            )

            qr_image = generate_qr(token)

            left, center, right = st.columns(
                [1, 2, 1]
            )

            with center:

                st.markdown(
                    '<div class="qr-box">',
                    unsafe_allow_html=True
                )

                st.image(
                    qr_image,
                    width=300
                )

                st.caption(
                    f"Session code: {token}"
                )

                st.markdown(
                    '</div>',
                    unsafe_allow_html=True
                )

            if st.button(
                "■ End Session",
                type="primary"
            ):

                selected["status"] = "Completed"
                selected["actual_end"] = datetime.now()

                st.success(
                    "Session completed."
                )

                st.rerun()

        else:

            minutes = session_duration(
                selected
            )

            st.info(
                f"Session completed. "
                f"Actual duration: "
                f"**{format_duration(minutes)}**"
            )


# ============================================================
# TUTOR — CREATE SESSION
# ============================================================

def create_session_page():

    tutor = st.session_state.user

    st.title("Create Tutoring Session")

    with st.form("create_session"):

        session_date = st.date_input(
            "Date",
            value=date.today()
        )

        session_time = st.time_input(
            "Start time",
            value=time(16, 0)
        )

        duration = st.selectbox(
            "Expected duration",
            [30, 45, 60, 90, 120],
            format_func=lambda x:
                format_duration(x)
        )

        student_options = {
            student["id"]: student["name"]
            for student in USERS["students"]
        }

        selected_students = st.multiselect(
            "Students",
            options=list(student_options.keys()),
            format_func=lambda x:
                f"{x} — {student_options[x]}"
        )

        submitted = st.form_submit_button(
            "Create Session",
            type="primary"
        )

    if submitted:

        if not selected_students:

            st.error(
                "Please select at least one student."
            )

            return

        new_session = {
            "id": "SES" + uuid.uuid4().hex[:6].upper(),
            "tutor_id": tutor["id"],
            "student_ids": selected_students,
            "date": session_date,
            "start_time": session_time,
            "expected_minutes": duration,
            "status": "Scheduled",
            "actual_start": None,
            "actual_end": None,
            "qr_token": None
        }

        st.session_state.sessions.append(
            new_session
        )

        st.success(
            f"Session {new_session['id']} created."
        )


# ============================================================
# STUDENT DASHBOARD
# ============================================================

def student_dashboard():

    student = st.session_state.user

    st.title(
        f"Welcome, {student['name']}"
    )

    my_attendance = [
        a for a in st.session_state.attendance
        if a["student_id"] == student["id"]
    ]

    completed = 0

    for a in my_attendance:

        if a["check_in"] and a["check_out"]:

            completed += (
                a["check_out"] -
                a["check_in"]
            ).total_seconds() / 3600

    c1, c2 = st.columns(2)

    c1.metric(
        "My Sessions",
        len(my_attendance)
    )

    c2.metric(
        "Hours Attended",
        f"{completed:.1f}"
    )

    st.divider()

    st.subheader("Today's Available Sessions")

    available = [
        s for s in st.session_state.sessions
        if (
            student["id"] in s["student_ids"]
            and s["date"] == date.today()
            and s["status"] == "Active"
        )
    ]

    if not available:

        st.info(
            "There are currently no active sessions "
            "available for you."
        )

    else:

        for session in available:

            tutor = get_tutor(
                session["tutor_id"]
            )

            st.container(border=True).write(
                f"**{tutor['name']}** — "
                f"{session['start_time'].strftime('%I:%M %p')} "
                f"— {session['id']}"
            )


# ============================================================
# STUDENT — AVAILABLE SESSIONS
# ============================================================

def available_sessions_page():

    student = st.session_state.user

    st.title("Available Sessions")

    st.write(
        "These are the sessions currently available "
        "for your student ID."
    )

    sessions = [
        s for s in st.session_state.sessions
        if (
            student["id"] in s["student_ids"]
            and s["status"] == "Active"
        )
    ]

    if not sessions:

        st.info(
            "No active sessions are currently available."
        )

        st.divider()

        st.subheader("Demo QR Attendance")

        st.write(
            "For testing, use the QR code displayed "
            "by a tutor during an active session."
        )

        return

    for session in sessions:

        tutor = get_tutor(
            session["tutor_id"]
        )

        with st.container(border=True):

            st.write(
                f"### {tutor['name']}"
            )

            st.write(
                f"Session: **{session['id']}**"
            )

            st.write(
                f"Started: "
                f"{session['actual_start'].strftime('%I:%M %p')}"
            )

            if st.button(
                "Confirm Attendance",
                key=f"attend_{session['id']}",
                type="primary"
            ):

                existing = [
                    a for a in st.session_state.attendance
                    if (
                        a["session_id"] == session["id"]
                        and a["student_id"] == student["id"]
                    )
                ]

                if existing:

                    st.warning(
                        "You have already checked in."
                    )

                else:

                    attendance = {
                        "id": "ATT" +
                        uuid.uuid4().hex[:6].upper(),
                        "session_id": session["id"],
                        "student_id": student["id"],
                        "check_in": datetime.now(),
                        "check_out": None
                    }

                    st.session_state.attendance.append(
                        attendance
                    )

                    st.success(
                        "Attendance confirmed!"
                    )


# ============================================================
# STUDENT — MY ATTENDANCE
# ============================================================

def student_attendance_page():

    student = st.session_state.user

    st.title("My Attendance")

    records = [
        a for a in st.session_state.attendance
        if a["student_id"] == student["id"]
    ]

    rows = []

    for record in records:

        session = next(
            (
                s for s in st.session_state.sessions
                if s["id"] == record["session_id"]
            ),
            None
        )

        if not session:
            continue

        tutor = get_tutor(
            session["tutor_id"]
        )

        if record["check_out"]:

            minutes = (
                record["check_out"] -
                record["check_in"]
            ).total_seconds() / 60

        else:

            minutes = None

        rows.append({
            "Date": session["date"],
            "Tutor": tutor["name"],
            "Check-in": record["check_in"].strftime(
                "%Y-%m-%d %H:%M"
            ),
            "Check-out":
                record["check_out"].strftime(
                    "%Y-%m-%d %H:%M"
                )
                if record["check_out"]
                else "Still attending",
            "Duration": format_duration(minutes)
        })

    if rows:

        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "No attendance records yet."
        )


# ============================================================
# REPORTS
# ============================================================

def reports_page():

    st.title("Reports")

    st.subheader("Tutor Hours")

    rows = []

    for tutor in USERS["tutors"]:

        sessions = [
            s for s in st.session_state.sessions
            if (
                s["tutor_id"] == tutor["id"]
                and s["status"] == "Completed"
            )
        ]

        hours = sum(
            session_duration(s) / 60
            for s in sessions
        )

        rows.append({
            "Tutor ID": tutor["id"],
            "Tutor": tutor["name"],
            "Sessions": len(sessions),
            "Hours": round(hours, 2)
        })

    df = pd.DataFrame(rows)

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    st.subheader("Detailed Sessions")

    detailed = []

    for session in st.session_state.sessions:

        tutor = get_tutor(
            session["tutor_id"]
        )

        detailed.append({
            "Session": session["id"],
            "Date": session["date"],
            "Tutor": tutor["name"],
            "Students": ", ".join(
                get_student(s)["name"]
                for s in session["student_ids"]
            ),
            "Status": session["status"],
            "Hours": round(
                session_duration(session) / 60,
                2
            )
        })

    detailed_df = pd.DataFrame(detailed)

    st.dataframe(
        detailed_df,
        use_container_width=True,
        hide_index=True
    )

    csv = detailed_df.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        "⬇ Download CSV",
        csv,
        "tutor_sessions.csv",
        "text/csv"
    )


# ============================================================
# MAIN APPLICATION
# ============================================================

if "user" not in st.session_state:
    st.session_state.user = None

if "role" not in st.session_state:
    st.session_state.role = None


if st.session_state.user is None:

    login_page()

else:

    page = sidebar()

    role = st.session_state.role

    # ---------------- ADMIN ----------------

    if role == "admin":

        if page == "Dashboard":
            admin_dashboard()

        elif page == "Tutors":
            admin_tutors()

        elif page == "Students":
            admin_students()

        elif page == "Sessions":
            admin_sessions()

        elif page == "Reports":
            reports_page()

    # ---------------- TUTOR ----------------

    elif role == "tutor":

        if page == "Dashboard":
            tutor_dashboard()

        elif page == "My Sessions":
            tutor_sessions_page()

        elif page == "Create Session":
            create_session_page()

    # ---------------- STUDENT ----------------

    elif role == "student":

        if page == "Dashboard":
            student_dashboard()

        elif page == "Available Sessions":
            available_sessions_page()

        elif page == "My Attendance":
            student_attendance_page()
