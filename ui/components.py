"""
Reusable UI Components and Visual Presentation Helpers
"""
import streamlit as st
import plotly.graph_objects as go
import config


def render_header():
    """Renders the top branding header and educational prototype disclaimer."""
    st.markdown(f"""
    <div class="app-header-container">
        <h1 class="app-header-title">
            <span>💧</span> {config.APP_TITLE}
        </h1>
        <p class="app-header-subtitle">
            {config.APP_SUBTITLE} • v{config.VERSION}
        </p>
        <div class="prototype-pill">
            🔬 Simulated Prototype Mode • No Live Municipal Connection
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_disclaimer_banner():
    """Renders standard regulatory / educational disclaimer banner."""
    st.markdown(f"""
    <div class="advisory-banner">
        <strong>⚠️ OPERATIONAL NOTICE:</strong> {config.DISCLAIMER_TEXT}
    </div>
    """, unsafe_allow_html=True)


def render_badge(category: str) -> str:
    """Returns HTML for an accessible status badge."""
    c_upper = str(category).upper()
    if "URGENT" in c_upper or "CRITICAL" in c_upper or "BURST" in c_upper:
        return f'<span class="badge badge-urgent">● {category}</span>'
    elif "INSPECTION" in c_upper or "LEAK" in c_upper or "HIGH" in c_upper:
        return f'<span class="badge badge-inspection">▲ {category}</span>'
    elif "MONITOR" in c_upper or "MEDIUM" in c_upper or "SURGE" in c_upper or "WARNING" in c_upper:
        return f'<span class="badge badge-monitor">◆ {category}</span>'
    elif "NORMAL" in c_upper or "HEALTHY" in c_upper or "RESOLVED" in c_upper or "COMPLETED" in c_upper:
        return f'<span class="badge badge-normal">✔ {category}</span>'
    else:
        return f'<span class="badge badge-gray">■ {category}</span>'


def apply_chart_theme(fig: go.Figure, title: str = "", height: int = 380) -> go.Figure:
    """Applies a clean, modern, accessible theme to Plotly figures."""
    fig.update_layout(
        title={
            "text": title,
            "y": 0.95,
            "x": 0.02,
            "xanchor": "left",
            "yanchor": "top",
            "font": {"size": 15, "color": "#0f172a", "family": "Inter, sans-serif", "weight": 600},
        },
        template="plotly_white",
        height=height,
        margin={"l": 45, "r": 25, "t": 55, "b": 40},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
        hoverlabel={"font": {"family": "Inter, sans-serif"}, "bgcolor": "#0f172a", "font_color": "#ffffff"},
        xaxis={
            "gridcolor": "#f1f5f9",
            "linecolor": "#cbd5e1",
            "tickfont": {"family": "Inter, sans-serif", "size": 11, "color": "#64748b"},
        },
        yaxis={
            "gridcolor": "#f1f5f9",
            "linecolor": "#cbd5e1",
            "tickfont": {"family": "Inter, sans-serif", "size": 11, "color": "#64748b"},
        },
    )
    return fig
