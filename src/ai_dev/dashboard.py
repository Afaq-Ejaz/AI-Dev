"""
Phase 5 — TicketWise Verification Interface & Stress Testing

Streamlit dashboard that:
  1. Submits customer tickets to the FastAPI triage API
  2. Visualizes classification results, similarity scores, and routing
  3. Runs built-in stress tests (vague, aggressive, mixed-issue tickets)
  4. Tracks session history for comparison
"""

import streamlit as st
import requests
import plotly.graph_objects as go
import time
from datetime import datetime


# ── Configuration ────────────────────────────────────────────────────
API_BASE_URL = "http://127.0.0.1:8000"
DETAIL_ENDPOINT = f"{API_BASE_URL}/triage/detail"

# ── Color Palettes ───────────────────────────────────────────────────
CATEGORY_COLORS = {
    "bug": "#EF4444",
    "billing": "#F59E0B",
    "faq": "#3B82F6",
    "account": "#8B5CF6",
    "escalation": "#EC4899",
}

PRIORITY_COLORS = {
    "urgent": "#DC2626",
    "high": "#F97316",
    "medium": "#EAB308",
    "low": "#22C55E",
}

PRIORITY_ICONS = {
    "urgent": "🔴",
    "high": "🟠",
    "medium": "🟡",
    "low": "🟢",
}


# ── Stress Test Suites ──────────────────────────────────────────────
STRESS_TESTS = {
    "🌫️ Vague Queries": {
        "description": "Tickets with insufficient or ambiguous information — tests whether the system handles uncertainty gracefully.",
        "tickets": [
            {
                "label": "Minimal info",
                "customer_email": "vague1@test.com",
                "subject": "Help",
                "message": "Something is wrong.",
            },
            {
                "label": "Off-topic / unrelated",
                "customer_email": "vague2@test.com",
                "subject": "Question",
                "message": "What's the weather like today?",
            },
            {
                "label": "Ambiguous intent",
                "customer_email": "vague3@test.com",
                "subject": "Issue",
                "message": "It's not working and I need it fixed.",
            },
            {
                "label": "Single word",
                "customer_email": "vague4@test.com",
                "subject": "Problem",
                "message": "Broken.",
            },
        ],
    },
    "😡 Aggressive Messages": {
        "description": "Emotional or hostile tickets — tests whether tone/anger causes misclassification or priority inflation.",
        "tickets": [
            {
                "label": "Angry billing complaint",
                "customer_email": "angry1@test.com",
                "subject": "THIS IS ROBBERY!!!",
                "message": "You people STOLE my money! I was charged THREE TIMES and nobody is responding. I'm filing a complaint with the BBB and my lawyer!",
            },
            {
                "label": "Frustrated bug report",
                "customer_email": "angry2@test.com",
                "subject": "YOUR APP IS GARBAGE",
                "message": "This stupid app crashes EVERY SINGLE TIME I open it. I've reinstalled 5 times. Are your developers even real??",
            },
            {
                "label": "Threatening escalation",
                "customer_email": "angry3@test.com",
                "subject": "LAST WARNING",
                "message": "If I don't get a response in the next HOUR I'm going to the media. This is the WORST customer service I've ever experienced. GET ME A MANAGER NOW.",
            },
            {
                "label": "ALL CAPS rage",
                "customer_email": "angry4@test.com",
                "subject": "FIX THIS NOW OR ELSE",
                "message": "I CANNOT LOG IN. I HAVE BEEN LOCKED OUT FOR 3 DAYS. MY BUSINESS IS LOSING MONEY BECAUSE OF YOUR INCOMPETENT SYSTEM. DO SOMETHING!",
            },
        ],
    },
    "🔀 Mixed Issues": {
        "description": "Tickets combining multiple categories — tests whether the classifier picks the dominant issue correctly.",
        "tickets": [
            {
                "label": "Billing + Bug",
                "customer_email": "mixed1@test.com",
                "subject": "Charged twice AND app crashes",
                "message": "I was charged $29.99 twice this month. Also, your app keeps crashing on my iPhone whenever I try to view my billing history.",
            },
            {
                "label": "Account + Escalation",
                "customer_email": "mixed2@test.com",
                "subject": "Locked out — need a manager",
                "message": "My account is locked and the password reset isn't working. I've waited 48 hours with no response. I want to speak with a supervisor immediately.",
            },
            {
                "label": "FAQ + Billing",
                "customer_email": "mixed3@test.com",
                "subject": "How do I cancel and get a refund?",
                "message": "I want to cancel my subscription and get a refund for this month. Where do I find the cancellation option? I couldn't find it in settings.",
            },
            {
                "label": "Bug + Account + Billing",
                "customer_email": "mixed4@test.com",
                "subject": "Multiple problems",
                "message": "Three issues: 1) The app crashes when I open settings. 2) I can't change my email address. 3) I was charged for a premium plan I didn't sign up for.",
            },
        ],
    },
}


# ── Helper: Call the API ─────────────────────────────────────────────
def call_triage_api(email: str, subject: str, message: str) -> dict | None:
    """Submit a ticket to the FastAPI /triage/detail endpoint."""
    try:
        response = requests.post(
            DETAIL_ENDPOINT,
            json={
                "customer_email": email,
                "subject": subject,
                "message": message,
            },
            timeout=30,
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"**API Error {response.status_code}:** {response.json().get('detail', response.text)}")
            return None
    except requests.exceptions.ConnectionError:
        st.error(
            "**Cannot connect to the FastAPI server.** "
            "Make sure it's running with:\n\n"
            "```bash\nuv run ai-dev\n```"
        )
        return None
    except Exception as e:
        st.error(f"**Unexpected Error:** {e}")
        return None


# ── Helper: Render result card ───────────────────────────────────────
def render_result(result: dict, label: str = ""):
    """Display a single triage result with classification info and similarity chart."""

    classification = result["classification"]
    category = classification["category"]
    confidence = classification["confidence"]
    priority = classification["priority"]
    reasoning = classification["reasoning"]

    # ── Header with label ────────────────────────────────────────
    if label:
        st.markdown(f"##### 🏷️ {label}")

    # ── Classification Metrics ───────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        cat_color = CATEGORY_COLORS.get(category, "#6B7280")
        st.markdown(
            f'<div style="text-align:center; padding:12px; border-radius:12px; '
            f'background:linear-gradient(135deg, {cat_color}22, {cat_color}11); '
            f'border:1px solid {cat_color}44;">'
            f'<p style="margin:0; font-size:0.75em; opacity:0.7;">CATEGORY</p>'
            f'<p style="margin:0; font-size:1.3em; font-weight:700; color:{cat_color};">'
            f'{category.upper()}</p></div>',
            unsafe_allow_html=True,
        )
    with col2:
        pri_color = PRIORITY_COLORS.get(priority, "#6B7280")
        pri_icon = PRIORITY_ICONS.get(priority, "⚪")
        st.markdown(
            f'<div style="text-align:center; padding:12px; border-radius:12px; '
            f'background:linear-gradient(135deg, {pri_color}22, {pri_color}11); '
            f'border:1px solid {pri_color}44;">'
            f'<p style="margin:0; font-size:0.75em; opacity:0.7;">PRIORITY</p>'
            f'<p style="margin:0; font-size:1.3em; font-weight:700; color:{pri_color};">'
            f'{pri_icon} {priority.upper()}</p></div>',
            unsafe_allow_html=True,
        )
    with col3:
        conf_pct = confidence * 100
        conf_color = "#22C55E" if conf_pct >= 70 else "#EAB308" if conf_pct >= 50 else "#EF4444"
        st.markdown(
            f'<div style="text-align:center; padding:12px; border-radius:12px; '
            f'background:linear-gradient(135deg, {conf_color}22, {conf_color}11); '
            f'border:1px solid {conf_color}44;">'
            f'<p style="margin:0; font-size:0.75em; opacity:0.7;">CONFIDENCE</p>'
            f'<p style="margin:0; font-size:1.3em; font-weight:700; color:{conf_color};">'
            f'{conf_pct:.0f}%</p></div>',
            unsafe_allow_html=True,
        )
    with col4:
        sim_pct = result["similarity_score"] * 100
        sim_color = "#3B82F6" if sim_pct >= 70 else "#EAB308" if sim_pct >= 50 else "#EF4444"
        st.markdown(
            f'<div style="text-align:center; padding:12px; border-radius:12px; '
            f'background:linear-gradient(135deg, {sim_color}22, {sim_color}11); '
            f'border:1px solid {sim_color}44;">'
            f'<p style="margin:0; font-size:0.75em; opacity:0.7;">SIMILARITY</p>'
            f'<p style="margin:0; font-size:1.3em; font-weight:700; color:{sim_color};">'
            f'{sim_pct:.1f}%</p></div>',
            unsafe_allow_html=True,
        )

    st.markdown("")  # spacer

    # ── Details columns ──────────────────────────────────────────
    left, right = st.columns([1, 1])

    with left:
        st.markdown("**🧠 AI Reasoning:**")
        st.info(reasoning)
        st.markdown(f"**📋 Matched Policy:** `{result['matched_policy']}`")
        st.markdown(f"**🎫 Ticket ID:** `{result['ticket_id']}`")

    with right:
        st.markdown("**💬 Response Message:**")
        st.success(result["response_message"])

    # ── Similarity Scores Chart ──────────────────────────────────
    if "all_similarity_scores" in result:
        scores = result["all_similarity_scores"]
        titles = [s["policy_title"] for s in scores]
        values = [s["similarity_score"] for s in scores]
        categories = [s["category"] for s in scores]
        colors = [CATEGORY_COLORS.get(c, "#6B7280") for c in categories]

        # Highlight the matched policy
        bar_colors = []
        for i, title in enumerate(titles):
            if title == result["matched_policy"]:
                bar_colors.append(colors[i])
            else:
                bar_colors.append(colors[i] + "66")  # semi-transparent

        fig = go.Figure(
            data=[
                go.Bar(
                    x=values,
                    y=titles,
                    orientation="h",
                    marker_color=bar_colors,
                    text=[f"{v:.4f}" for v in values],
                    textposition="auto",
                    textfont=dict(size=11, color="white"),
                )
            ]
        )
        fig.update_layout(
            title=dict(
                text="Similarity Scores — All KB Policies",
                font=dict(size=14),
            ),
            xaxis=dict(
                title="Cosine Similarity",
                range=[0, 1],
                gridcolor="rgba(128,128,128,0.15)",
            ),
            yaxis=dict(autorange="reversed"),
            height=max(280, len(titles) * 40),
            margin=dict(l=10, r=10, t=40, b=30),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(size=12),
        )
        st.plotly_chart(fig, use_container_width=True)


# ── Page Config ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="TicketWise — Verification Dashboard",
    page_icon="🎫",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ── Custom CSS ───────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Subtle background gradient */
    .stApp {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
    }

    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e293b, #0f172a);
    }

    /* Make metric cards pop */
    div[data-testid="stMetric"] {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px;
        padding: 12px;
    }

    /* Form submit button styling */
    .stButton > button {
        background: linear-gradient(135deg, #3B82F6, #8B5CF6);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4);
    }

    /* Expander headers */
    .streamlit-expanderHeader {
        font-weight: 600;
        font-size: 1.05em;
    }

    /* Divider styling */
    hr {
        border-color: rgba(255,255,255,0.08);
    }
</style>
""", unsafe_allow_html=True)


# ── Session State ────────────────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []


# ── Sidebar ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎫 TicketWise")
    st.markdown("**Phase 5** — Verification & Stress Testing")
    st.divider()

    # API Health Check
    st.markdown("### 🔌 API Status")
    try:
        health = requests.get(f"{API_BASE_URL}/health", timeout=3)
        if health.status_code == 200:
            st.success("✅ API Online")
        else:
            st.warning(f"⚠️ API returned {health.status_code}")
    except Exception:
        st.error("❌ API Offline — start the server first")

    st.divider()

    # Session History
    st.markdown("### 📊 Session History")
    if st.session_state.history:
        st.markdown(f"**{len(st.session_state.history)}** tickets triaged")

        # Category breakdown
        cats = {}
        for h in st.session_state.history:
            cat = h["classification"]["category"]
            cats[cat] = cats.get(cat, 0) + 1

        for cat, count in sorted(cats.items(), key=lambda x: -x[1]):
            color = CATEGORY_COLORS.get(cat, "#6B7280")
            st.markdown(
                f'<span style="color:{color}; font-weight:600;">● {cat.upper()}</span>: {count}',
                unsafe_allow_html=True,
            )

        # Priority breakdown
        st.markdown("")
        pris = {}
        for h in st.session_state.history:
            pri = h["classification"]["priority"]
            pris[pri] = pris.get(pri, 0) + 1
        for pri, count in sorted(pris.items()):
            icon = PRIORITY_ICONS.get(pri, "⚪")
            st.markdown(f"{icon} **{pri}**: {count}")

        st.markdown("")
        if st.button("🗑️ Clear History", use_container_width=True):
            st.session_state.history = []
            st.rerun()
    else:
        st.caption("No tickets triaged yet.")

    st.divider()
    st.caption("Built with FastAPI + Gemini + Streamlit")


# ── Main Content ─────────────────────────────────────────────────────
st.markdown(
    '<h1 style="text-align:center; background: linear-gradient(135deg, #3B82F6, #8B5CF6, #EC4899); '
    '-webkit-background-clip:text; -webkit-text-fill-color:transparent; '
    'font-size:2.5em; margin-bottom:0;">🎫 TicketWise Dashboard</h1>',
    unsafe_allow_html=True,
)
st.markdown(
    '<p style="text-align:center; opacity:0.6; margin-top:0;">Verification Interface & Stress Testing</p>',
    unsafe_allow_html=True,
)

st.markdown("")

# ── Tab Layout ───────────────────────────────────────────────────────
tab_submit, tab_stress, tab_history = st.tabs([
    "📝 Submit Ticket",
    "🧪 Stress Tests",
    "📜 History",
])


# ── Tab 1: Submit Ticket ─────────────────────────────────────────────
with tab_submit:
    st.markdown("### Submit a Test Ticket")
    st.markdown("Enter ticket details below and the system will classify, retrieve, and route it in real-time.")
    st.markdown("")

    with st.form("ticket_form", clear_on_submit=False):
        col_email, col_subject = st.columns([1, 1])
        with col_email:
            email = st.text_input(
                "Customer Email",
                value="test@example.com",
                placeholder="user@example.com",
            )
        with col_subject:
            subject = st.text_input(
                "Subject",
                placeholder="Brief summary of the issue...",
            )

        message = st.text_area(
            "Message",
            height=120,
            placeholder="Describe the issue in detail...",
        )

        submitted = st.form_submit_button("🚀 Triage Ticket", use_container_width=True)

    if submitted:
        if not subject or not message:
            st.warning("Please fill in both the **subject** and **message** fields.")
        else:
            with st.spinner("🔄 Running triage pipeline..."):
                start_time = time.time()
                result = call_triage_api(email, subject, message)
                elapsed = time.time() - start_time

            if result:
                st.session_state.history.append(result)
                st.markdown("")
                st.markdown(f"---")
                st.markdown(f"### ✅ Triage Complete — `{elapsed:.2f}s`")
                render_result(result)


# ── Tab 2: Stress Tests ─────────────────────────────────────────────
with tab_stress:
    st.markdown("### 🧪 Stress Test Suite")
    st.markdown(
        "These pre-built test suites verify the system handles edge cases: "
        "**vague queries**, **aggressive messages**, and **mixed-issue tickets**."
    )
    st.markdown("")

    for suite_name, suite_data in STRESS_TESTS.items():
        with st.expander(f"**{suite_name}**", expanded=False):
            st.caption(suite_data["description"])
            st.markdown("")

            # Run all button
            if st.button(f"▶️ Run All {suite_name}", key=f"run_{suite_name}", use_container_width=True):
                progress_bar = st.progress(0)
                total = len(suite_data["tickets"])

                for idx, ticket in enumerate(suite_data["tickets"]):
                    progress_bar.progress((idx + 1) / total, text=f"Testing: {ticket['label']}...")

                    with st.spinner(f"Triaging: {ticket['label']}..."):
                        result = call_triage_api(
                            ticket["customer_email"],
                            ticket["subject"],
                            ticket["message"],
                        )

                    if result:
                        st.session_state.history.append(result)
                        st.markdown(f"---")
                        render_result(result, label=ticket["label"])
                    else:
                        st.error(f"❌ Failed: {ticket['label']}")

                progress_bar.empty()
                st.success(f"✅ Completed {total} stress tests!")

            # Individual ticket buttons
            st.markdown("**Or run individually:**")
            for ticket in suite_data["tickets"]:
                with st.container():
                    tcol1, tcol2 = st.columns([3, 1])
                    with tcol1:
                        st.markdown(
                            f"**{ticket['label']}** — _{ticket['subject']}_\n\n"
                            f"> {ticket['message'][:100]}{'...' if len(ticket['message']) > 100 else ''}"
                        )
                    with tcol2:
                        if st.button(
                            "▶️ Run",
                            key=f"single_{ticket['customer_email']}_{ticket['subject']}",
                            use_container_width=True,
                        ):
                            with st.spinner("Triaging..."):
                                result = call_triage_api(
                                    ticket["customer_email"],
                                    ticket["subject"],
                                    ticket["message"],
                                )
                            if result:
                                st.session_state.history.append(result)
                                st.markdown("---")
                                render_result(result, label=ticket["label"])


# ── Tab 3: History ───────────────────────────────────────────────────
with tab_history:
    st.markdown("### 📜 Triage History")

    if not st.session_state.history:
        st.info("No tickets triaged yet. Submit a ticket or run stress tests to see results here.")
    else:
        st.markdown(f"**{len(st.session_state.history)}** tickets in this session.")
        st.markdown("")

        # Summary table
        table_data = []
        for i, h in enumerate(reversed(st.session_state.history), 1):
            cat = h["classification"]["category"]
            pri = h["classification"]["priority"]
            conf = h["classification"]["confidence"]
            sim = h["similarity_score"]
            table_data.append({
                "#": i,
                "Ticket ID": h["ticket_id"],
                "Category": cat.upper(),
                "Priority": f"{PRIORITY_ICONS.get(pri, '')} {pri}",
                "Confidence": f"{conf*100:.0f}%",
                "Similarity": f"{sim*100:.1f}%",
                "Matched Policy": h["matched_policy"],
            })

        st.dataframe(
            table_data,
            use_container_width=True,
            hide_index=True,
        )

        # Expandable detail for each
        st.markdown("---")
        st.markdown("#### Detailed Results")
        for i, h in enumerate(reversed(st.session_state.history)):
            with st.expander(f"#{i+1} — {h['ticket_id']} ({h['classification']['category'].upper()})"):
                render_result(h)
