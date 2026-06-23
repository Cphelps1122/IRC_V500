import streamlit as st

DARK = {
    "name": "dark",
    "bg": "#07111F",
    "panel": "#0F1F35",
    "panel2": "#122945",
    "text": "#EAF2FF",
    "muted": "#9FB4CF",
    "border": "rgba(148, 163, 184, 0.22)",
    "accent": "#38BDF8",
    "accent2": "#22C55E",
    "warning": "#F59E0B",
    "danger": "#EF4444",
    "info": "#60A5FA",
    "card_shadow": "0 14px 36px rgba(0,0,0,0.22)",
    "plotly_template": "plotly_dark",
}

LIGHT = {
    "name": "light",
    "bg": "#F5F7FB",
    "panel": "#FFFFFF",
    "panel2": "#F8FAFC",
    "text": "#0F172A",
    "muted": "#64748B",
    "border": "rgba(15, 23, 42, 0.12)",
    "accent": "#0284C7",
    "accent2": "#16A34A",
    "warning": "#D97706",
    "danger": "#DC2626",
    "info": "#2563EB",
    "card_shadow": "0 12px 30px rgba(15,23,42,0.08)",
    "plotly_template": "plotly_white",
}


def init_theme():
    if "theme_mode" not in st.session_state:
        st.session_state.theme_mode = "dark"


def current_theme():
    init_theme()
    return DARK if st.session_state.theme_mode == "dark" else LIGHT


def theme_toggle():
    init_theme()
    selected = st.sidebar.toggle(
        "Light mode",
        value=(st.session_state.theme_mode == "light"),
        help="Switch the dashboard from dark mode to light mode.",
    )
    st.session_state.theme_mode = "light" if selected else "dark"


def apply_theme():
    t = current_theme()
    st.markdown(
        f"""
        <style>
        :root {{
            --app-bg: {t['bg']};
            --panel-bg: {t['panel']};
            --panel-bg-2: {t['panel2']};
            --text-main: {t['text']};
            --text-muted: {t['muted']};
            --border: {t['border']};
            --accent: {t['accent']};
            --accent-2: {t['accent2']};
            --warning: {t['warning']};
            --danger: {t['danger']};
        }}
        .stApp {{
            background: radial-gradient(circle at top left, rgba(56, 189, 248, 0.11), transparent 24rem), var(--app-bg) !important;
            color: var(--text-main) !important;
        }}
        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, #050B14 0%, #0A1628 55%, #07111F 100%) !important;
            border-right: 1px solid rgba(148, 163, 184, 0.18);
        }}
        [data-testid="stSidebar"] * {{ color: #EAF2FF !important; }}

        /* Sidebar filter visibility fix: Streamlit select boxes use their own
           nested BaseWeb elements, so force filter labels, values, inputs,
           dropdown arrows, and captions to readable colors on the dark sidebar. */
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] div,
        [data-testid="stSidebar"] .stMarkdown,
        [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {{
            color: #EAF2FF !important;
        }}
        [data-testid="stSidebar"] div[data-baseweb="select"] > div,
        [data-testid="stSidebar"] div[data-baseweb="input"] > div,
        [data-testid="stSidebar"] input,
        [data-testid="stSidebar"] textarea {{
            background-color: rgba(18, 41, 69, 0.95) !important;
            border: 1px solid rgba(148, 163, 184, 0.38) !important;
            color: #EAF2FF !important;
            -webkit-text-fill-color: #EAF2FF !important;
            border-radius: 12px !important;
        }}
        [data-testid="stSidebar"] div[data-baseweb="select"] span,
        [data-testid="stSidebar"] div[data-baseweb="select"] svg,
        [data-testid="stSidebar"] div[data-baseweb="select"] input {{
            color: #EAF2FF !important;
            fill: #EAF2FF !important;
            -webkit-text-fill-color: #EAF2FF !important;
        }}
        [data-testid="stSidebar"] div[data-baseweb="select"] > div:hover,
        [data-testid="stSidebar"] div[data-baseweb="input"] > div:hover {{
            border-color: #38BDF8 !important;
        }}
        div[data-baseweb="popover"] ul,
        div[data-baseweb="popover"] li,
        div[role="listbox"] {{
            background-color: #0F1F35 !important;
            color: #EAF2FF !important;
        }}
        div[role="option"],
        div[role="option"] span,
        div[data-baseweb="menu"] li,
        div[data-baseweb="menu"] li span {{
            color: #EAF2FF !important;
            background-color: #0F1F35 !important;
        }}
        div[role="option"]:hover,
        div[data-baseweb="menu"] li:hover {{
            background-color: #122945 !important;
        }}

        .block-container {{
            padding-top: 1.6rem;
            padding-bottom: 3rem;
            max-width: 1450px;
        }}
        h1, h2, h3 {{ color: var(--text-main) !important; letter-spacing: -0.02em; }}
        p, span, label, div {{ color: inherit; }}
        .page-title {{
            font-size: 1.9rem;
            font-weight: 800;
            color: var(--text-main);
            margin-bottom: 0.2rem;
        }}
        .page-subtitle {{
            color: var(--text-muted);
            font-size: 0.95rem;
            margin-bottom: 1rem;
        }}
        .metric-card {{
            background: linear-gradient(180deg, var(--panel-bg) 0%, var(--panel-bg-2) 100%);
            border: 1px solid var(--border);
            border-radius: 18px;
            padding: 18px 18px 16px 18px;
            box-shadow: {t['card_shadow']};
            min-height: 134px;
        }}
        .metric-label {{
            color: var(--text-muted);
            font-size: 0.77rem;
            text-transform: uppercase;
            letter-spacing: 0.075em;
            font-weight: 700;
        }}
        .metric-value {{
            color: var(--text-main);
            font-size: 1.72rem;
            font-weight: 800;
            line-height: 1.15;
            margin-top: 0.4rem;
        }}
        .metric-prev {{
            color: var(--text-muted);
            font-size: 0.82rem;
            margin-top: 0.35rem;
        }}
        .delta-up {{ color: var(--danger); font-weight: 800; }}
        .delta-down {{ color: var(--accent-2); font-weight: 800; }}
        .delta-neutral {{ color: var(--text-muted); font-weight: 800; }}
        .panel {{
            background: linear-gradient(180deg, var(--panel-bg) 0%, var(--panel-bg-2) 100%);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 18px;
            box-shadow: {t['card_shadow']};
            margin-bottom: 1rem;
        }}
        .panel-title {{
            color: var(--text-main);
            font-weight: 800;
            font-size: 1.05rem;
            margin-bottom: 0.15rem;
        }}
        .panel-caption {{ color: var(--text-muted); font-size: 0.86rem; margin-bottom: 0.8rem; }}
        .pill {{
            display: inline-block;
            border-radius: 999px;
            padding: 0.22rem 0.62rem;
            font-size: 0.78rem;
            font-weight: 800;
            margin-right: 0.35rem;
        }}
        .pill-danger {{ background: rgba(239,68,68,0.16); color: #FCA5A5; border: 1px solid rgba(239,68,68,0.35); }}
        .pill-warning {{ background: rgba(245,158,11,0.16); color: #FCD34D; border: 1px solid rgba(245,158,11,0.35); }}
        .pill-good {{ background: rgba(34,197,94,0.16); color: #86EFAC; border: 1px solid rgba(34,197,94,0.35); }}
        .pill-info {{ background: rgba(96,165,250,0.16); color: #93C5FD; border: 1px solid rgba(96,165,250,0.35); }}
        .small-muted {{ color: var(--text-muted); font-size: 0.86rem; }}
        .insight-box {{
            border-left: 4px solid var(--accent);
            background: rgba(56,189,248,0.08);
            border-radius: 12px;
            padding: 12px 14px;
            margin-bottom: 0.7rem;
            color: var(--text-main);
        }}
        div[data-testid="stDataFrame"] {{
            border: 1px solid var(--border);
            border-radius: 16px;
            overflow: hidden;
        }}
        .stButton > button, .stDownloadButton > button {{
            border-radius: 12px;
            border: 1px solid var(--border);
            background: linear-gradient(180deg, var(--panel-bg-2), var(--panel-bg));
            color: var(--text-main);
            font-weight: 800;
        }}
        .stButton > button:hover, .stDownloadButton > button:hover {{
            border-color: var(--accent);
            color: var(--accent);
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(title: str, subtitle: str = ""):
    st.markdown(f'<div class="page-title">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="page-subtitle">{subtitle}</div>', unsafe_allow_html=True)


def kpi_card(label: str, value: str, previous: str = "", delta: float | None = None, caption: str = ""):
    if delta is None:
        delta_html = ""
    else:
        cls = "delta-neutral"
        arrow = "→"
        if delta > 0:
            cls = "delta-up"
            arrow = "▲"
        elif delta < 0:
            cls = "delta-down"
            arrow = "▼"
        delta_html = f'<span class="{cls}">{arrow} {abs(delta):.1f}%</span>'
    previous_html = f'<div class="metric-prev">Prev: {previous} {delta_html}</div>' if previous else ""
    caption_html = f'<div class="small-muted">{caption}</div>' if caption else ""
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            {previous_html}
            {caption_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def panel_start(title: str, caption: str = ""):
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown(f'<div class="panel-title">{title}</div>', unsafe_allow_html=True)
    if caption:
        st.markdown(f'<div class="panel-caption">{caption}</div>', unsafe_allow_html=True)


def panel_end():
    st.markdown('</div>', unsafe_allow_html=True)
