import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google import genai
from prompts import SYSTEM_PROMPT


# -----------------------------
# PAGE CONFIG
# -----------------------------

st.set_page_config(
    page_title="snappicstudy-ai",
    page_icon="📚",
    layout="wide"
)


# -----------------------------
# GEMINI CLIENT
# -----------------------------

client = genai.Client(
    api_key=st.secrets["GEMINI_API_KEY"]
)
def send_email(receiver_email, subject, body):

    sender_email = st.secrets["EMAIL_ADDRESS"]
    app_password = st.secrets["EMAIL_APP_PASSWORD"]

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject

    message.attach(
        MIMEText(body, "plain", "utf-8")
    )

    with smtplib.SMTP("smtp.gmail.com", 587) as server:

        server.starttls()

        server.login(
            sender_email,
            app_password
        )

        server.sendmail(
            sender_email,
            receiver_email,
            message.as_string()
        )


# -----------------------------
# SESSION STATE
# -----------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "image_data" not in st.session_state:
    st.session_state.image_data = None

if "image_type" not in st.session_state:
    st.session_state.image_type = None


# -----------------------------
# TITLE
# -----------------------------

st.title("📚 snappicstudy-ai")
st.caption(
    "Upload a question, diagram, or notes and learn step by step."
)


# -----------------------------
# SIDEBAR
# -----------------------------

with st.sidebar:

    st.header("⚙️ Study Mode")

    mode = st.selectbox(
        "Choose explanation style",
        [
            "Simple Explanation",
            "Detailed Explanation",
            "Exam Answer",
            "Numerical Problem"
        ]
    )

    st.divider()

    if st.button("🗑️ Clear Chat"):

        st.session_state.messages = []
        st.session_state.image_data = None
        st.session_state.image_type = None

        st.rerun()


# -----------------------------
# IMAGE UPLOAD
# -----------------------------

uploaded_file = st.file_uploader(
    "📷 Upload a question, diagram, or notes",
    type=["jpg", "jpeg", "png", "webp"]
)


# Store uploaded image
if uploaded_file is not None:

    st.session_state.image_data = uploaded_file.getvalue()
    st.session_state.image_type = uploaded_file.type

    st.image(
        uploaded_file,
        caption="Uploaded Study Material",
        width=500
    )


# -----------------------------
# INITIAL QUESTION
# -----------------------------

question = st.text_area(
    "✍️ Ask your question",
    placeholder="Example: Explain this circuit step by step."
)


# -----------------------------
# ANALYZE BUTTON
# -----------------------------

if st.button("🚀 Analyze", type="primary"):

    if uploaded_file is None and not question.strip():

        st.warning(
            "Please upload an image or enter a question."
        )

    else:

        with st.spinner("🔍 snappicstudy-ai is analyzing..."):

            try:

                contents = [
                    SYSTEM_PROMPT,
                    f"""
Explanation mode:
{mode}

Student question:
{question}
"""
                ]

                if st.session_state.image_data is not None:

                    contents.append(
                        {
                            "inline_data": {
                                "mime_type":
                                    st.session_state.image_type,
                                "data":
                                    st.session_state.image_data
                            }
                        }
                    )

                response = client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents=contents
                )

                answer = response.text

                # Save conversation
                st.session_state.messages.append(
                    {
                        "role": "user",
                        "content": question
                    }
                )

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer
                    }
                )

                st.success("✅ Analysis complete")

                st.divider()

                st.subheader("📧 Send Explanation by Email")

                receiver_email = st.text_input(
                    "Enter your email address",
                    placeholder="student@example.com"
                )

                if st.button("📨 Send Explanation"):

                    if not receiver_email.strip():

                        st.warning(
                            "Please enter an email address."
                        )

                    else:

                        try:

                            send_email(
                                receiver_email,
                                "StudySnap AI - Your Study Explanation",
                                answer
                            )

                            st.success(
                                "📨 Explanation sent successfully!"
                            )

                        except Exception as e:

                            st.error(
                                f"Email sending failed: {e}"
                            )


            except Exception as e:

                st.error(
                    f"Something went wrong: {e}"
                )


# -----------------------------
# DISPLAY CHAT HISTORY
# -----------------------------

if st.session_state.messages:

    st.divider()

    st.subheader("💬 Study Conversation")

    for message in st.session_state.messages:

        if message["role"] == "user":

            with st.chat_message("user"):
                st.markdown(message["content"])

        else:

            with st.chat_message("assistant"):
                st.markdown(message["content"])


# -----------------------------
# FOLLOW-UP CHAT
# -----------------------------

if st.session_state.messages:

    follow_up = st.chat_input(
        "Ask a follow-up question..."
    )

    if follow_up:

        with st.chat_message("user"):
            st.markdown(follow_up)

        with st.spinner("🤖 snappicstudy-ai is thinking..."):

            try:

                conversation = [
                    SYSTEM_PROMPT,
                    f"""
The student's selected study mode is:

{mode}

Previous conversation:
"""
                ]

                for message in st.session_state.messages:

                    conversation.append(
                        f"""
{message["role"].upper()}:
{message["content"]}
"""
                    )

                conversation.append(
                    f"""
USER:
{follow_up}
"""
                )

                response = client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents=conversation
                )

                answer = response.text

                st.session_state.messages.append(
                    {
                        "role": "user",
                        "content": follow_up
                    }
                )

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer
                    }
                )

                with st.chat_message("assistant"):
                    st.markdown(answer)

            except Exception as e:

                st.error(
                    f"Something went wrong: {e}"
                )