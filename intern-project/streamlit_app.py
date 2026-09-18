import requests
import streamlit as st

API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="AI Support Decision Assistant",
    page_icon="🤖",
    layout="centered",
)


# ============================================================
# API FUNCTIONS
# ============================================================

def register_user(email: str, password: str):
    try:
        return requests.post(
            f"{API_URL}/register",
            json={
                "email": email,
                "password": password,
            },
            timeout=10,
        )
    except requests.RequestException as exc:
        st.error(f"Could not connect to backend: {exc}")
        return None


def login_user(email: str, password: str):
    try:
        return requests.post(
            f"{API_URL}/login",
            json={
                "email": email,
                "password": password,
            },
            timeout=10,
        )
    except requests.RequestException as exc:
        st.error(f"Could not connect to backend: {exc}")
        return None


def get_current_user(token: str):
    try:
        return requests.get(
            f"{API_URL}/me",
            headers={
                "Authorization": f"Bearer {token}"
            },
            timeout=10,
        )
    except requests.RequestException as exc:
        st.error(f"Could not connect to backend: {exc}")
        return None


def create_ticket(token: str, message: str):
    try:
        return requests.post(
            f"{API_URL}/tickets",
            json={
                "message": message
            },
            headers={
                "Authorization": f"Bearer {token}"
            },
            timeout=60,
        )
    except requests.RequestException as exc:
        st.error(f"Could not connect to backend: {exc}")
        return None


# ============================================================
# SESSION STATE
# ============================================================

if "access_token" not in st.session_state:
    st.session_state.access_token = None

if "user" not in st.session_state:
    st.session_state.user = None


# ============================================================
# HEADER
# ============================================================

st.title("🤖 AI Support Decision Assistant")
st.caption("AI-powered support-ticket decision system")


# ============================================================
# LOGGED-IN USER
# ============================================================

if st.session_state.access_token:

    # --------------------------------------------------------
    # Sidebar
    # --------------------------------------------------------

    with st.sidebar:
        st.subheader("Account")

        if st.session_state.user:
            st.write(
                f"**{st.session_state.user['email']}**"
            )

        if st.button("Logout"):
            st.session_state.access_token = None
            st.session_state.user = None
            st.rerun()

    # --------------------------------------------------------
    # Main application
    # --------------------------------------------------------

    new_decision_tab, history_tab = st.tabs(
        ["📝 New Decision", "📚 History"]
    )

    # ========================================================
    # NEW DECISION
    # ========================================================

    with new_decision_tab:

        st.header("New Support Decision")

        st.write(
            "Enter a customer support ticket and the AI will "
            "recommend the appropriate action using the policy "
            "knowledge base."
        )

        ticket_message = st.text_area(
            "Support Ticket",
            placeholder=(
                "Example: My ₹3,500 order arrived damaged yesterday."
            ),
            height=150,
        )

        if st.button(
            "Analyze Ticket",
            type="primary",
            use_container_width=True,
        ):

            if not ticket_message.strip():
                st.warning("Please enter a support ticket.")

            else:
                with st.spinner(
                    "Analyzing ticket using AI and policy knowledge..."
                ):

                    response = create_ticket(
                        st.session_state.access_token,
                        ticket_message.strip(),
                    )

                if response is not None:

                    if response.status_code in (200, 201):

                        data = response.json()
                        decision = data.get("decision")

                        st.success("Decision generated successfully!")

                        if decision:

                            st.divider()

                            st.subheader("AI Recommendation")

                            # -------------------------------
                            # Action
                            # -------------------------------

                            st.markdown(
                                f"### `{decision['action']}`"
                            )

                            # -------------------------------
                            # Confidence
                            # -------------------------------

                            confidence = float(
                                decision["confidence"]
                            )

                            st.metric(
                                "Confidence",
                                f"{confidence:.0%}",
                            )

                            st.progress(confidence)

                            # -------------------------------
                            # Reason
                            # -------------------------------

                            st.subheader("Reasoning")

                            st.write(
                                decision["reason"]
                            )

                            # -------------------------------
                            # Sources
                            # -------------------------------

                            st.subheader("Policy Sources")

                            sources = decision.get(
                                "sources",
                                [],
                            )

                            if sources:
                                for source in sources:
                                    st.write(
                                        f"📄 {source}"
                                    )
                            else:
                                st.write(
                                    "No policy sources returned."
                                )

                        else:
                            st.warning(
                                "Ticket was created, but no decision "
                                "was returned."
                            )

                    else:

                        try:
                            detail = response.json().get(
                                "detail",
                                "AI decision failed.",
                            )
                        except ValueError:
                            detail = "AI decision failed."

                        st.error(
                            f"Backend error ({response.status_code}): "
                            f"{detail}"
                        )

    # ========================================================
    # HISTORY
    # ========================================================

    with history_tab:

        st.header("Decision History")

        try:
            response = requests.get(
                f"{API_URL}/tickets",
                headers={
                    "Authorization": (
                        f"Bearer "
                        f"{st.session_state.access_token}"
                    )
                },
                timeout=10,
            )

            if response.status_code == 200:

                tickets = response.json()

                if not tickets:

                    st.info(
                        "You don't have any support tickets yet."
                    )

                else:

                    for ticket in tickets:

                        decision = ticket.get("decision")

                        with st.expander(
                            f"Ticket #{ticket['id']} — "
                            f"{ticket['message'][:60]}"
                        ):

                            st.write(
                                f"**Ticket:** "
                                f"{ticket['message']}"
                            )

                            st.write(
                                f"**Created:** "
                                f"{ticket['created_at']}"
                            )

                            if decision:

                                st.write(
                                    f"**Action:** "
                                    f"`{decision['action']}`"
                                )

                                st.write(
                                    f"**Confidence:** "
                                    f"{decision['confidence']:.0%}"
                                )

                                st.write(
                                    f"**Reason:** "
                                    f"{decision['reason']}"
                                )

                                sources = decision.get(
                                    "sources",
                                    [],
                                )

                                if sources:
                                    st.write(
                                        "**Sources:** "
                                        + ", ".join(sources)
                                    )

            else:
                st.error(
                    f"Could not load history "
                    f"({response.status_code})."
                )

        except requests.RequestException as exc:
            st.error(
                f"Could not connect to backend: {exc}"
            )


# ============================================================
# NOT LOGGED IN
# ============================================================

else:

    login_tab, register_tab = st.tabs(
        ["Login", "Register"]
    )

    # ========================================================
    # LOGIN
    # ========================================================

    with login_tab:

        st.subheader("Login")

        login_email = st.text_input(
            "Email",
            key="login_email",
        )

        login_password = st.text_input(
            "Password",
            type="password",
            key="login_password",
        )

        if st.button(
            "Login",
            type="primary",
            use_container_width=True,
        ):

            if not login_email or not login_password:

                st.warning(
                    "Please enter both email and password."
                )

            else:

                response = login_user(
                    login_email,
                    login_password,
                )

                if response is not None:

                    if response.status_code == 200:

                        data = response.json()

                        token = data["access_token"]

                        me_response = get_current_user(token)

                        if (
                            me_response is not None
                            and me_response.status_code == 200
                        ):

                            st.session_state.access_token = token
                            st.session_state.user = (
                                me_response.json()
                            )

                            st.success(
                                "Login successful!"
                            )

                            st.rerun()

                        else:

                            st.error(
                                "Login succeeded, but "
                                "/me failed."
                            )

                    else:

                        try:
                            detail = response.json().get(
                                "detail",
                                "Login failed.",
                            )
                        except ValueError:
                            detail = "Login failed."

                        st.error(detail)

    # ========================================================
    # REGISTER
    # ========================================================

    with register_tab:

        st.subheader("Create Account")

        register_email = st.text_input(
            "Email",
            key="register_email",
        )

        register_password = st.text_input(
            "Password",
            type="password",
            key="register_password",
        )

        register_confirm = st.text_input(
            "Confirm Password",
            type="password",
            key="register_confirm",
        )

        if st.button(
            "Register",
            use_container_width=True,
        ):

            if (
                not register_email
                or not register_password
            ):

                st.warning(
                    "Please fill in all required fields."
                )

            elif register_password != register_confirm:

                st.error(
                    "Passwords do not match."
                )

            else:

                response = register_user(
                    register_email,
                    register_password,
                )

                if response is not None:

                    if response.status_code == 201:

                        st.success(
                            "Account created successfully. "
                            "You can now log in."
                        )

                    else:

                        try:
                            detail = response.json().get(
                                "detail",
                                "Registration failed.",
                            )
                        except ValueError:
                            detail = "Registration failed."

                        st.error(detail)