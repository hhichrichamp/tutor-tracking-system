import streamlit as st
import pandas as pd
import qrcode
import io
import uuid
import json
import gspread



from urllib.parse import urlencode
from datetime import datetime, timedelta, date, time


from google_sheets import read_classes_from_sheet


try:
    credentials = dict(st.secrets["gcp_service_account"])

    # st.success("✓ Secrets loaded")

    gc = gspread.service_account_from_dict(credentials)

    # st.success("✓ Google authentication successful")

except Exception as e:
    st.error("Google authentication failed")
    st.exception(e)

# ============================================================
# APPLICATION URL
# ============================================================

APP_URL = "https://tutor-center.streamlit.app"

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Tutor Attendance",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# CSS
# ============================================================

st.markdown("""
<style>

.main-title {
    font-size: 2.2rem;
    font-weight: 700;
    margin-bottom: 0;
}

.subtitle {
    color: #666;
    margin-top: 0;
    margin-bottom: 25px;
}

.metric-card {
    background: white;
    padding: 20px;
    border-radius: 12px;
    border: 1px solid #e5e7eb;
    text-align: center;
}

.session-card {
    background: white;
    padding: 18px;
    border-radius: 12px;
    border: 1px solid #e5e7eb;
    margin-bottom: 12px;
}

.status-active {
    color: #15803d;
    font-weight: 700;
}

.status-completed {
    color: #2563eb;
    font-weight: 700;
}

.status-scheduled {
    color: #d97706;
    font-weight: 700;
}

.status-cancelled {
    color: #dc2626;
    font-weight: 700;
}

.qr-box {
    text-align: center;
    padding: 20px;
    background: white;
    border-radius: 12px;
    border: 1px solid #ddd;
}

.small-text {
    color: #666;
    font-size: 0.9rem;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# LOAD USERS
# ============================================================

def load_users():

    with open("data/users.json", "r", encoding="utf-8") as file:
        return json.load(file)

USERS = load_users()



# ============================================================
# SESSION STATE INITIALIZATION
# ============================================================

def initialize_data():

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if "user" not in st.session_state:
        st.session_state.user = None

    if "role" not in st.session_state:
        st.session_state.role = None

    # --------------------------------------------------------
    # INDIVIDUAL TUTORING SESSIONS
    # --------------------------------------------------------

    if "sessions" not in st.session_state:

        now = datetime.now()

        st.session_state.sessions = [         ]

    # --------------------------------------------------------
    # CLASS SCHEDULE
    # --------------------------------------------------------

    if "classes" not in st.session_state:

        now = datetime.now()

        st.session_state.classes =read_classes_from_sheet()

    # --------------------------------------------------------
    # CLASS SIGNUPS
    # --------------------------------------------------------

    if "class_signups" not in st.session_state:

        st.session_state.class_signups = [         ]

    # --------------------------------------------------------
    # ATTENDANCE
    # --------------------------------------------------------

    if "attendance" not in st.session_state:

        st.session_state.attendance = [        ]


initialize_data()







# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_tutor(tutor_id):

    for tutor in USERS["tutors"]:
        if tutor["id"] == tutor_id:
            return tutor

    return None


def get_student(student_id):

    student_id = str(student_id).strip()

    for student in USERS["students"]:

        if str(student["id"]).strip() == student_id:

            return student

    return None
def student_display_name(student):

    return (
        f"{student['first_name']} "
        f"{student['last_name']}"
    )

def get_class(class_id):

    for c in st.session_state.classes:

        if c["id"] == class_id:
            return c

    return None


def get_session(session_id):

    for session in st.session_state.sessions:

        if session["id"] == session_id:
            return session

    return None


def format_duration(seconds):

    if seconds is None:
        return "0h 0m"

    minutes = int(seconds / 60)

    hours = minutes // 60
    mins = minutes % 60

    return f"{hours}h {mins}m"


def calculate_hours(start, end):

    if not start or not end:
        return 0

    return (end - start).total_seconds() / 3600


def generate_qr(data):

    qr = qrcode.QRCode(
        version=1,
        box_size=8,
        border=4
    )

    qr.add_data(data)
    qr.make(fit=True)

    image = qr.make_image()

    buffer = io.BytesIO()

    image.save(buffer, format="PNG")

    return buffer.getvalue()


def logout():

    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.role = None

    st.rerun()






# ============================================================
# AUTHENTICATION
# ============================================================

def authenticate(user_id, password):

    for role in ["admins", "tutors"]:

        for user in USERS[role]:

            if (
                user["id"] == user_id
                and user.get("password") == password
            ):

                return user, role[:-1]

    # Students use their ID only
    for student in USERS["students"]:

        if student["id"] == user_id:

            return student, "student"

    return None, None


# ============================================================
# LOGIN
# ============================================================

def login_page():

    st.markdown(
        '<div class="main-title">📚 Tutor Attendance</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">'
        'Tutor effort and student attendance management'
        '</div>',
        unsafe_allow_html=True
    )

    st.divider()

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:

        st.subheader("Login")

        user_id = st.text_input(
            "User ID",
            placeholder="Example: T001 or S001"
        )

        password = st.text_input(
            "Password",
            type="password",
            help="Students do not need a password."
        )

        if st.button(
            "Login",
            type="primary",
            use_container_width=True
        ):

            user, role = authenticate(
                user_id,
                password
            )

            if user:

                st.session_state.logged_in = True
                st.session_state.user = user
                st.session_state.role = role

                st.rerun()

            else:

                st.error("Invalid User ID or password.")

        st.info(
            "Welcome to the tutor center tracking system. "
            "Students can enter S001–S005 without a password."
        )


# ============================================================
# SIDEBAR
# ============================================================

def sidebar():

    user = st.session_state.user
    role = st.session_state.role

    st.sidebar.markdown("## 📚 Tutor Attendance")

    st.sidebar.write(
        f"**{user['name']}**"
    )

    st.sidebar.caption(
        role.capitalize()
    )

    st.sidebar.divider()

    if role == "admin":

        pages = [
            "Dashboard",
            "Classes",
            "Tutors",
            "Students",
            "Sessions",
            "Reports"
        ]

    elif role == "tutor":

        pages = [
            "Dashboard",
            "Available Classes",
            "My Commitments",
            "My Sessions",
            "Create Tutoring Session"
        ]

    else:

        pages = [
            "Dashboard",
            "Available Sessions",
            "My Attendance"
        ]

    page = st.sidebar.radio(
        "Navigation",
        pages
    )

    st.sidebar.divider()

    if st.sidebar.button(
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
        'Overview of tutoring and classroom support'
        '</div>',
        unsafe_allow_html=True
    )

    total_tutors = len(USERS["tutors"])
    total_students = len(USERS["students"])
    total_classes = len(st.session_state.classes)
    total_sessions = len(st.session_state.sessions)

    total_hours = 0

    for session in st.session_state.sessions:

        total_hours += calculate_hours(
            session["actual_start"],
            session["actual_end"]
        )

    for att in st.session_state.attendance:

        if (
            att["type"] == "Class Support"
            and att["tutor_id"]
        ):

            total_hours += calculate_hours(
                att["check_in"],
                att["check_out"]
            )

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric("Tutors", total_tutors)
    c2.metric("Students", total_students)
    c3.metric("Classes", total_classes)
    c4.metric("Tutoring Sessions", total_sessions)
    c5.metric("Tutor Hours", f"{total_hours:.1f}")

    st.divider()

    st.subheader("Today's Classes")

    today = date.today()

    todays_classes = [
        c for c in st.session_state.classes
        if c["date"] == today
    ]

    if not todays_classes:

        st.info("No classes scheduled today.")

    for c in todays_classes:

        signups = [
            s for s in st.session_state.class_signups
            if s["class_id"] == c["id"]
        ]

        st.markdown(
            f"""
            <div class="session-card">
                <strong>{c['course']}</strong><br>
                {c['title']}<br>
                📅 {c['date']} |
                🕐 {c['start'].strftime('%H:%M')} -
                {c['end'].strftime('%H:%M')} |
                📍 {c['room']}<br>
                👨‍🏫 Tutors signed up:
                {len(signups)} / {c['max_tutors']}
            </div>
            """,
            unsafe_allow_html=True
        )


# ============================================================
# ADMIN CLASSES
# ============================================================

def admin_classes():

    st.markdown(
        '<div class="main-title">Class Schedule</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">'
        'Post classes that tutors can support'
        '</div>',
        unsafe_allow_html=True
    )

    with st.expander(
        "➕ Add a Class",
        expanded=False
    ):

        course = st.text_input(
            "Course",
            placeholder="420-N34-Java Web Programming"
        )

        title = st.text_input(
            "Class / Topic",
            placeholder="Spring Boot / REST"
        )

        c1, c2 = st.columns(2)

        with c1:

            class_date = st.date_input(
                "Date",
                value=date.today()
            )

        with c2:

            room = st.text_input(
                "Room",
                placeholder="B201"
            )

        c1, c2, c3 = st.columns(3)

        with c1:

            start_time = st.time_input(
                "Start time",
                value=time(10, 0)
            )

        with c2:

            end_time = st.time_input(
                "End time",
                value=time(12, 0)
            )

        with c3:

            max_tutors = st.number_input(
                "Maximum tutors",
                min_value=1,
                max_value=10,
                value=2
            )

        if st.button(
            "Post Class",
            type="primary"
        ):

            if not course or not title or not room:

                st.error(
                    "Please complete all fields."
                )

            else:

                new_id = (
                    "CLS"
                    + str(len(st.session_state.classes) + 1)
                )

                token = (
                    "CLASS-"
                    + uuid.uuid4().hex[:8]
                )

                new_class = {

                    "id": new_id,
                    "course": course,
                    "title": title,
                    "date": class_date,
                    "start": datetime.combine(
                        class_date,
                        start_time
                    ),
                    "end": datetime.combine(
                        class_date,
                        end_time
                    ),
                    "room": room,
                    "max_tutors": int(max_tutors),
                    "status": "Open",
                    "qr_token": token
                }

                st.session_state.classes.append(
                    new_class
                )

                st.success(
                    "Class posted successfully."
                )

                st.rerun()

    st.divider()

    for c in sorted(
        st.session_state.classes,
        key=lambda x: x["start"]
    ):

        signups = [
            s for s in st.session_state.class_signups
            if s["class_id"] == c["id"]
        ]

        with st.container(border=True):

            st.subheader(
                f"{c['course']} — {c['title']}"
            )

            c1, c2, c3, c4 = st.columns(4)

            c1.write(
                f"📅 **{c['date']}**"
            )

            c2.write(
                f"🕐 **{c['start'].strftime('%H:%M')} - "
                f"{c['end'].strftime('%H:%M')}**"
            )

            c3.write(
                f"📍 **{c['room']}**"
            )

            c4.write(
                f"👨‍🏫 **{len(signups)} / "
                f"{c['max_tutors']} tutors**"
            )
####################################################################
            if st.button(
                "Display Classroom QR",
                key=f"qr_class_{c['id']}"
            ):

                qr_data = create_qr_url(
                    "class",
                    c["id"],
                    c["qr_token"]
                )

                image = generate_qr(
                    qr_data
                )

                st.image(
                    image,
                    width=300
                )

                st.caption(
                    "Tutors scan this QR code when attending this class."
                )
####################################################################
            if signups:

                names = []

                for signup in signups:

                    tutor = get_tutor(
                        signup["tutor_id"]
                    )

                    if tutor:
                        names.append(
                            tutor["name"]
                        )

                st.write(
                    "Signed up: "
                    + ", ".join(names)
                )

            else:

                st.caption(
                    "No tutors have signed up."
                )


# ============================================================
# ADMIN TUTORS
# ============================================================

def admin_tutors():

    st.markdown(
        '<div class="main-title">Tutors</div>',
        unsafe_allow_html=True
    )

    rows = []

    for tutor in USERS["tutors"]:

        hours = 0

        # Individual tutoring
        for session in st.session_state.sessions:

            if session["tutor_id"] == tutor["id"]:

                hours += calculate_hours(
                    session["actual_start"],
                    session["actual_end"]
                )

        # Classroom support
        for attendance in st.session_state.attendance:

            if (
                attendance["tutor_id"] == tutor["id"]
                and attendance["type"] == "Class Support"
            ):

                hours += calculate_hours(
                    attendance["check_in"],
                    attendance["check_out"]
                )

        rows.append({
            "Tutor ID": tutor["id"],
            "Name": tutor["name"],
            "Hours": round(hours, 2)
        })

    st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# ADMIN STUDENTS
# ============================================================

def admin_students():

    st.markdown(
        '<div class="main-title">Students</div>',
        unsafe_allow_html=True
    )

    rows = []

    for student in USERS["students"]:

        rows.append({
            "Student ID": student["id"],
            "Name": student["name"]
        })

    st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# ADMIN SESSIONS
# ============================================================

def admin_sessions():

    st.markdown(
        '<div class="main-title">Sessions</div>',
        unsafe_allow_html=True
    )

    rows = []

    for session in st.session_state.sessions:

        tutor = get_tutor(
            session["tutor_id"]
        )

        student_names = []

        for sid in session["student_ids"]:

            student = get_student(sid)

            if student:
                student_names.append(
                    student["name"]
                )

        hours = calculate_hours(
            session["actual_start"],
            session["actual_end"]
        )

        rows.append({

            "ID": session["id"],
            "Type": session["type"],
            "Tutor": tutor["name"] if tutor else "",
            "Students": ", ".join(student_names),
            "Date": session["date"],
            "Status": session["status"],
            "Hours": round(hours, 2)

        })

    st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# ADMIN REPORTS
# ============================================================

def admin_reports():

    st.markdown(
        '<div class="main-title">Reports</div>',
        unsafe_allow_html=True
    )

    st.subheader("Tutor Hours")

    rows = []

    for tutor in USERS["tutors"]:

        tutoring_hours = 0
        class_hours = 0

        for session in st.session_state.sessions:

            if session["tutor_id"] == tutor["id"]:

                tutoring_hours += calculate_hours(
                    session["actual_start"],
                    session["actual_end"]
                )

        for attendance in st.session_state.attendance:

            if (
                attendance["tutor_id"] == tutor["id"]
                and attendance["type"] == "Class Support"
            ):

                class_hours += calculate_hours(
                    attendance["check_in"],
                    attendance["check_out"]
                )

        rows.append({

            "Tutor ID": tutor["id"],
            "Tutor": tutor["name"],
            "Tutoring Hours": round(
                tutoring_hours,
                2
            ),
            "Class Support Hours": round(
                class_hours,
                2
            ),
            "Total Hours": round(
                tutoring_hours + class_hours,
                2
            )

        })

    df = pd.DataFrame(rows)

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    csv = df.to_csv(index=False)

    st.download_button(
        "Download CSV",
        csv,
        "tutor_hours.csv",
        "text/csv"
    )

    st.divider()

    st.subheader(
        "Classroom Support Attendance"
    )

    class_rows = []

    for attendance in st.session_state.attendance:

        if attendance["type"] != "Class Support":
            continue

        tutor = get_tutor(
            attendance["tutor_id"]
        )

        c = get_class(
            attendance["class_id"]
        )

        hours = calculate_hours(
            attendance["check_in"],
            attendance["check_out"]
        )

        class_rows.append({

            "Tutor": tutor["name"] if tutor else "",
            "Course": c["course"] if c else "",
            "Class": c["title"] if c else "",
            "Date": c["date"] if c else "",
            "Check In": attendance["check_in"],
            "Check Out": attendance["check_out"],
            "Hours": round(hours, 2)

        })

    if class_rows:

        st.dataframe(
            pd.DataFrame(class_rows),
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "No classroom-support attendance yet."
        )


# ============================================================
# TUTOR DASHBOARD
# ============================================================

def tutor_dashboard():

    tutor_id = st.session_state.user["id"]

    st.markdown(
        '<div class="main-title">Tutor Dashboard</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">'
        'Your tutoring and classroom-support activity'
        '</div>',
        unsafe_allow_html=True
    )

    tutoring_hours = 0
    class_hours = 0

    for session in st.session_state.sessions:

        if session["tutor_id"] == tutor_id:

            tutoring_hours += calculate_hours(
                session["actual_start"],
                session["actual_end"]
            )

    for attendance in st.session_state.attendance:

        if (
            attendance["tutor_id"] == tutor_id
            and attendance["type"] == "Class Support"
        ):

            class_hours += calculate_hours(
                attendance["check_in"],
                attendance["check_out"]
            )

    total_hours = tutoring_hours + class_hours

    signups = [
        s for s in st.session_state.class_signups
        if s["tutor_id"] == tutor_id
    ]

    active_sessions = [
        s for s in st.session_state.sessions
        if (
            s["tutor_id"] == tutor_id
            and s["status"] == "Active"
        )
    ]

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Total Hours",
        f"{total_hours:.1f}"
    )

    c2.metric(
        "Tutoring",
        f"{tutoring_hours:.1f} h"
    )

    c3.metric(
        "Class Support",
        f"{class_hours:.1f} h"
    )

    c4.metric(
        "Class Commitments",
        len(signups)
    )

    st.divider()

    if active_sessions:

        st.subheader(
            "Active Tutoring Session"
        )

        for session in active_sessions:

            st.info(
                f"{session['title']} — "
                f"{session['scheduled_start'].strftime('%H:%M')}"
            )

    st.subheader(
        "Upcoming Commitments"
    )

    upcoming = []

    for signup in signups:

        c = get_class(
            signup["class_id"]
        )

        if c and c["start"] >= datetime.now():

            upcoming.append(c)

    if not upcoming:

        st.info(
            "You have no upcoming classroom-support commitments."
        )

    for c in upcoming:

        st.markdown(
            f"""
            <div class="session-card">
                <strong>{c['course']}</strong><br>
                {c['title']}<br>
                📅 {c['date']} |
                🕐 {c['start'].strftime('%H:%M')} -
                {c['end'].strftime('%H:%M')} |
                📍 {c['room']}
            </div>
            """,
            unsafe_allow_html=True
        )


# ============================================================
# AVAILABLE CLASSES
# ============================================================

def tutor_available_classes():

    tutor_id = st.session_state.user["id"]

    st.markdown(
        '<div class="main-title">Available Classes</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">'
        'Choose classes where you can provide student support'
        '</div>',
        unsafe_allow_html=True
    )

    for c in sorted(
        st.session_state.classes,
        key=lambda x: x["start"]
    ):

        signups = [
            s for s in st.session_state.class_signups
            if s["class_id"] == c["id"]
        ]

        already_signed = any(
            s["tutor_id"] == tutor_id
            for s in signups
        )

        available = (
            len(signups) < c["max_tutors"]
        )

        with st.container(border=True):

            st.subheader(
                f"{c['course']} — {c['title']}"
            )

            c1, c2, c3 = st.columns(3)

            c1.write(
                f"📅 {c['date']}"
            )

            c2.write(
                f"🕐 {c['start'].strftime('%H:%M')} - "
                f"{c['end'].strftime('%H:%M')}"
            )

            c3.write(
                f"📍 {c['room']}"
            )

            st.write(
                f"Tutors: {len(signups)} / {c['max_tutors']}"
            )

            if already_signed:

                st.success(
                    "You are signed up for this class."
                )

            elif not available:

                st.warning(
                    "This class is full."
                )

            elif c["start"] < datetime.now():

                st.info(
                    "This class has already started."
                )

            else:

                if st.button(
                    "Sign Up",
                    key=f"signup_{c['id']}"
                ):

                    st.session_state.class_signups.append({

                        "class_id": c["id"],
                        "tutor_id": tutor_id,
                        "signup_time": datetime.now()

                    })

                    st.success(
                        "You have signed up."
                    )

                    st.rerun()


# ============================================================
# MY COMMITMENTS
# ============================================================

def tutor_commitments():

    tutor_id = st.session_state.user["id"]

    st.markdown(
        '<div class="main-title">My Commitments</div>',
        unsafe_allow_html=True
    )

    my_signups = [

        s for s in st.session_state.class_signups

        if s["tutor_id"] == tutor_id

    ]

    if not my_signups:

        st.info(
            "You have no classroom-support commitments."
        )

        return

    for signup in my_signups:

        c = get_class(
            signup["class_id"]
        )

        if not c:
            continue

        with st.container(border=True):

            st.subheader(
                f"{c['course']} — {c['title']}"
            )

            st.write(
                f"📅 {c['date']}"
            )

            st.write(
                f"🕐 {c['start'].strftime('%H:%M')} - "
                f"{c['end'].strftime('%H:%M')}"
            )

            st.write(
                f"📍 {c['room']}"
            )

            # Find attendance
            attendance = None

            for a in st.session_state.attendance:

                if (
                    a["class_id"] == c["id"]
                    and a["tutor_id"] == tutor_id
                ):

                    attendance = a
                    break

            if attendance:

                if attendance["check_out"]:

                    hours = calculate_hours(
                        attendance["check_in"],
                        attendance["check_out"]
                    )

                    st.success(
                        f"Completed — {hours:.2f} hours"
                    )

                else:

                    st.warning(
                        "You are currently checked in."
                    )

                    if st.button(
                        "Check Out",
                        key=f"class_checkout_{c['id']}"
                    ):

                        attendance["check_out"] = datetime.now()

                        st.success(
                            "Classroom attendance recorded."
                        )

                        st.rerun()

            else:

                if (
                    datetime.now() >= c["start"]
                    and datetime.now() <= c["end"] + timedelta(hours=1)
                ):

                    st.info(
                        "The class is currently available "
                        "for attendance."
                    )

                    if st.button(
                        "Check In",
                        key=f"class_checkin_{c['id']}",
                        type="primary"
                    ):

                        st.session_state.attendance.append({

                            "id": "ATT"
                            + uuid.uuid4().hex[:8],

                            "type": "Class Support",

                            "session_id": None,

                            "class_id": c["id"],

                            "student_id": None,

                            "tutor_id": tutor_id,

                            "check_in": datetime.now(),

                            "check_out": None,

                            "status": "Present"

                        })

                        st.success(
                            "You are checked in."
                        )

                        st.rerun()

                else:

                    st.info(
                        "Check-in will become available "
                        "when the class starts."
                    )


# ============================================================
# TUTOR MY SESSIONS
# ============================================================

def tutor_sessions():

    tutor_id = st.session_state.user["id"]

    st.markdown(
        '<div class="main-title">My Tutoring Sessions</div>',
        unsafe_allow_html=True
    )

    my_sessions = [

        s for s in st.session_state.sessions

        if s["tutor_id"] == tutor_id

    ]

    for session in my_sessions:

        with st.container(border=True):

            st.subheader(
                session["title"]
            )

            st.write(
                f"📅 {session['date']}"
            )

            st.write(
                f"🕐 "
                f"{session['scheduled_start'].strftime('%H:%M')} - "
                f"{session['scheduled_end'].strftime('%H:%M')}"
            )

            students = []

            for sid in session["student_ids"]:

                student = get_student(sid)

                if student:
                    students.append(
                        student["name"]
                    )

            st.write(
                "Students: "
                + ", ".join(students)
            )

            if session["status"] == "Scheduled":

                if st.button(
                    "Start Session",
                    key=f"start_{session['id']}"
                ):

                    session["status"] = "Active"
                    session["actual_start"] = datetime.now()
                    session["qr_token"] = (
                        "SESSION-"
                        + uuid.uuid4().hex
                    )

                    st.rerun()

            elif session["status"] == "Active":

                st.success(
                    "Session is active."
                )

                st.subheader(
                    "Student Attendance QR Code"
                )

                qr_data = create_qr_url(
                    "tutoring",
                    session["id"],
                    session["qr_token"]
                )

                image = generate_qr(
                    qr_data
                )

                col1, col2, col3 = st.columns(
                    [1, 2, 1]
                )

                with col2:

                    st.image(
                        image,
                        width=300
                    )

                    st.caption(
                        "Students scan this QR code "
                        "to confirm attendance."
                    )

                if st.button(
                    "End Session",
                    key=f"end_{session['id']}"
                ):

                    session["status"] = "Completed"
                    session["actual_end"] = datetime.now()

                    st.success(
                        "Session completed."
                    )

                    st.rerun()

            else:

                hours = calculate_hours(
                    session["actual_start"],
                    session["actual_end"]
                )

                st.info(
                    f"Completed — {hours:.2f} hours"
                )


# ============================================================
# CREATE TUTORING SESSION
# ============================================================

def create_tutoring_session():

    tutor_id = st.session_state.user["id"]

    st.markdown(
        '<div class="main-title">'
        'Create Tutoring Session'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">'
        'Create an individual or small-group tutoring session'
        '</div>',
        unsafe_allow_html=True
    )

    title = st.text_input(
        "Session title",
        placeholder="Java Help"
    )

    students = st.multiselect(

        "Students",

        options=[
            s["id"]
            for s in USERS["students"]
        ],

        format_func=lambda sid:
            f"{get_student(sid)['name']}"

    )

    session_date = st.date_input(
        "Date",
        value=date.today()
    )

    c1, c2 = st.columns(2)

    with c1:

        start = st.time_input(
            "Start",
            value=time(14, 0)
        )

    with c2:

        end = st.time_input(
            "End",
            value=time(15, 0)
        )

    if st.button(
        "Create Session",
        type="primary"
    ):

        if not title:

            st.error(
                "Enter a session title."
            )

        elif not students:

            st.error(
                "Select at least one student."
            )

        elif end <= start:

            st.error(
                "End time must be after start time."
            )

        else:

            new_id = (
                "SES"
                + uuid.uuid4().hex[:6].upper()
            )

            st.session_state.sessions.append({

                "id": new_id,

                "type": "Individual Tutoring",

                "tutor_id": tutor_id,

                "student_ids": students,

                "title": title,

                "date": session_date,

                "scheduled_start":
                    datetime.combine(
                        session_date,
                        start
                    ),

                "scheduled_end":
                    datetime.combine(
                        session_date,
                        end
                    ),

                "actual_start": None,

                "actual_end": None,

                "status": "Scheduled",

                "qr_token": None

            })

            st.success(
                "Tutoring session created."
            )


# ============================================================
# STUDENT DASHBOARD
# ============================================================

def student_dashboard():

    student_id = st.session_state.user["id"]

    st.markdown(
        '<div class="main-title">Student Dashboard</div>',
        unsafe_allow_html=True
    )

    my_sessions = [

        s for s in st.session_state.sessions

        if student_id in s["student_ids"]

    ]

    attendance_count = len([

        a for a in st.session_state.attendance

        if a["student_id"] == student_id

    ])

    active = len([

        s for s in my_sessions

        if s["status"] == "Active"

    ])

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "My Sessions",
        len(my_sessions)
    )

    c2.metric(
        "Active Sessions",
        active
    )

    c3.metric(
        "Attendance Records",
        attendance_count
    )

    st.divider()

    st.subheader(
        "Upcoming Sessions"
    )

    for session in my_sessions:

        if session["status"] in [
            "Scheduled",
            "Active"
        ]:

            st.markdown(
                f"""
                <div class="session-card">
                    <strong>{session['title']}</strong><br>
                    Tutor:
                    {get_tutor(session['tutor_id'])['name']}<br>
                    📅 {session['date']} |
                    🕐 {session['scheduled_start'].strftime('%H:%M')} -
                    {session['scheduled_end'].strftime('%H:%M')}<br>
                    Status: {session['status']}
                </div>
                """,
                unsafe_allow_html=True
            )


# ============================================================
# STUDENT AVAILABLE SESSIONS
# ============================================================

def student_available_sessions():

    student_id = st.session_state.user["id"]

    st.markdown(
        '<div class="main-title">Available Sessions</div>',
        unsafe_allow_html=True
    )

    sessions = [

        s for s in st.session_state.sessions

        if (
            student_id in s["student_ids"]
            and s["status"] == "Active"
        )

    ]

    if not sessions:

        st.info(
            "You have no active tutoring sessions."
        )

        return

    for session in sessions:

        tutor = get_tutor(
            session["tutor_id"]
        )

        st.markdown(
            f"""
            <div class="session-card">
                <strong>{session['title']}</strong><br>
                Tutor: {tutor['name']}<br>
                Session ID: {session['id']}
            </div>
            """,
            unsafe_allow_html=True
        )

        already_present = any(

            a["session_id"] == session["id"]
            and a["student_id"] == student_id

            for a in st.session_state.attendance

        )

        if already_present:

            st.success(
                "✓ Your attendance has been recorded."
            )

        else:

            if st.button(
                "Confirm Attendance",
                key=f"attend_{session['id']}"
            ):

                st.session_state.attendance.append({

                    "id":
                        "ATT"
                        + uuid.uuid4().hex[:8],

                    "type":
                        "Tutoring",

                    "session_id":
                        session["id"],

                    "class_id":
                        None,

                    "student_id":
                        student_id,

                    "tutor_id":
                        session["tutor_id"],

                    "check_in":
                        datetime.now(),

                    "check_out":
                        None,

                    "status":
                        "Present"

                })

                st.success(
                    "Attendance confirmed."
                )

                st.rerun()


# ============================================================
# STUDENT ATTENDANCE
# ============================================================

def student_attendance():

    student_id = st.session_state.user["id"]

    st.markdown(
        '<div class="main-title">My Attendance</div>',
        unsafe_allow_html=True
    )

    records = [

        a for a in st.session_state.attendance

        if a["student_id"] == student_id

    ]

    rows = []

    for a in records:

        session = get_session(
            a["session_id"]
        )

        rows.append({

            "Type": a["type"],

            "Session":
                session["title"]
                if session else "",

            "Check In":
                a["check_in"],

            "Status":
                a["status"]

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
# QR CODE FUNCTIONS
# ============================================================

def create_qr_url(action, item_id, token):

    params = {
        "action": action,
        "id": item_id,
        "token": token
    }

    return APP_URL + "/?" + urlencode(params)


def generate_qr(data):

    qr = qrcode.QRCode(
        version=1,
        box_size=8,
        border=4
    )

    qr.add_data(data)
    qr.make(fit=True)

    image = qr.make_image()

    buffer = io.BytesIO()

    image.save(buffer, format="PNG")

    return buffer.getvalue()

# ============================================================
# QR ATTENDANCE PAGE
# ============================================================

def qr_attendance_page():

    params = st.query_params

    action = params.get("action")
    item_id = params.get("id")
    token = params.get("token")

    st.markdown(
        '<div class="main-title">📱 Attendance</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">'
        'Confirm your attendance'
        '</div>',
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # Validate QR parameters
    # --------------------------------------------------------

    if not action or not item_id or not token:

        st.error(
            "Invalid or incomplete QR code."
        )

        return

    # --------------------------------------------------------
    # INDIVIDUAL TUTORING
    # --------------------------------------------------------

    if action == "tutoring":

        tutoring_qr_page(
            item_id,
            token
        )

        return

    # --------------------------------------------------------
    # CLASSROOM SUPPORT
    # --------------------------------------------------------

    if action == "class":

        class_qr_page(
            item_id,
            token
        )

        return

    st.error(
        "Unknown attendance type."
    )



# ============================================================
# TUTORING QR PAGE
# ============================================================

def tutoring_qr_page(session_id, token):

    session = get_session(session_id)

    # --------------------------------------------------------
    # Verify session exists
    # --------------------------------------------------------

    if not session:

        st.error(
            "This tutoring session does not exist."
        )

        return

    # --------------------------------------------------------
    # Verify QR token
    # --------------------------------------------------------

    if session["qr_token"] != token:

        st.error(
            "Invalid QR code."
        )

        return

    # --------------------------------------------------------
    # Verify session is active
    # --------------------------------------------------------

    if session["status"] != "Active":

        st.warning(
            "This tutoring session is not currently active."
        )

        return

    tutor = get_tutor(
        session["tutor_id"]
    )

    # --------------------------------------------------------
    # Display session information
    # --------------------------------------------------------

    st.subheader(
        "📚 " + session["title"]
    )

    st.write(
        f"**Tutor:** {tutor['name']}"
    )

    st.write(
        f"**Session ID:** {session['id']}"
    )

    st.divider()

    st.subheader(
        "Student Attendance"
    )

    st.write(
        "Enter your student number to confirm your attendance."
    )

    # --------------------------------------------------------
    # Student enters student number
    # --------------------------------------------------------

    student_id = st.text_input(
        "Student Number",
        placeholder="Example: 2431744",
        max_chars=20
    )

    # --------------------------------------------------------
    # Confirm attendance
    # --------------------------------------------------------

    if st.button(
        "✓ Confirm My Attendance",
        type="primary",
        use_container_width=True
    ):

        # -----------------------------------------------
        # Check that student number was entered
        # -----------------------------------------------

        if not student_id:

            st.error(
                "Please enter your student number."
            )

            return

        student_id = student_id.strip()

        # -----------------------------------------------
        # Validate student against users.json
        # -----------------------------------------------

        student = get_student(
            student_id
        )

        if not student:

            st.error(
                "Student number not found."
            )

            st.warning(
                "Please enter the student number "
                "exactly as it appears in your student record."
            )

            return

        # -----------------------------------------------
        # IMPORTANT:
        # Verify student belongs to this session
        # -----------------------------------------------

        if student_id not in [
            str(sid)
            for sid in session["student_ids"]
        ]:

            st.error(
                "You are not registered for this "
                "tutoring session."
            )

            return

        # -----------------------------------------------
        # Check for duplicate attendance
        # -----------------------------------------------

        already_present = any(

            str(a["session_id"]) == str(session_id)
            and str(a["student_id"]) == str(student_id)

            for a in st.session_state.attendance

        )

        if already_present:

            st.success(
                "✓ Your attendance has already been recorded."
            )

            return

        # -----------------------------------------------
        # Record attendance
        # -----------------------------------------------

        st.session_state.attendance.append({

            "id":
                "ATT"
                + uuid.uuid4().hex[:8].upper(),

            "type":
                "Tutoring",

            "session_id":
                session_id,

            "class_id":
                None,

            "student_id":
                student_id,

            "tutor_id":
                session["tutor_id"],

            "check_in":
                datetime.now(),

            "check_out":
                None,

            "status":
                "Present"

        })

        # -----------------------------------------------
        # Confirmation
        # -----------------------------------------------

        st.success(
            "✓ Attendance confirmed successfully!"
        )

        st.write(
            f"**Student:** "
            f"{student_display_name(student)}"
        )

        st.write(
            f"**Student Number:** {student_id}"
        )

        st.write(
            f"**Time:** "
            f"{datetime.now().strftime('%H:%M:%S')}"
        )

        st.balloons()




# ============================================================
# CLASSROOM SUPPORT QR PAGE
# ============================================================

def class_qr_page(class_id, token):

    class_event = get_class(
        class_id
    )

    if not class_event:

        st.error(
            "This class does not exist."
        )

        return

    # --------------------------------------------------------
    # Verify QR token
    # --------------------------------------------------------

    if class_event["qr_token"] != token:

        st.error(
            "Invalid classroom QR code."
        )

        return

    st.subheader(
        class_event["course"]
    )

    st.write(
        f"**Class:** {class_event['title']}"
    )

    st.write(
        f"**Room:** {class_event['room']}"
    )

    st.write(
        f"**Time:** "
        f"{class_event['start'].strftime('%H:%M')} - "
        f"{class_event['end'].strftime('%H:%M')}"
    )

    st.divider()

    # --------------------------------------------------------
    # Tutor identifies themselves
    # --------------------------------------------------------

    tutor_id = st.selectbox(

        "Select your tutor ID",

        options=[
            tutor["id"]
            for tutor in USERS["tutors"]
        ],

        format_func=lambda tid:
            f"{tid} — "
            f"{get_tutor(tid)['name']}"

    )

    tutor = get_tutor(
        tutor_id
    )

    # --------------------------------------------------------
    # Verify tutor is signed up
    # --------------------------------------------------------

    signed_up = any(

        s["class_id"] == class_id
        and s["tutor_id"] == tutor_id

        for s in st.session_state.class_signups

    )

    if not signed_up:

        st.error(
            "You are not signed up for this class."
        )

        return

    st.success(
        f"You are signed up for this class, "
        f"{tutor['name']}."
    )

    # --------------------------------------------------------
    # Check existing attendance
    # --------------------------------------------------------

    attendance = None

    for a in st.session_state.attendance:

        if (
            a["class_id"] == class_id
            and a["tutor_id"] == tutor_id
            and a["type"] == "Class Support"
        ):

            attendance = a

            break

    # --------------------------------------------------------
    # No attendance yet → CHECK IN
    # --------------------------------------------------------

    if attendance is None:

        if st.button(
            "✓ Check In",
            type="primary",
            use_container_width=True
        ):

            st.session_state.attendance.append({

                "id":
                    "ATT"
                    + uuid.uuid4().hex[:8].upper(),

                "type":
                    "Class Support",

                "session_id":
                    None,

                "class_id":
                    class_id,

                "student_id":
                    None,

                "tutor_id":
                    tutor_id,

                "check_in":
                    datetime.now(),

                "check_out":
                    None,

                "status":
                    "Present"

            })

            st.success(
                "You are now checked in."
            )

            st.rerun()

    # --------------------------------------------------------
    # Already checked in → CHECK OUT
    # --------------------------------------------------------

    elif attendance["check_out"] is None:

        st.success(
            "✓ You are currently checked in."
        )

        st.write(
            f"Check-in time: "
            f"**{attendance['check_in'].strftime('%H:%M:%S')}**"
        )

        if st.button(
            "Check Out",
            type="primary",
            use_container_width=True
        ):

            attendance["check_out"] = datetime.now()

            hours = calculate_hours(
                attendance["check_in"],
                attendance["check_out"]
            )

            st.success(
                f"Checked out successfully. "
                f"Time recorded: **{hours:.2f} hours**."
            )

            st.rerun()

    # --------------------------------------------------------
    # Already completed
    # --------------------------------------------------------

    else:

        hours = calculate_hours(
            attendance["check_in"],
            attendance["check_out"]
        )

        st.success(
            "✓ Classroom attendance completed."
        )

        st.write(
            f"Check-in: "
            f"{attendance['check_in'].strftime('%H:%M:%S')}"
        )

        st.write(
            f"Check-out: "
            f"{attendance['check_out'].strftime('%H:%M:%S')}"
        )

        st.write(
            f"**Hours: {hours:.2f}**"
        )







# ============================================================
# MAIN APPLICATION
# ============================================================

def main():

    # ========================================================
    # HANDLE QR ATTENDANCE LINKS
    # ========================================================

    params = st.query_params

    if (
        params.get("action")
        and params.get("id")
        and params.get("token")
    ):

        qr_attendance_page()

        return

    # ========================================================
    # NORMAL LOGIN APPLICATION
    # ========================================================

    if not st.session_state.logged_in:

        login_page()

        return

    page = sidebar()

    role = st.session_state.role

    # ... rest of your existing main()

    # --------------------------------------------------------
    # ADMIN
    # --------------------------------------------------------

    if role == "admin":

        if page == "Dashboard":
            admin_dashboard()

        elif page == "Classes":
            admin_classes()

        elif page == "Tutors":
            admin_tutors()

        elif page == "Students":
            admin_students()

        elif page == "Sessions":
            admin_sessions()

        elif page == "Reports":
            admin_reports()

    # --------------------------------------------------------
    # TUTOR
    # --------------------------------------------------------

    elif role == "tutor":

        if page == "Dashboard":
            tutor_dashboard()

        elif page == "Available Classes":
            tutor_available_classes()

        elif page == "My Commitments":
            tutor_commitments()

        elif page == "My Sessions":
            tutor_sessions()

        elif page == "Create Tutoring Session":
            create_tutoring_session()

    # --------------------------------------------------------
    # STUDENT
    # --------------------------------------------------------

    elif role == "student":

        if page == "Dashboard":
            student_dashboard()

        elif page == "Available Sessions":
            student_available_sessions()

        elif page == "My Attendance":
            student_attendance()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()