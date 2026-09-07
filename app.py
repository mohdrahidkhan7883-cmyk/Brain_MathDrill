import streamlit as st
import random
import time
import os
import uuid
from datetime import datetime

import pandas as pd
import plotly.express as px


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Brain MathDrill",
    page_icon="🧠",
    layout="wide"
)


# =========================================================
# PATHS
# =========================================================

DATA_DIR = "data"
REPORT_DIR = os.path.join(DATA_DIR, "session_reports")

HISTORY_FILE = os.path.join(
    DATA_DIR,
    "practice_history.csv"
)

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)
def format_time(seconds):
    seconds = float(seconds)

    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    remaining_seconds = seconds % 60

    if hours > 0:
        if minutes > 0:
            return f"{hours} hr {minutes} min"
        return f"{hours} hr"

    elif minutes > 0:
        if remaining_seconds > 0:
            return f"{minutes} min {remaining_seconds:.0f} sec"
        return f"{minutes} min"

    else:
        return f"{remaining_seconds:.2f} sec"


# =========================================================
# CSS
# =========================================================

st.markdown("""
<style>

.main {
    padding-top: 1rem;
}

.hero {
    padding: 1.2rem 0 1rem 0;
}

.hero h1 {
    font-size: 2.8rem;
    margin-bottom: 0.2rem;
}

.hero p {
    color: #777;
    font-size: 1.05rem;
}

.question-box {
    padding: 35px;
    border-radius: 18px;
    text-align: center;
    border: 1px solid rgba(128,128,128,0.25);
    margin: 20px 0;
}

.question {
    font-size: 3rem;
    font-weight: 700;
}

.correct {
    padding: 15px;
    border-radius: 12px;
    background: rgba(0, 180, 100, 0.12);
    border: 1px solid rgba(0, 180, 100, 0.3);
}

.wrong {
    padding: 15px;
    border-radius: 12px;
    background: rgba(220, 50, 50, 0.12);
    border: 1px solid rgba(220, 50, 50, 0.3);
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# SESSION STATE
# =========================================================

defaults = {

    "game_started": False,
    "game_finished": False,

    "current_question": None,
    "correct_answer": None,

    "question_start": None,
    "practice_start": None,

    "question_number": 0,

    "score": 0,

    "results": [],

    "last_feedback": None,
    "last_answer": None,
    "last_correct_answer": None,
    "last_response_time": None,

    "session_no": None,

    "practice_saved": False,

    "operation": None,
    "difficulty": None,
    "total_questions": 10,

    "digits_a": 2,
    "digits_b": 2,

    "user_id": None

}


for key, value in defaults.items():

    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# PER-USER / PER-TAB IDENTITY
# =========================================================
# A fresh unique ID is generated the first time this browser
# tab/session touches the app. It stays the same for as long
# as the user keeps this tab open (across reruns), so all
# practice sessions done in one visit are grouped together.
# Reopening the app (new tab / new session) generates a brand
# new ID, so old history from other visits/users is not shown.

if st.session_state.user_id is None:

    st.session_state.user_id = str(uuid.uuid4())


# =========================================================
# SESSION NUMBER
# =========================================================

def get_next_session_number():

    if not os.path.exists(HISTORY_FILE):
        return 1

    try:

        df = pd.read_csv(HISTORY_FILE)

        if df.empty:
            return 1

        return int(df["Session No"].max()) + 1

    except Exception:

        return 1


# =========================================================
# NUMBER GENERATOR BASED ON DIGITS
# =========================================================

def generate_number(digits):

    if digits == 1:

        return random.randint(1, 9)

    minimum = 10 ** (digits - 1)
    maximum = (10 ** digits) - 1

    return random.randint(
        minimum,
        maximum
    )


# =========================================================
# QUESTION GENERATOR
# =========================================================

def generate_question(
    operation,
    difficulty,
    digits_a,
    digits_b
):

    # -----------------------------------------------------
    # Addition
    # -----------------------------------------------------

    if operation == "Addition (+)":

        a = generate_number(digits_a)
        b = generate_number(digits_b)

        question = f"{a} + {b}"
        answer = a + b


    # -----------------------------------------------------
    # Subtraction
    # -----------------------------------------------------

    elif operation == "Subtraction (-)":

        a = generate_number(digits_a)
        b = generate_number(digits_b)

        if b > a:

            a, b = b, a

        question = f"{a} - {b}"
        answer = a - b


    # -----------------------------------------------------
    # Multiplication
    # -----------------------------------------------------

    elif operation == "Multiplication (×)":

        a = generate_number(digits_a)
        b = generate_number(digits_b)

        question = f"{a} × {b}"
        answer = a * b


    # -----------------------------------------------------
    # Division
    # -----------------------------------------------------

    elif operation == "Division (÷)":

    # HARD MODE → Decimal answer (up to 3 decimal places)
       if difficulty == "Hard":

          dividend = generate_number(digits_a)
          divisor = generate_number(digits_b)

          question = f"{dividend} ÷ {divisor}"
          answer = round(dividend / divisor, 3)

    # EASY & MEDIUM → Exact Integer Division
       else:

          # Generate divisor
          divisor = generate_number(digits_b)

          # Maximum dividend according to selected digits
          max_dividend = (10 ** digits_a) - 1

          # Maximum possible quotient
          max_quotient = max_dividend // divisor

        # Ensure quotient is at least 1
          max_quotient = max(1, max_quotient)

          quotient = random.randint(1, max_quotient)

        # Exact division
          dividend = divisor * quotient

          question = f"{dividend} ÷ {divisor}"
          answer = quotient
    # -----------------------------------------------------
    # Percentage
    # -----------------------------------------------------

    elif operation == "Percentage (%)":

        percentage_options = [
            5,
            10,
            12.5,
            15,
            16.67,
            20,
            25,
            30,
            33.33,
            40,
            50,
            60,
            66.67,
            70,
            75,
            80,
            83.33,
            90,
            95,
            98
        ]

        percentage = random.choice(
            percentage_options
        )

        base = generate_number(
            max(1, digits_b)
        )

        # Make common percentages mentally easier

        if percentage == 5:

            base = base // 20 * 20

            if base == 0:
                base = 20

        elif percentage == 10:

            base = base // 10 * 10

            if base == 0:
                base = 10

        elif percentage == 20:

            base = base // 5 * 5

            if base == 0:
                base = 5

        elif percentage == 25:

            base = base // 4 * 4

            if base == 0:
                base = 4

        elif percentage == 50:

            base = base // 2 * 2

            if base == 0:
                base = 2

        question = f"{percentage}% of {base}"

        answer = (percentage / 100) * base


    # -----------------------------------------------------
    # Square
    # -----------------------------------------------------

    elif operation == "Square (x²)":

        a = generate_number(
            digits_a
        )

        question = f"{a}²"

        answer = a ** 2


    # -----------------------------------------------------
    # Cube
    # -----------------------------------------------------

    elif operation == "Cube (x³)":

        a = generate_number(
            digits_a
        )

        question = f"{a}³"

        answer = a ** 3


    return question, answer


# =========================================================
# CREATE QUESTION
# =========================================================

def create_next_question():

    question, answer = generate_question(

        st.session_state.operation,

        st.session_state.difficulty,

        st.session_state.digits_a,

        st.session_state.digits_b

    )

    st.session_state.current_question = question

    st.session_state.correct_answer = answer

    # VERY IMPORTANT:
    # Timer starts exactly when question appears

    st.session_state.question_start = time.time()


# =========================================================
# SAVE COMPLETED SESSION
# =========================================================

def save_session():

    if st.session_state.practice_saved:
        return

    results = st.session_state.results

    if not results:
        return

    session_no = st.session_state.session_no

    session_date = datetime.now().strftime(
        "%Y-%m-%d"
    )

    session_datetime = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    df = pd.DataFrame(results)

    total_questions = len(df)

    correct = (
        df["Result"] == "Correct"
    ).sum()

    wrong = total_questions - correct

    accuracy = (
        correct / total_questions
    ) * 100

    total_time = df["Response Time"].sum()

    average_time = df["Response Time"].mean()

    fastest_time = df["Response Time"].min()

    slowest_time = df["Response Time"].max()


    # -----------------------------------------------------
    # Add session information
    # -----------------------------------------------------

    df["Session No"] = session_no

    df["User ID"] = st.session_state.user_id

    df["Date"] = session_date

    df["Session DateTime"] = session_datetime


    # -----------------------------------------------------
    # Save detailed session report
    # -----------------------------------------------------

    report_file = os.path.join(

        REPORT_DIR,

        f"session_{session_no}_{session_date}.csv"

    )

    df.to_csv(
        report_file,
        index=False
    )


    # -----------------------------------------------------
    # All practice history summary
    # -----------------------------------------------------

    summary = pd.DataFrame([{

        "Session No": session_no,

        "User ID": st.session_state.user_id,

        "Date": session_date,

        "Date & Time": session_datetime,

        "Operation": st.session_state.operation,

        "Difficulty": st.session_state.difficulty,

        "Questions": total_questions,

        "Correct": correct,

        "Wrong": wrong,

        "Accuracy": round(
            accuracy,
            2
        ),

        "Total Practice Time": round(
            total_time,
            2
        ),

        "Average Question Time": round(
            average_time,
            2
        ),

        "Fastest Question": round(
            fastest_time,
            2
        ),

        "Slowest Question": round(
            slowest_time,
            2
        ),

        "First Number Digits": st.session_state.digits_a,

        "Second Number Digits": st.session_state.digits_b

    }])


    # -----------------------------------------------------
    # Append to history
    # -----------------------------------------------------

    if os.path.exists(HISTORY_FILE):

        old_history = pd.read_csv(
            HISTORY_FILE
        )

        history = pd.concat(
            [
                old_history,
                summary
            ],
            ignore_index=True
        )

    else:

        history = summary


    history.to_csv(
        HISTORY_FILE,
        index=False
    )


    st.session_state.practice_saved = True


# =========================================================
# SUBMIT ANSWER
# =========================================================

def submit_answer(user_answer):

    # Time when user submits answer

    end_time = time.time()

    response_time = (
        end_time
        - st.session_state.question_start
    )

    correct_answer = (
        st.session_state.correct_answer
    )


    # -----------------------------------------------------
    # Convert answer
    # -----------------------------------------------------

    try:

        user_value = float(
            user_answer
        )

        is_correct = (
            abs(
                user_value
                - float(correct_answer)
            )
            < 0.001
        )

    except:

        is_correct = False


    # -----------------------------------------------------
    # Score
    # -----------------------------------------------------

    if is_correct:

        st.session_state.score += 1

        feedback = "correct"

    else:

        feedback = "wrong"


    # -----------------------------------------------------
    # Store result
    # -----------------------------------------------------

    st.session_state.results.append({

        "Question No": (
            st.session_state.question_number + 1
        ),

        "Operation": (
            st.session_state.operation
        ),

        "Question": (
            st.session_state.current_question
        ),

        "Your Answer": user_answer,

        "Correct Answer": correct_answer,

        "Result": (
            "Correct"
            if is_correct
            else "Wrong"
        ),

        "Response Time": round(
            response_time,
            2
        )

    })


    st.session_state.last_feedback = feedback

    st.session_state.last_answer = user_answer

    st.session_state.last_correct_answer = correct_answer

    st.session_state.last_response_time = response_time

    st.session_state.question_number += 1


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.header("⚙️ Practice Settings")


    # -----------------------------------------------------
    # Operation
    # -----------------------------------------------------

    operation = st.selectbox(

        "Operation",

        [
            "Addition (+)",
            "Subtraction (-)",
            "Multiplication (×)",
            "Division (÷)",
            "Percentage (%)",
            "Square (x²)",
            "Cube (x³)"
        ]

    )


    # -----------------------------------------------------
    # Difficulty
    # -----------------------------------------------------

    difficulty = st.select_slider(

        "Difficulty",

        options=[
            "Easy",
            "Medium",
            "Hard"
        ],

        value="Medium"

    )


    st.subheader("🔢 Number Digits")


    # -----------------------------------------------------
    # FIRST NUMBER DIGITS
    # -----------------------------------------------------

    digits_a = st.selectbox(

        "First Number",

        [1, 2, 3, 4, 5, 6, 7, 8,9],

        index=1,

        format_func=lambda x:
        f"{x} digit"
        if x == 1
        else f"{x} digits"

    )


    # -----------------------------------------------------
    # SECOND NUMBER DIGITS
    # -----------------------------------------------------

    digits_b = st.selectbox(

        "Second Number",

        [1, 2, 3, 4, 5, 6, 7, 8,9],

        index=1,

        format_func=lambda x:
        f"{x} digit"
        if x == 1
        else f"{x} digits"

    )


    # -----------------------------------------------------
    # Number of questions
    # -----------------------------------------------------

    total_questions = st.slider(

        "Number of Questions",

        min_value=5,

        max_value=100,

        value=10,

        step=5

    )


    st.divider()


    # -----------------------------------------------------
    # START
    # -----------------------------------------------------

    if st.button(

        "🚀 Start Practice",

        use_container_width=True

    ):

        st.session_state.game_started = True

        st.session_state.game_finished = False

        st.session_state.practice_saved = False

        st.session_state.question_number = 0

        st.session_state.score = 0

        st.session_state.results = []

        st.session_state.last_feedback = None

        st.session_state.last_answer = None

        st.session_state.last_correct_answer = None

        st.session_state.last_response_time = None


        st.session_state.operation = operation

        st.session_state.difficulty = difficulty

        st.session_state.total_questions = (
            total_questions
        )

        st.session_state.digits_a = digits_a

        st.session_state.digits_b = digits_b


        # New session number

        st.session_state.session_no = (
            get_next_session_number()
        )


        # Start overall practice timer

        st.session_state.practice_start = (
            time.time()
        )


        create_next_question()

        st.rerun()

    st.sidebar.markdown("---")
st.sidebar.caption("Developed by Mohd Rahid Khan")
# =========================================================
# HEADER
# =========================================================

st.markdown("""
<div class="hero">

<h1>🧠 Brain MathDrill</h1>

<p>
Train your mental calculation speed, accuracy and consistency.
</p>

</div>
""", unsafe_allow_html=True)


# =========================================================
# DASHBOARD SUMMARY
# =========================================================

if st.session_state.results:

    current_df = pd.DataFrame(
        st.session_state.results
    )

    current_correct = (
        current_df["Result"] == "Correct"
    ).sum()

    current_accuracy = (
        current_correct
        / len(current_df)
    ) * 100

    current_avg_time = (
        current_df["Response Time"].mean()
    )

    current_total_time = (
        current_df["Response Time"].sum()
    )

else:

    current_accuracy = 0

    current_avg_time = 0

    current_total_time = 0


c1, c2, c3, c4 = st.columns(4)


with c1:

    st.metric(
        "Questions",
        len(st.session_state.results)
    )


with c2:

    st.metric(
        "Avg Question Time",
       format_time(current_avg_time)
    )


with c3:

    st.metric(
        "Total Practice Time",
       format_time(current_total_time)
    )


with c4:

    st.metric(
        "Session",
        st.session_state.session_no
        if st.session_state.session_no
        else "-"
    )


st.divider()


# =========================================================
# ACTIVE PRACTICE
# =========================================================

if (

    st.session_state.game_started

    and not st.session_state.game_finished

):

    current_no = (
        st.session_state.question_number + 1
    )


    # -----------------------------------------------------
    # Complete practice
    # -----------------------------------------------------

    if current_no > st.session_state.total_questions:

        save_session()

        st.session_state.game_finished = True

        st.rerun()


    # -----------------------------------------------------
    # Progress
    # -----------------------------------------------------

    progress = (
        st.session_state.question_number
        / st.session_state.total_questions
    )

    st.progress(progress)


    st.caption(

        f"Session {st.session_state.session_no}  •  "
        f"Question {current_no} of "
        f"{st.session_state.total_questions}"

    )


    # -----------------------------------------------------
    # Question
    # -----------------------------------------------------

    st.markdown(

        f"""
        <div class="question-box">

        <div class="question">
        {st.session_state.current_question}
        </div>

        </div>
        """,

        unsafe_allow_html=True

    )


    # -----------------------------------------------------
    # Answer
    # -----------------------------------------------------

    with st.form(

        key=f"answer_{st.session_state.question_number}"

    ):

        user_answer = st.text_input(

            "Your Answer",

            placeholder="Type your answer..."

        )


        submitted = st.form_submit_button(

            "Submit Answer",

            use_container_width=True

        )


    # -----------------------------------------------------
    # Submit
    # -----------------------------------------------------

    if submitted:

        if not user_answer.strip():

            st.warning(
                "Please enter your answer."
            )

        else:

            submit_answer(
                user_answer
            )

            # ---------------------------------------------
            # Automatically move to the next question
            # (or finish the practice) right after the
            # answer is submitted — no extra click needed.
            # ---------------------------------------------

            if (
                st.session_state.question_number
                >= st.session_state.total_questions
            ):

                save_session()

                st.session_state.game_finished = True

            else:

                create_next_question()

            st.rerun()


    # -----------------------------------------------------
    # Feedback
    # -----------------------------------------------------

    if st.session_state.last_feedback:

        response_time = (
            st.session_state.last_response_time
        )


        if (
            st.session_state.last_feedback
            == "correct"
        ):

            st.markdown(

                f"""
                <div class="correct">

                <h3>✅ Correct!</h3>

                Your answer:
                <b>{st.session_state.last_answer}</b>

                <br>

                ⏱️ Time taken:
                <b>{response_time:.2f} seconds</b>

                </div>
                """,

                unsafe_allow_html=True

            )

        else:

            st.markdown(

                f"""
                <div class="wrong">

                <h3>❌ Incorrect</h3>

                Your answer:
                <b>{st.session_state.last_answer}</b>

                <br>

                Correct answer:
                <b>{st.session_state.last_correct_answer}</b>

                <br>

                ⏱️ Time taken:
                <b>{response_time:.2f} seconds</b>

                </div>
                """,

                unsafe_allow_html=True

            )


        st.caption(
            "☝️ Result of your previous answer — the next "
            "question has already started above."
        )


# =========================================================
# FINAL SESSION REPORT
# =========================================================

if st.session_state.game_finished:

    save_session()


    df = pd.DataFrame(
        st.session_state.results
    )


    total_questions = len(df)

    correct = (
        df["Result"] == "Correct"
    ).sum()

    wrong = (
        total_questions - correct
    )

    accuracy = (
        correct / total_questions
    ) * 100

    total_time = (
        df["Response Time"].sum()
    )

    average_time = (
        df["Response Time"].mean()
    )

    fastest_time = (
        df["Response Time"].min()
    )

    slowest_time = (
        df["Response Time"].max()
    )


    st.success(
        "🎉 Practice Session Completed!"
    )


    st.subheader(
        f"🏆 Session {st.session_state.session_no} Report"
    )


    # -----------------------------------------------------
    # Session metrics
    # -----------------------------------------------------

    c1, c2, c3, c4, c5 = st.columns(5)


    c1.metric(
        "Questions",
        total_questions
    )


    c2.metric(
        "Correct",
        correct
    )


    c3.metric(
        "Wrong",
        wrong
    )


    c4.metric(
        "Accuracy",
        f"{accuracy:.1f}%"
    )


    c5.metric(
        "Total Time",
        format_time(total_time)
    )


    st.info(

        f"""
        **Total Practice Time:** {total_time:.2f} seconds  
        **Average Question Time:** {average_time:.2f} seconds  
        **Fastest Question:** {fastest_time:.2f} seconds  
        **Slowest Question:** {slowest_time:.2f} seconds
        """

    )


    st.divider()


    # =====================================================
    # RESPONSE TIME CHART
    # =====================================================

    st.subheader(
        "⏱️ Response Time per Question"
    )


    # This is the MAIN performance chart.
    # Accuracy is NOT used here.

    time_chart = px.line(

        df,

        x="Question No",

        y="Response Time",

        markers=True,

        title="Time Taken for Each Question",

        labels={
            "Question No": "Question",
            "Response Time": "Time (seconds)"
        }

    )


    time_chart.update_layout(

        yaxis_title="Time (seconds)",

        xaxis_title="Question Number"

    )


    st.plotly_chart(

        time_chart,

        use_container_width=True

    )


    st.caption(

        "Lower response time means faster mental calculation."

    )


    # =====================================================
    # DONUT
    # =====================================================

    st.subheader(
        "📌 Result Distribution"
    )


    result_counts = (

        df["Result"]

        .value_counts()

        .reset_index()

    )


    result_counts.columns = [

        "Result",
        "Count"

    ]


    donut = px.pie(

        result_counts,

        names="Result",

        values="Count",

        hole=0.55,

        title="Questions Completed"

    )


    # IMPORTANT:
    # Show numbers, NOT percentages

    donut.update_traces(

        textinfo="value",

        hovertemplate=(
            "<b>%{label}</b><br>"
            "Questions: %{value}"
            "<extra></extra>"
        )

    )


    st.plotly_chart(

        donut,

        use_container_width=True

    )


    # =====================================================
    # QUESTION HISTORY
    # =====================================================

    st.subheader(
        "📋 Question-by-Question Report"
    )


    st.dataframe(

        df,

        use_container_width=True,

        hide_index=True

    )


    # =====================================================
    # DOWNLOAD CURRENT SESSION
    # =====================================================

    session_csv = df.to_csv(
        index=False
    ).encode("utf-8")


    st.download_button(

        "⬇️ Download This Session Report",

        data=session_csv,

        file_name=(
            f"session_"
            f"{st.session_state.session_no}"
            f"_report.csv"
        ),

        mime="text/csv",

        use_container_width=True

    )


# =========================================================
# MY PRACTICE HISTORY (THIS VISIT / THIS BROWSER TAB ONLY)
# =========================================================
# Every user gets their own history, scoped to how long they
# keep this tab open. As soon as a session finishes, it is
# added to this list. Reopening the app later starts fresh —
# older sessions (yours or anyone else's) are not shown here.

st.divider()

st.subheader(
    "📚 My Practice History (This Visit)"
)


all_history_df = None

if os.path.exists(HISTORY_FILE):

    all_history_df = pd.read_csv(
        HISTORY_FILE
    )

    # Backward compatibility for history files saved
    # before per-user tracking was added.
    if "User ID" not in all_history_df.columns:
        all_history_df["User ID"] = "unknown"


if all_history_df is not None and not all_history_df.empty:

    my_history_df = all_history_df[
        all_history_df["User ID"]
        == st.session_state.user_id
    ].reset_index(drop=True)

else:

    my_history_df = pd.DataFrame()


if not my_history_df.empty:

    # ---------------------------------------------
    # Overall stats (this user, this visit)
    # ---------------------------------------------

    total_sessions = len(
        my_history_df
    )

    total_questions_all = (
        my_history_df["Questions"].sum()
    )

    total_time_all = (
        my_history_df["Total Practice Time"].sum()
    )


    c1, c2, c3 = st.columns(3)


    c1.metric(
        "Sessions This Visit",
        total_sessions
    )


    c2.metric(
        "Total Questions",
        total_questions_all
    )


    c3.metric(
        "Total Practice Time",
        f"{total_time_all:.2f}s"
    )


    st.dataframe(

        my_history_df.drop(
            columns=["User ID"]
        ),

        use_container_width=True,

        hide_index=True

    )


    # ---------------------------------------------
    # Session-wise total time
    # ---------------------------------------------

    st.subheader(
        "⏱️ Practice Time by Session"
    )


    session_time_chart = px.bar(

        my_history_df,

        x="Session No",

        y="Total Practice Time",

        text="Total Practice Time",

        title="Total Time Spent in Each Session",

        labels={
            "Session No": "Session",
            "Total Practice Time":
                "Time (seconds)"
        }

    )


    session_time_chart.update_traces(

        texttemplate="%{text:.2f}s"

    )
    session_time_chart.update_xaxes(
        tickmode="linear",
        dtick=1
    )


    st.plotly_chart(

        session_time_chart,

        use_container_width=True

    )


    # ---------------------------------------------
    # Download my history
    # ---------------------------------------------

    history_csv = my_history_df.to_csv(
        index=False
    ).encode("utf-8")


    st.download_button(

        "⬇️ Download My Practice History",

        data=history_csv,

        file_name="brain_mathdrill_my_history.csv",

        mime="text/csv",

        use_container_width=True

    )


else:

    st.info(
        "No practice sessions yet in this visit. "
        "Finish a practice session and it will show up here "
        "right away."
    )


# =========================================================
# USAGE TRACKER (ACROSS ALL USERS)
# =========================================================

st.divider()

st.subheader(
    "📊 Usage Tracker"
)

st.caption(
    "Overall usage across every user of this app."
)


if all_history_df is not None and not all_history_df.empty:

    sessions_per_user = (
        all_history_df
        .groupby("User ID")
        .size()
    )

    total_users = sessions_per_user.shape[0]

    avg_sessions_per_user = (
        sessions_per_user.mean()
    )

    max_sessions_by_a_user = (
        sessions_per_user.max()
    )


    t1, t2, t3 = st.columns(3)


    t1.metric(
        "👥 Total Users",
        total_users
    )


    t2.metric(
        "📈 Avg. Sessions / User",
        f"{avg_sessions_per_user:.2f}"
    )


    t3.metric(
        "🏅 Max Sessions (Single User)",
        int(max_sessions_by_a_user)
    )


else:

    st.info(
        "No usage data yet — stats will appear once "
        "practice sessions have been completed."
    )


# =========================================================
# DEFAULT SCREEN
# =========================================================

if not st.session_state.game_started:

    st.info(

        "👈 Select your operation, difficulty, "
        "number of digits and number of questions "
        "from the sidebar, then start your practice."

    )


    st.markdown(
        "### 🎯 Available Operations"
    )


    c1, c2, c3, c4 = st.columns(4)


    c1.info("➕ **Addition**")

    c2.info("➖ **Subtraction**")

    c3.info("✖️ **Multiplication**")

    c4.info("➗ **Division**")


    c1, c2, c3 = st.columns(3)


    c1.info("％ **Percentage**")

    c2.info("² **Square**")

    c3.info("³ **Cube**")


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.markdown(
    """
    <div style="text-align:center; color:#888; padding: 10px 0;">
    🧠 Brain MathDrill &nbsp;•&nbsp; Developed by
    <b>Mohd Rahid Khan</b>
    </div>
    """,
    unsafe_allow_html=True
)