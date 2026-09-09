import streamlit as st
import pandas as pd
import qrcode
import io
import uuid
import json
import gspread

from streamlit_calendar import calendar

from urllib.parse import urlencode
from datetime import datetime, timedelta, date, time


from google_sheets import (
    read_classes_from_sheet,
    add_class_to_sheet,
    read_sessions_from_sheet, read_class_signups_from_sheet, read_attendance_from_sheet,
    add_session_to_sheet, add_class_signup_to_sheet, add_attendance_to_sheet    ,
    update_session_in_sheet, update_attendance_checkout_in_sheet
)

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

        st.session_state.sessions = read_sessions_from_sheet()

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

        st.session_state.class_signups = read_class_signups_from_sheet()

    # --------------------------------------------------------
    # ATTENDANCE
    # --------------------------------------------------------

    if "attendance" not in st.session_state:

        st.session_state.attendance = read_attendance_from_sheet()

         


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

    return (        f"{student['name']} "    )

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
            "Login to access your dashboard."
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

        total_hours += tutoring_hours_earned(session)

    for att in st.session_state.attendance:

        if (
            att["type"] == "Class Support"
            and att["tutor_id"]
        ):

            total_hours += tutoring_hours_earned(session)

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

                new_id = "CLS" + uuid.uuid4().hex[:8].upper()

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
                add_class_to_sheet(new_class)

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
        key=lambda x: x["start"],
        reverse=True
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

    st.markdown(
        '<div class="subtitle">'
        'Tutor commitments and tutoring activity'
        '</div>',
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # Tutor selection
    # --------------------------------------------------------

    tutor_options = {
        tutor["id"]: tutor["name"]
        for tutor in USERS["tutors"]
    }

    selected_tutor_id = st.selectbox(
        "Select tutor",
        options=list(tutor_options.keys()),
        format_func=lambda tid:
            f"{tid} — {tutor_options[tid]}"
    )

    tutor = get_tutor(
        selected_tutor_id
    )

    # --------------------------------------------------------
    # Calculate accomplished hours
    # --------------------------------------------------------

    tutoring_hours = 0
    class_hours = 0

    for session in st.session_state.sessions:

        if session["tutor_id"] == selected_tutor_id:

            tutoring_hours += tutoring_hours_earned(
                session
            )

    for attendance in st.session_state.attendance:

        if (
            attendance["tutor_id"] == selected_tutor_id
            and attendance["type"] == "Class Support"
        ):

            class_hours += calculate_hours(
                attendance["check_in"],
                attendance["check_out"]
            )

    total_hours = tutoring_hours + class_hours

    # --------------------------------------------------------
    # Metrics
    # --------------------------------------------------------

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Tutoring Hours",
        f"{tutoring_hours:.2f}"
    )

    c2.metric(
        "Class Support Hours",
        f"{class_hours:.2f}"
    )

    c3.metric(
        "Total Hours",
        f"{total_hours:.2f}"
    )

    st.divider()

    # ========================================================
    # COMMITMENTS
    # ========================================================

    st.subheader(
        "Commitments"
    )

    commitments = get_tutor_commitments(
        selected_tutor_id
    )

    if not commitments:

        st.info(
            "This tutor has no commitments."
        )

    else:

        rows = []

        for commitment in commitments:

            rows.append({

                "Type":
                    commitment["type"],

                "Title":
                    commitment["title"],

                "Date":
                    commitment["date"],

                "Start":
                    commitment["start"].strftime(
                        "%H:%M"
                    ),

                "End":
                    commitment["end"].strftime(
                        "%H:%M"
                    ),

                "Location":
                    commitment["location"],

                "Status":
                    commitment["status"]

            })

        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True
        )

    st.divider()

    # ========================================================
    # TUTORING SESSIONS
    # ========================================================

    st.subheader(
        "Tutoring Sessions"
    )

    sessions = [

        s for s in st.session_state.sessions

        if s["tutor_id"] == selected_tutor_id

    ]

    sessions.sort(
        key=lambda s: s["scheduled_start"]
    )

    if not sessions:

        st.info(
            "No tutoring sessions."
        )

    else:

        rows = []

        for session in sessions:

            attendance = get_session_attendance(
                session["id"]
            )

            credited_hours = tutoring_hours_earned(
                session
            )

            rows.append({

                "Date":
                    session["date"],

                "Session":
                    session["title"],

                "Scheduled":
                    (
                        session["scheduled_start"]
                        .strftime("%H:%M")
                        + " - "
                        + session["scheduled_end"]
                        .strftime("%H:%M")
                    ),

                "Students Registered":
                    len(
                        session.get(
                            "student_ids",
                            []
                        )
                    ),

                "Students Attended":
                    len(attendance),

                "Status":
                    session["status"],

                "Hours Earned":
                    round(
                        credited_hours,
                        2
                    )

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

        hours =  tutoring_hours_earned(session)
        attendance_count = len(
            get_session_attendance(
                session["id"]
            )
        )
        rows.append({

            "ID": session["id"],
            "Type": session["type"],
            "Tutor": tutor["name"] if tutor else "",
            "Students": ", ".join(student_names),
            "Date": session["date"],
            "Status": session["status"],
            "Hours": round(hours, 2),
            "Students Registered": len(session.get("student_ids", [])),
            "Students Attended": attendance_count,
            "Hours Earned": round(hours, 2)
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

    st.markdown(
        '<div class="subtitle">'
        'Tutoring, classroom support and attendance reports'
        '</div>',
        unsafe_allow_html=True
    )

    tab1, tab2, tab3 = st.tabs([
        "Overall Summary",
        "Tutor Drilldown",
        "Student Report"
    ])

    # ========================================================
    # OVERALL
    # ========================================================

    with tab1:

        total_tutoring_hours = 0
        total_class_hours = 0

        for session in st.session_state.sessions:

            total_tutoring_hours += (
                tutoring_hours_earned(session)
            )

        for attendance in st.session_state.attendance:

            if (
                attendance["type"] == "Class Support"
            ):

                total_class_hours += calculate_hours(
                    attendance["check_in"],
                    attendance["check_out"]
                )

        total_hours = (
            total_tutoring_hours
            + total_class_hours
        )

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "Tutoring Hours",
            f"{total_tutoring_hours:.2f}"
        )

        c2.metric(
            "Class Support Hours",
            f"{total_class_hours:.2f}"
        )

        c3.metric(
            "Total Tutor Hours",
            f"{total_hours:.2f}"
        )

        c4.metric(
            "Tutoring Sessions",
            len(st.session_state.sessions)
        )

        st.divider()

        rows = []

        for tutor in USERS["tutors"]:

            tutoring_hours = sum(
                tutoring_hours_earned(s)
                for s in st.session_state.sessions
                if s["tutor_id"] == tutor["id"]
            )

            class_hours = sum(
                calculate_hours(
                    a["check_in"],
                    a["check_out"]
                )
                for a in st.session_state.attendance
                if (
                    a["type"] == "Class Support"
                    and a["tutor_id"] == tutor["id"]
                )
            )

            rows.append({

                "Tutor":
                    tutor["name"],

                "Tutoring Hours":
                    round(
                        tutoring_hours,
                        2
                    ),

                "Class Support Hours":
                    round(
                        class_hours,
                        2
                    ),

                "Total Hours":
                    round(
                        tutoring_hours + class_hours,
                        2
                    )

            })

        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True
        )

    # ========================================================
    # TUTOR DRILLDOWN
    # ========================================================

    with tab2:

        tutor_options = {
            tutor["id"]: tutor["name"]
            for tutor in USERS["tutors"]
        }

        selected_tutor_id = st.selectbox(
            "Tutor",
            options=list(tutor_options.keys()),
            format_func=lambda tid:
                f"{tid} — {tutor_options[tid]}",
            key="report_tutor"
        )

        sessions = [

            s for s in st.session_state.sessions

            if s["tutor_id"] == selected_tutor_id

        ]

        # ----------------------------------------------------
        # Only completed / credited sessions
        # ----------------------------------------------------

        sessions = [
            s for s in sessions
            if tutoring_hours_earned(s) > 0
        ]

        sessions.sort(
            key=lambda s: s["scheduled_start"]
        )

        cumulative_hours = 0
        current_group = 1

        rows = []

        for session in sessions:

            hours = tutoring_hours_earned(
                session
            )

            # Group according to cumulative hours
            group_number = (
                int(cumulative_hours // 5)
                + 1
            )

            cumulative_hours += hours

            rows.append({

                "Group":
                    f"Group {group_number}",

                "Date":
                    session["date"],

                "Session":
                    session["title"],

                "Start":
                    session["actual_start"],

                "End":
                    session["actual_end"],

                "Students Attended":
                    len(
                        get_session_attendance(
                            session["id"]
                        )
                    ),

                "Hours":
                    round(
                        hours,
                        2
                    ),

                "Cumulative Hours":
                    round(
                        cumulative_hours,
                        2
                    )

            })

        if rows:

            st.dataframe(
                pd.DataFrame(rows),
                use_container_width=True,
                hide_index=True
            )

            st.metric(
                "Total Tutoring Hours",
                f"{cumulative_hours:.2f}"
            )

        else:

            st.info(
                "This tutor has no credited tutoring hours yet."
            )

    # ========================================================
    # STUDENT REPORT
    # ========================================================

    with tab3:

        student_options = {
            student["id"]: student["name"]
            for student in USERS["students"]
        }

        selected_student_id = st.selectbox(
            "Student",
            options=list(student_options.keys()),
            format_func=lambda sid:
                f"{sid} — {student_options[sid]}",
            key="report_student"
        )

        records = [

            a for a in st.session_state.attendance

            if (
                a["student_id"] == selected_student_id
                and a["type"] == "Tutoring"
            )

        ]

        records.sort(
            key=lambda a: a["check_in"]
        )

        rows = []

        for attendance in records:

            session = get_session(
                attendance["session_id"]
            )

            tutor = (
                get_tutor(
                    session["tutor_id"]
                )
                if session
                else None
            )

            rows.append({

                "Date":
                    (
                        session["date"]
                        if session
                        else ""
                    ),

                "Session":
                    (
                        session["title"]
                        if session
                        else ""
                    ),

                "Tutor":
                    (
                        tutor["name"]
                        if tutor
                        else ""
                    ),

                "Scheduled":
                    (
                        session["scheduled_start"]
                        .strftime("%H:%M")
                        + " - "
                        + session["scheduled_end"]
                        .strftime("%H:%M")
                        if session
                        else ""
                    ),

                "Attendance":
                    attendance["check_in"],

                "Status":
                    attendance["status"]

            })

        if rows:

            st.dataframe(
                pd.DataFrame(rows),
                use_container_width=True,
                hide_index=True
            )

            st.metric(
                "Sessions Attended",
                len(rows)
            )

        else:

            st.info(
                "This student has no tutoring attendance records."
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

            tutoring_hours +=  tutoring_hours_earned(session)

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
        key=lambda x: x["start"],
        reverse=True
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

                    # in tutor_available_classes(), replace the append block:
                    st.session_state.class_signups.append({
                        "id": "SGN" + uuid.uuid4().hex[:8].upper(),   # ← add this
                        "class_id": c["id"],
                        "tutor_id": tutor_id,
                        "signup_time": datetime.now()
                    })
                    add_class_signup_to_sheet(st.session_state.class_signups[-1])

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
                        # ← add this right after:
                        update_attendance_checkout_in_sheet(
                            attendance["id"],
                            attendance["check_out"]
                        )
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
                        add_attendance_to_sheet(st.session_state.attendance[-1])
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

    # --------------------------------------------------------
    # Get this tutor's sessions
    # --------------------------------------------------------
    my_sessions = [
        s for s in st.session_state.sessions
        if s["tutor_id"] == tutor_id
    ]

    # Sort sessions in descending order by date and time
    my_sessions.sort(
        key=lambda x: (
            x["date"],
            x["scheduled_start"]
        ),
        reverse=True
    )

    for session in my_sessions:

        # ====================================================
        # SCHEDULED START / END
        # ====================================================

        scheduled_start = session["scheduled_start"]
        scheduled_end = session["scheduled_end"]

        # Convert strings if necessary
        if isinstance(scheduled_start, str):
            scheduled_start = datetime.fromisoformat(
                scheduled_start
            )

        if isinstance(scheduled_end, str):
            scheduled_end = datetime.fromisoformat(
                scheduled_end
            )

        # Latest time the tutor can START
        #
        # Example:
        # 10:00 - 11:00
        # latest start = 10:45
        latest_start = (
            scheduled_end - timedelta(minutes=15)
        )

        # Latest time the tutor can MANUALLY END
        #
        # Example:
        # 10:00 - 11:00
        # maximum end = 11:15
        maximum_end = (
            scheduled_end + timedelta(minutes=15)
        )

        with st.container(border=True):

            st.subheader(
                session["title"]
            )

            st.write(
                f"📅 {session['date']}"
            )

            st.write(
                f"🕐 "
                f"{scheduled_start.strftime('%H:%M')} - "
                f"{scheduled_end.strftime('%H:%M')}"
            )
            # ------------------------------------------------
            # Students
            # ------------------------------------------------

            students = []

            for sid in session.get("student_ids", []):

                student = get_student(sid)

                if student:
                    students.append(
                        student["name"]
                    )

            if students:

                st.write(
                    "Registered students: "
                    + ", ".join(students)
                )

            else:

                st.info(
                    "No students registered yet."
                )

            # ====================================================
            # SCHEDULED
            # ====================================================

            if session["status"] == "Scheduled":

                now = datetime.now()

                # --------------------------------------------
                # Too early
                # --------------------------------------------

                if now < scheduled_start:

                    st.info(
                        f"Session cannot be started before "
                        f"{scheduled_start.strftime('%H:%M')}."
                    )

                # --------------------------------------------
                # Too late
                # --------------------------------------------

                elif now > latest_start:

                    st.warning(
                        f"Session can no longer be started. "
                        f"The latest start time was "
                        f"{latest_start.strftime('%H:%M')}."
                    )

                # --------------------------------------------
                # Valid start period
                # --------------------------------------------

                else:

                    if st.button(
                        "Start Session",
                        key=f"start_{session['id']}"
                    ):

                        now = datetime.now()

                        # ------------------------------------
                        # Double-check the time.
                        #
                        # This protects against the page being
                        # open while the allowed start window
                        # changes.
                        # ------------------------------------

                        if (
                            now >= scheduled_start
                            and now <= latest_start
                        ):

                            session["status"] = "Active"

                            session["actual_start"] = now

                            # --------------------------------
                            # Default session length = 15 min
                            # --------------------------------

                            session["actual_end"] = (
                                now + timedelta(minutes=15)
                            )

                            session["qr_token"] = (
                                "SESSION-"
                                + uuid.uuid4().hex
                            )

                            # --------------------------------
                            # Persist to Google Sheet
                            # --------------------------------

                            update_session_in_sheet(
                                session["id"],
                                {
                                    "status": session["status"],
                                    "actual_start": session["actual_start"],
                                    "actual_end": session["actual_end"],
                                    "qr_token": session["qr_token"],
                                }
                            )

                            st.rerun()

                        else:

                            st.error(
                                "The session can no longer be started."
                            )

            # ====================================================
            # ACTIVE
            # ====================================================

            elif session["status"] == "Active":

                st.success("Session is active.")

                # The initial actual_end was set to:
                # actual_start + 15 minutes
                #
                # This value stays unchanged if the tutor forgets
                # to click End Session.

                actual_end = session.get("actual_end")

                if actual_end:
                    st.info(
                        "Default session end: "
                        + actual_end.strftime("%H:%M")
                    )

                st.subheader(
                    "Student Attendance QR Code"
                )

                qr_data = create_qr_url(
                    "tutoring",
                    session["id"],
                    session["qr_token"]
                )

                image = generate_qr(qr_data)

                col1, col2, col3 = st.columns([1, 2, 1])

                with col2:

                    st.image(
                        image,
                        width=300
                    )

                    st.caption(
                        "Students scan this QR code "
                        "to confirm attendance."
                    )

                # ------------------------------------------------
                # End Session
                # ------------------------------------------------

                if st.button(
                    "End Session",
                    key=f"end_{session['id']}"
                ):

                    now = datetime.now()

                    # ------------------------------------------------
                    # Tutor can manually end the session only up to
                    # scheduled_end + 15 minutes.
                    # ------------------------------------------------

                    if now <= maximum_end:

                        session["status"] = "Completed"

                        # Actual session length is:
                        #
                        # actual_end - actual_start
                        #
                        # This can be longer than 15 minutes, but
                        # never beyond scheduled_end + 15 minutes.

                        session["actual_end"] = now

                        update_session_in_sheet(
                            session["id"],
                            {
                                "status": session["status"],
                                "actual_end": session["actual_end"],
                            }
                        )

                        st.success(
                            "Session completed."
                        )

                        st.rerun()

                    else:

                        # ------------------------------------------------
                        # Tutor forgot to end the session.
                        #
                        # DO NOT change actual_end.
                        #
                        # The original 15-minute default remains.
                        # ------------------------------------------------

                        st.warning(
                            "The session end time has passed. "
                            "The default 15-minute session length "
                            "will be recorded because the session "
                            "was not ended on time."
                        )

            # ====================================================
            # COMPLETED
            # ====================================================

            elif session["status"] == "Completed":

                if (
                    session.get("actual_start")
                    and session.get("actual_end")
                ):

                    hours =  tutoring_hours_earned(session)

                    st.info(
                        f"Completed — {hours:.2f} hours"
                    )

                else:

                    st.info(
                        "Completed"
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
        'Set a time when you are available for tutoring. '
        'Students can then discover and register for the session.'
        '</div>',
        unsafe_allow_html=True
    )

    title = st.text_input(
        "Session title",
        placeholder="Java Help"
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

            return

        if end <= start:

            st.error(
                "End time must be after start time."
            )

            return

        scheduled_start = datetime.combine(
            session_date,
            start
        )

        scheduled_end = datetime.combine(
            session_date,
            end
        )

        # ----------------------------------------------------
        # A session must be long enough to permit the
        # 15-minute default tutoring period.
        # ----------------------------------------------------

        if (
            scheduled_end - scheduled_start
        ) < timedelta(minutes=15):

            st.error(
                "A tutoring session must be at least "
                "15 minutes long."
            )

            return

        new_id = (
            "SES"
            + uuid.uuid4().hex[:6].upper()
        )

        new_session = {

            "id": new_id,

            "type": "Individual Tutoring",

            "tutor_id": tutor_id,

            # Students register themselves later
            "student_ids": [],

            "title": title,

            "date": session_date,

            "scheduled_start": scheduled_start,

            "scheduled_end": scheduled_end,

            "actual_start": None,

            "actual_end": None,

            "status": "Scheduled",

            "qr_token": None
        }

        st.session_state.sessions.append(
            new_session
        )

        add_session_to_sheet(
            new_session
        )

        st.success(
            "Tutoring session created successfully. "
            "Students can now register for it."
        )

        st.rerun()

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

    st.markdown(
        '<div class="subtitle">'
        'Browse tutoring sessions and register for one that '
        'fits your schedule.'
        '</div>',
        unsafe_allow_html=True
    )

    now = datetime.now()

    available_sessions = []

    for session in st.session_state.sessions:

        # Only scheduled sessions can be registered for
        if session["status"] != "Scheduled":
            continue

        # Do not show sessions that have already started
        if session["scheduled_start"] <= now:
            continue

        # Do not show sessions that already have this student
        if student_id in [
            str(sid)
            for sid in session.get("student_ids", [])
        ]:
            continue

        available_sessions.append(session)

    # --------------------------------------------------------
    # Calendar
    # --------------------------------------------------------

    events = []

    for session in available_sessions:

        events.append({

            "title":
                f"{session['title']} — "
                f"{get_tutor(session['tutor_id'])['name']}",

            "start":
                session["scheduled_start"].isoformat(),

            "end":
                session["scheduled_end"].isoformat(),

            "id":
                session["id"],

            "backgroundColor":
                "#2563eb",

            "borderColor":
                "#2563eb"

        })

    st.subheader("Calendar")

    if events:

        calendar_options = {

            "initialView":
                "dayGridMonth",

            "headerToolbar": {
                "left":
                    "prev,next today",

                "center":
                    "title",

                "right":
                    "dayGridMonth,timeGridWeek"
            },

            "height":
                650,

            "slotMinTime":
                "08:00:00",

            "slotMaxTime":
                "22:00:00",

            "allDaySlot":
                False
        }

        calendar(
            events=events,
            options=calendar_options
        )

    else:

        st.info(
            "There are currently no open tutoring sessions."
        )

    st.divider()

    # --------------------------------------------------------
    # Open sessions
    # --------------------------------------------------------

    st.subheader("Open Tutoring Sessions")

    if not available_sessions:

        st.info(
            "No sessions are currently available "
            "for registration."
        )

        return

    # Chronological order
    available_sessions.sort(
        key=lambda s: s["scheduled_start"]
    )

    for session in available_sessions:

        tutor = get_tutor(
            session["tutor_id"]
        )

        registered = len(
            session.get("student_ids", [])
        )

        with st.container(border=True):

            st.subheader(
                session["title"]
            )

            st.write(
                f"**Tutor:** "
                f"{tutor['name'] if tutor else ''}"
            )

            st.write(
                f"📅 "
                f"{session['scheduled_start'].strftime('%Y-%m-%d')}"
            )

            st.write(
                f"🕐 "
                f"{session['scheduled_start'].strftime('%H:%M')} - "
                f"{session['scheduled_end'].strftime('%H:%M')}"
            )

            st.write(
                f"👥 Registered students: {registered}"
            )

            if st.button(
                "Register for Session",
                key=f"register_{session['id']}",
                type="primary"
            ):

                # Re-fetch session state before modifying it
                current_session = get_session(
                    session["id"]
                )

                if not current_session:

                    st.error(
                        "Session no longer exists."
                    )

                    continue

                if current_session["status"] != "Scheduled":

                    st.error(
                        "This session is no longer available."
                    )

                    continue

                if student_id not in [
                    str(sid)
                    for sid in current_session.get(
                        "student_ids", []
                    )
                ]:

                    current_session.setdefault(
                        "student_ids",
                        []
                    ).append(student_id)

                    update_session_in_sheet(
                        current_session["id"],
                        {
                            "student_ids":
                                current_session["student_ids"]
                        }
                    )

                    st.success(
                        "You have successfully registered "
                        "for this tutoring session."
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
        # IMPORTANT:
        # Verify that session has started
        # -----------------------------------------------
        if datetime.now() < session["scheduled_start"]:
            st.error(
                "Attendance cannot be recorded before "
                "the scheduled session start."
            )
            return

        maximum_end = (
            session["scheduled_end"]
            + timedelta(minutes=15)
        )

        if datetime.now() > maximum_end:
            st.error(
                "The attendance period for this session has ended."
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
        add_attendance_to_sheet(
            st.session_state.attendance[-1]     
        )
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
            add_attendance_to_sheet(st.session_state.attendance[-1])
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
            update_attendance_checkout_in_sheet(attendance["id"], attendance["check_out"])

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
# TUTORING SESSION HELPERS
# ============================================================

def session_has_attendance(session_id):
    """
    Returns True if at least one student has confirmed
    attendance for this tutoring session.
    """

    return any(
        a["type"] == "Tutoring"
        and str(a["session_id"]) == str(session_id)
        for a in st.session_state.attendance
    )


def get_session_attendance(session_id):
    """
    Return all student attendance records for a session.
    """

    return [
        a for a in st.session_state.attendance
        if (
            a["type"] == "Tutoring"
            and str(a["session_id"]) == str(session_id)
        )
    ]


def tutoring_hours_earned(session):
    """
    A tutoring session only counts toward tutor hours
    if at least one student scanned the QR code.

    The duration is actual_end - actual_start.
    """

    if not session_has_attendance(session["id"]):
        return 0

    return calculate_hours(
            session.get("actual_start"),
            session.get("actual_end")
        )


def get_tutor_commitments(tutor_id):
    """
    Return both classroom commitments and tutoring
    session commitments for a tutor.
    """

    commitments = []

    # Classroom commitments
    for signup in st.session_state.class_signups:

        if signup["tutor_id"] != tutor_id:
            continue

        c = get_class(signup["class_id"])

        if c:
            commitments.append({
                "type": "Class Support",
                "title": f"{c['course']} — {c['title']}",
                "date": c["date"],
                "start": c["start"],
                "end": c["end"],
                "location": c["room"],
                "status": c.get("status", "Open")
            })

    # Tutoring session commitments
    for session in st.session_state.sessions:

        if session["tutor_id"] != tutor_id:
            continue

        commitments.append({
            "type": "Tutoring",
            "title": session["title"],
            "date": session["date"],
            "start": session["scheduled_start"],
            "end": session["scheduled_end"],
            "location": "",
            "status": session["status"]
        })

    commitments.sort(
        key=lambda x: x["start"]
    )

    return commitments



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