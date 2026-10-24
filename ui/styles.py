"""
Modern Professional CSS & Design System for WaterGuard AI — Maharashtra
Clean corporate water-utility dashboard aesthetics with dark navy, water blue, teal accents,
subtle micro-animations, glassmorphism, responsive cards, and accessible status badges.
"""

CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }

    /* Subtle pulse animation for active monitoring */
    @keyframes pulse-subtle {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.75; transform: scale(1.02); }
    }

    @keyframes live-dot {
        0%, 100% { box-shadow: 0 0 0 0 rgba(14, 165, 233, 0.6); }
        70% { box-shadow: 0 0 0 6px rgba(14, 165, 233, 0); }
    }

    /* Top App Header Banner */
    .app-header-container {
        background: linear-gradient(135deg, #091322 0%, #0f172a 45%, #0369a1 85%, #0d9488 100%);
        padding: 24px 32px;
        border-radius: 16px;
        margin-bottom: 24px;
        box-shadow: 0 12px 30px -6px rgba(15, 23, 42, 0.35), 0 4px 12px -2px rgba(2, 132, 199, 0.2);
        border: 1px solid rgba(255, 255, 255, 0.12);
        position: relative;
        overflow: hidden;
    }
    .app-header-container::before {
        content: "";
        position: absolute;
        top: -40px;
        right: -40px;
        width: 180px;
        height: 180px;
        background: radial-gradient(circle, rgba(56, 189, 248, 0.15) 0%, transparent 70%);
        pointer-events: none;
    }
    .app-header-title {
        font-size: 28px;
        font-weight: 800;
        color: #ffffff;
        margin: 0;
        letter-spacing: -0.025em;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .app-header-subtitle {
        font-size: 14px;
        color: #94a3b8;
        margin-top: 6px;
        margin-bottom: 0;
        font-weight: 400;
    }
    .prototype-pill {
        background: rgba(14, 165, 233, 0.2);
        color: #38bdf8;
        border: 1px solid rgba(56, 189, 248, 0.4);
        padding: 4px 14px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        margin-top: 10px;
        backdrop-filter: blur(4px);
    }
    .live-indicator-dot {
        width: 7px;
        height: 7px;
        background: #38bdf8;
        border-radius: 50%;
        display: inline-block;
        animation: live-dot 2s infinite;
    }

    /* Metric Card Styling */
    .metric-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 20px 22px;
        box-shadow: 0 1px 3px 0 rgba(15, 23, 42, 0.05), 0 10px 15px -3px rgba(15, 23, 42, 0.02);
        transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.2s ease, border-color 0.2s ease;
        height: 100%;
        position: relative;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px -4px rgba(15, 23, 42, 0.1), 0 4px 8px -2px rgba(2, 132, 199, 0.06);
        border-color: #94a3b8;
    }
    .metric-label {
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #64748b;
        margin-bottom: 6px;
    }
    .metric-value {
        font-size: 26px;
        font-weight: 700;
        color: #0f172a;
        line-height: 1.2;
        letter-spacing: -0.02em;
    }
    .metric-delta {
        font-size: 12px;
        font-weight: 500;
        margin-top: 6px;
        display: flex;
        align-items: center;
        gap: 4px;
    }

    /* Status Badges */
    .badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 600;
        line-height: 1;
    }
    .badge-normal {
        background: #ecfdf5;
        color: #059669;
        border: 1px solid #a7f3d0;
    }
    .badge-monitor {
        background: #fffbeb;
        color: #d97706;
        border: 1px solid #fde68a;
    }
    .badge-inspection {
        background: #fff7ed;
        color: #ea580c;
        border: 1px solid #fed7aa;
    }
    .badge-urgent {
        background: #fef2f2;
        color: #dc2626;
        border: 1px solid #fecaca;
    }
    .badge-gray {
        background: #f1f5f9;
        color: #475569;
        border: 1px solid #e2e8f0;
    }
    .badge-maharashtra {
        background: rgba(2, 132, 199, 0.12);
        color: #0284c7;
        border: 1px solid rgba(2, 132, 199, 0.35);
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        padding: 3px 8px;
        border-radius: 4px;
        display: inline-flex;
        align-items: center;
        gap: 4px;
    }

    /* Callout & Advisory Banners */
    .advisory-banner {
        background: #f8fafc;
        border-left: 4px solid #0284c7;
        padding: 14px 20px;
        border-radius: 0 10px 10px 0;
        font-size: 13px;
        color: #334155;
        margin-bottom: 20px;
        border-top: 1px solid #e2e8f0;
        border-right: 1px solid #e2e8f0;
        border-bottom: 1px solid #e2e8f0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    }
    .advisory-banner strong {
        color: #0369a1;
    }

    /* Table styling tweaks */
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
        border: 1px solid #e2e8f0;
    }

    /* Scenario Bar Card */
    .scenario-box {
        background: linear-gradient(135deg, #f0fdfa 0%, #f8fafc 100%);
        border: 1px solid #99f6e4;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 20px;
        box-shadow: 0 2px 6px rgba(13, 148, 136, 0.05);
    }

    /* Maharashtra Dam Card */
    .dam-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px 18px;
        margin-bottom: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        transition: transform 0.15s ease, border-color 0.15s ease;
    }
    .dam-card:hover {
        transform: translateY(-2px);
        border-color: #0284c7;
        box-shadow: 0 4px 12px rgba(2, 132, 199, 0.08);
    }

    /* Workflow Step Card */
    .workflow-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 20px;
        height: 100%;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        position: relative;
    }
    .workflow-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 18px -4px rgba(15, 23, 42, 0.08);
        border-color: #38bdf8;
    }

    /* Streamlit Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: 1px solid #e2e8f0;
    }
    .stTabs [data-baseweb="tab"] {
        font-weight: 600;
        font-size: 13px;
        color: #64748b;
        padding: 8px 16px;
        border-radius: 6px 6px 0 0;
    }
    .stTabs [aria-selected="true"] {
        color: #0284c7 !important;
        border-bottom: 2px solid #0284c7 !important;
    }

    /* Button Enhancements */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        font-size: 13px;
        transition: all 0.15s ease;
    }
    .stButton > button:hover {
        border-color: #0284c7;
        color: #0284c7;
        transform: translateY(-1px);
        box-shadow: 0 2px 6px rgba(2, 132, 199, 0.15);
    }
</style>
"""
