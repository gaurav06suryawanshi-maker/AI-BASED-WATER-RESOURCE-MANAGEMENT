"""
Information Slides and Technical Reference View
Provides interactive educational presentation slides covering the municipal water journey,
multi-indicator leak detection theory, explainable risk scoring, and hardware architecture.
Enhanced with slide-wise technical hero images, clickable references, and comprehensive bibliography.
"""
import base64
from pathlib import Path
import streamlit as st
import config
from ui.components import render_disclaimer_banner


def load_slide_image_base64(filename: str) -> tuple[str | None, str]:
    """
    Safely loads a local slide image and converts it to a base64 data URI.
    Returns (data_uri, local_path_str) if file exists, or (None, local_path_str) on fallback.
    """
    img_path = config.BASE_DIR / "assets" / "slides" / filename
    if img_path.is_file():
        try:
            with open(img_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode("utf-8")
                suffix = img_path.suffix.lower()
                mime = "image/png" if suffix == ".png" else "image/jpeg"
                return f"data:{mime};base64,{encoded}", str(img_path)
        except Exception:
            return None, str(img_path)
    return None, str(img_path)


def render_slides_view():
    st.markdown("## 📚 Information Slides & Technical Reference")
    render_disclaimer_banner()

    slides = [
        {
            "id": 1,
            "title": "Slide 1: Municipal Water Journey & Network Topology",
            "subtitle": "From Source Impoundment to Household Reticulation",
            "image_file": "slide1_water_network.jpg",
            "image_caption": "Municipal raw water impoundment dam, central treatment works, and transmission trunk network topology.",
            "image_attribution": "WaterGuard AI Engineering Asset • Digital Twin Photorealistic Render",
            "content": """
### 1. Water Journey Lifecycle
The simulated infrastructure models the end-to-end municipal water transmission lifecycle across six critical stages:

1. **Water Source / Dam (Intake):**
   - **Pine Valley Dam** ($12,500,000\\text{ m}^3$ storage capacity, safe yield $4,500\\text{ m}^3/\\text{h}$)
   - **Clearwater River Abstraction Intake** ($5,000,000\\text{ m}^3$)
2. **Water Treatment Plant (WTP-MAIN):**
   - Central water treatment works featuring coagulation, sand filtration, chlorination ($1.25\\text{ ppm}$ residual), and high-lift pumping ($2,450\\text{ m}^3/\\text{h}$ throughput).
3. **Main Transmission Trunk (`TX-101`):**
   - $6.8\\text{ km}$, $900\\text{ mm}$ ductile iron transmission trunk operating under $5.8\\text{ bar}$ nominal pressure.
4. **Monitoring & Junction Stations (`MS-01` to `MS-05`):**
   - Telemetry nodes recording upstream/downstream pressure, flow, acoustic frequency, and pipe-wall vibration.
5. **City Storage Reservoirs:**
   - **North Hill Elevated Reservoir** ($45,000\\text{ m}^3$, $82\\%$ storage level)
   - **South Valley Ground Reservoir** ($60,000\\text{ m}^3$, $17.5\\%$ low water alert)
6. **Distribution Metered Areas (DMAs):**
   - Metro East Residential Feeder (`DN-201`), Commercial Zone (`DN-202`), Industrial Loop (`DN-203`), and Legacy Heritage Reticulation (`DN-204`).
            """,
            "references": [
                {
                    "source": "US EPA",
                    "title": "Drinking Water Infrastructure & System Capacity",
                    "url": "https://www.epa.gov/dwcapacity",
                    "search_url": "https://www.google.com/search?q=municipal+water+transmission+network+topology+trunk+main",
                },
                {
                    "source": "World Bank",
                    "title": "Water Supply and Sanitation Global Practice",
                    "url": "https://www.worldbank.org/en/topic/water",
                    "search_url": "https://www.google.com/search?q=World+Bank+water+supply+and+sanitation+global+practice",
                },
            ],
        },
        {
            "id": 2,
            "title": "Slide 2: Physics-Based Multi-Indicator Detection",
            "subtitle": "Eliminating False Alarms via Multi-Modal Physical Corroboration",
            "image_file": "slide2_leak_detection.jpg",
            "image_caption": "Underground pipe breach with acoustic vibration sensors, dual pressure monitoring, and cloud telemetry.",
            "image_attribution": "WaterGuard AI Engineering Asset • Digital Twin Photorealistic Render",
            "content": """
### 2. Multi-Indicator Detection Principle
WaterGuard AI **never** declares a pipeline leak based on a single sensor reading. An anomaly requires cross-modal corroboration:

- **1. Data Quality Screening First:**
  - Detects sensor telemetry faults (Frozen flatline $\\sigma=0$, Missing packet dropouts, Unrealistic values $<0\\text{ bar}$, Delayed arrival).
  - Corrupted sensors generate instrument maintenance alerts rather than false leak alarms.

- **2. Volumetric Mass Conservation:**
  - Evaluates unexplained difference:
    $$\\text{Discrepancy} = Q_{\\text{in}} - Q_{\\text{out}} - \\Delta S_{\\text{reservoir}} - W_{\\text{authorized}}$$
  - Accounts for $\\pm 2\\%$ composite electromagnetic meter tolerance.

- **3. Hydraulic Friction Gradient (Hazen-Williams):**
  - Compares measured pressure drop against theoretical head loss:
    $$h_f = 10.67 \\cdot \\frac{L}{C^{1.852} \\cdot D^{4.8704}} \\cdot Q^{1.852}$$
  - Distinguishes normal friction losses from abnormal orifice breaches.

- **4. Acoustic & Vibration Signatures:**
  - Detects continuous high-frequency pipe wall hiss ($>50$ index) and turbulent vibration ($>3.0\\text{ mm/s RMS}$) characteristic of pressurized orifice discharge.
            """,
            "references": [
                {
                    "source": "Hindustan Times",
                    "title": "Urban Agenda: How new tech is helping plug leaks and reshaping water management",
                    "url": "https://www.hindustantimes.com/analysis/urban-agenda-how-new-tech-is-helping-plug-leaks-and-reshaping-water-management-101713798800871.html",
                    "search_url": "https://www.google.com/search?q=Hindustan+Times+urban+agenda+how+new+tech+is+helping+plug+leaks+and+reshaping+water+management",
                },
                {
                    "source": "US EPA",
                    "title": "Control and Mitigation of Drinking Water Losses in Distribution Systems",
                    "url": "https://www.epa.gov/sites/default/files/2015-04/documents/epa816r14002.pdf",
                    "search_url": "https://www.google.com/search?q=physics+based+multi+indicator+pipeline+leak+detection+pressure+acoustic",
                },
            ],
        },
        {
            "id": 3,
            "title": "Slide 3: Explainable Risk-to-Response Intelligence",
            "subtitle": "0–100 Inspection Priority Index — Decoupling Immediate from Long-Term Factors",
            "image_file": "slide3_risk_intelligence.jpg",
            "image_caption": "AI utility operations center dashboard displaying 0–100 explainable risk scoring and neural network anomaly detection.",
            "image_attribution": "WaterGuard AI Engineering Asset • Digital Twin Photorealistic Render",
            "content": """
### 3. Explainable Risk-to-Response Scoring
The inspection priority index is an engineering decision-support ranking that decomposes into two distinct, explainable subtotals:

$$\\text{Priority Score (0–100)} = \\text{Immediate Telemetry Score (Max 55)} + \\text{Long-Term Asset Deterioration (Max 45)}$$

#### Factor Breakdown:
| Factor Category | Maximum Points | Contributing Indicators |
|---|---|---|
| **Active Hydraulic Imbalance** | **35 pts** | Sustained flow deficit, pressure collapse, sudden burst breach |
| **Acoustic Evidence** | **20 pts** | Cavitation vibration, high-frequency pipe wall orifice hiss |
| **Asset Material & Age** | **20 pts** | Legacy Cast Iron (48 yrs), Asbestos-Cement, corrosive soil |
| **Failure & Repair History** | **15 pts** | Number of previous pipe repairs recorded on segment |
| **Criticality & Consequence** | **10 pts** | Hospital/main supply tier, nearby civil excavation activity |

#### Priority Categories:
- **Normal (0–29):** Low risk; standard annual preventative inspection.
- **Monitor (30–59):** Track minimum night flows (02:00–04:00) and review cathodic protection.
- **Inspection Recommended (60–79):** Schedule non-destructive testing (CCTV/acoustic ground mic) within 30 days.
- **Urgent Review (80–100):** Immediate field dispatch or emergency valve isolation.
- **Insufficient Data:** Sensor quality score $< 40\\%$; transducer maintenance required.
            """,
            "references": [
                {
                    "source": "US EPA",
                    "title": "Distribution System Condition Assessment & Asset Management",
                    "url": "https://www.epa.gov/water-infrastructure-finance",
                    "search_url": "https://www.google.com/search?q=water+pipeline+risk+scoring+asset+deterioration+priority+index",
                },
                {
                    "source": "US Dept of Energy",
                    "title": "Energy-Water Nexus Analytics & Critical Infrastructure Resilience",
                    "url": "https://www.energy.gov/policy/energy-water-nexus",
                    "search_url": "https://www.google.com/search?q=US+Department+of+Energy+Energy+Water+Nexus+smart+sensor+systems",
                },
            ],
        },
        {
            "id": 4,
            "title": "Slide 4: Water-Balance & Error Propagation",
            "subtitle": "Root-Sum-Square Measurement Uncertainty Bands",
            "image_file": "slide4_water_balance.jpg",
            "image_caption": "Industrial volumetric flow balancing telemetry station with electromagnetic meters and uncertainty band analysis.",
            "image_attribution": "WaterGuard AI Engineering Asset • Digital Twin Photorealistic Render",
            "content": """
### 4. Mass Conservation & Uncertainty Bounds
When evaluating municipal water balance, raw discrepancies can be misleading without quantifying measurement tolerance.

#### Error Propagation Formula:
Standard electromagnetic flowmeters and ultrasonic transducers have an inherent calibration uncertainty of approximately $\\pm 2\\%$.
Using Gaussian error propagation, the total composite uncertainty of the water balance is:

$$\\sigma_{\\text{balance}} = \\sqrt{\\sigma_{Q_{\\text{in}}}^2 + \\sigma_{Q_{\\text{out}}}^2 + \\sigma_{\\Delta S}^2} = \\sqrt{(0.02 \\cdot Q_{\\text{in}})^2 + (0.02 \\cdot Q_{\\text{out}})^2 + (0.02 \\cdot |\\Delta S|)^2}$$

The **95% Confidence Interval Band** is:
$$\\text{Uncertainty Band} = \\pm 1.96 \\cdot \\sigma_{\\text{balance}}$$

#### Decision Threshold:
- If $\\text{Discrepancy} \\le \\text{Uncertainty Band}$: Labeled as **Balanced (Within Meter Tolerance)**.
- If $\\text{Discrepancy} > \\text{Uncertainty Band}$: Labeled as **Unexplained Flow Deficit**; secondary acoustic and pressure corroboration is required before diagnosing leakage.
            """,
            "references": [
                {
                    "source": "World Bank",
                    "title": "The Challenge of Reducing Non-Revenue Water (NRW) in Developing Countries",
                    "url": "https://www.worldbank.org/en/topic/water",
                    "search_url": "https://www.google.com/search?q=World+Bank+water+global+practice+non+revenue+water+reduction",
                },
                {
                    "source": "US EPA",
                    "title": "WaterSense Program & AWWA M36 Water Audit Methodology",
                    "url": "https://www.epa.gov/watersense",
                    "search_url": "https://www.google.com/search?q=IWA+AWWA+water+balance+non+revenue+water+error+propagation",
                },
            ],
        },
        {
            "id": 5,
            "title": "Slide 5: Predictive Maintenance & Asset Lifecycle",
            "subtitle": "Work Orders, Condition Grading & Field Inspection Log",
            "image_file": "slide5_predictive_maint.jpg",
            "image_caption": "Field engineers using ultrasonic pipe thickness gauges, acoustic ground mics, and digital diagnostic tablets.",
            "image_attribution": "WaterGuard AI Engineering Asset • Digital Twin Photorealistic Render",
            "content": """
### 5. Maintenance Lifecycle & Work Orders
WaterGuard AI bridges predictive analytics and operational field workflows:

1. **Diagnostic Condition Grades (Model-Derived):**
   - **Grade 1 - Very Good:** Minor cosmetic wear; nominal hydraulic operation.
   - **Grade 2 - Good:** Expected aging; standard annual service.
   - **Grade 3 - Moderate:** Signs of gradual deterioration; plan preventative maintenance.
   - **Grade 4 - Poor:** Significant deterioration; field inspection recommended.
   - **Grade 5 - Critical:** Severe defect or failure risk; immediate physical intervention.

2. **Full Work Order Lifecycle:**
   - **Pending:** Auto-generated from diagnostic priority screening.
   - **Under Review:** Assigned to engineering supervisor for scoping.
   - **Scheduled:** Contractor or technician assigned with target date.
   - **Completed:** Work performed and logged with resolution notes in SQLite.

3. **Field Findings Calibration:**
   - Authorized inspectors record physical soil moisture, cathodic protection status, and pipe condition to calibrate future model assessments.
            """,
            "references": [
                {
                    "source": "US EPA",
                    "title": "Asset Management Resources for Small and Large Drinking Water Systems",
                    "url": "https://www.epa.gov/dwcapacity/asset-management-resources-small-drinking-water-systems",
                    "search_url": "https://www.google.com/search?q=water+utility+predictive+maintenance+asset+lifecycle+condition+grading",
                },
                {
                    "source": "US Dept of Energy",
                    "title": "Advanced Water Asset Reliability & Pumping Optimization",
                    "url": "https://www.energy.gov/eere/water",
                    "search_url": "https://www.google.com/search?q=water+utility+pipe+condition+grading+predictive+maintenance",
                },
            ],
        },
        {
            "id": 6,
            "title": "Slide 6: Hardware Roadmap & ESP32 Integration",
            "subtitle": "Modular Transition from Simulated Telemetry to Physical IoT Sensing",
            "image_file": "slide6_esp32_iot.jpg",
            "image_caption": "Industrial IP67 IoT telemetry unit with ESP32 microcontroller, LoRaWAN antenna, and 4-20mA sensor interfaces.",
            "image_attribution": "WaterGuard AI Engineering Asset • Digital Twin Photorealistic Render",
            "content": """
### 6. Physical Hardware & ESP32 Integration Architecture
WaterGuard AI is designed with clean, abstracted interfaces so physical IoT hardware can be integrated seamlessly:

```
[Industrial 4-20mA Pressure Transducer] ──┐
[Electromagnetic Pulse Flow Meter]     ├──> [ESP32-S3 IoT Microcontroller Node] ──(MQTT / LoRaWAN)──> [Ingestion API] ──> [SQLite DB]
[Piezoelectric Contact Accelerometer]  ──┘
```

#### Ingestion Schema:
Physical ESP32 units transmit telemetry matching the exact schema implemented in `models/sensor.py`:
```json
{
  "timestamp": "2026-10-24 08:30:00",
  "station_id": "MS-03",
  "segment_id": "TX-101",
  "sensor_type": "PRESSURE",
  "value": 5.82,
  "unit": "bar",
  "health_status": "HEALTHY",
  "is_synthetic": 0
}
```
Because the `SensorQualityFilter` and `AnomalyDetectionEngine` operate on standard dictionaries and pandas dataframes, physical hardware streams will feed directly into the SQLite `sensor_readings` table without rewriting any detection or reporting logic.
            """,
            "references": [
                {
                    "source": "US Dept of Energy",
                    "title": "Smart Sensors and Edge Telemetry Controls for Water Infrastructure",
                    "url": "https://www.energy.gov/policy/energy-water-nexus",
                    "search_url": "https://www.google.com/search?q=ESP32+industrial+4-20mA+pressure+sensor+water+telemetry+LoRaWAN+MQTT",
                },
                {
                    "source": "Espressif Systems",
                    "title": "ESP32 Series Industrial IoT Microcontroller Architecture",
                    "url": "https://www.espressif.com/en/products/socs/esp32",
                    "search_url": "https://www.google.com/search?q=ESP32-S3+IoT+edge+sensor+telemetry+architecture",
                },
            ],
        },
    ]

    # Slide navigation
    col_sel, col_stat = st.columns([2, 1])
    with col_sel:
        slide_titles = [f"{s['id']}. {s['title'].removeprefix('Slide ' + str(s['id']) + ': ')}" for s in slides]
        chosen_slide_idx = st.selectbox(
            "Navigate Presentation Slides:",
            options=range(len(slides)),
            format_func=lambda i: slide_titles[i],
            index=0,
        )

    chosen_slide = slides[chosen_slide_idx]
    with col_stat:
        st.markdown(f"""
        <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 10px 14px; font-size: 13px; color: #166534; margin-top: 4px;">
            <strong>Slide {chosen_slide['id']} of {len(slides)}</strong> • {chosen_slide['subtitle']}
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Display Hero Card with Slide-Wise Image & Subtle Dark-Blue Overlay (Plan 1)
    data_uri, img_path_str = load_slide_image_base64(chosen_slide["image_file"])
    if data_uri:
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, rgba(15, 23, 42, 0.90) 0%, rgba(30, 41, 59, 0.82) 45%, rgba(2, 132, 199, 0.72) 100%), url('{data_uri}') center / cover no-repeat;
            border: 1px solid rgba(255, 255, 255, 0.18);
            border-radius: 14px;
            padding: 28px 32px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.25);
            margin-bottom: 20px;
        ">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; flex-wrap: wrap;">
                <div style="flex: 1; min-width: 280px;">
                    <span style="background: rgba(14, 165, 233, 0.28); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.5); padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; display: inline-block; margin-bottom: 10px;">
                        Slide {chosen_slide['id']} • {chosen_slide['subtitle']}
                    </span>
                    <h2 style="color: #ffffff; margin: 0 0 6px 0; font-size: 26px; font-weight: 700; text-shadow: 0 2px 4px rgba(0,0,0,0.5);">{chosen_slide['title']}</h2>
                    <p style="color: #cbd5e1; font-size: 14px; margin: 0; font-weight: 400; text-shadow: 0 1px 2px rgba(0,0,0,0.6);">{chosen_slide['subtitle']}</p>
                </div>
                <div style="background: rgba(15, 23, 42, 0.82); backdrop-filter: blur(8px); border: 1px solid rgba(255, 255, 255, 0.16); border-radius: 8px; padding: 10px 14px; font-size: 12px; color: #cbd5e1; max-width: 360px;">
                    <div style="font-weight: 600; color: #38bdf8; margin-bottom: 3px; display: flex; align-items: center; gap: 5px;">
                        <span>📷</span> Technical Illustration
                    </div>
                    <div>{chosen_slide['image_caption']}</div>
                    <div style="color: #94a3b8; font-size: 10px; margin-top: 4px;">{chosen_slide['image_attribution']}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Graceful missing-image fallback
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0369a1 100%);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 14px;
            padding: 28px 32px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.15);
            margin-bottom: 20px;
        ">
            <span style="background: rgba(14, 165, 233, 0.25); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.5); padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; display: inline-block; margin-bottom: 10px;">
                Slide {chosen_slide['id']} • {chosen_slide['subtitle']}
            </span>
            <h2 style="color: #ffffff; margin: 0 0 6px 0; font-size: 26px; font-weight: 700;">{chosen_slide['title']}</h2>
            <p style="color: #94a3b8; font-size: 14px; margin: 0 0 12px 0;">{chosen_slide['subtitle']}</p>
            <div style="background: rgba(245, 158, 11, 0.15); border: 1px solid rgba(245, 158, 11, 0.4); border-radius: 6px; padding: 6px 12px; font-size: 11px; color: #fde68a; display: inline-flex; align-items: center; gap: 6px;">
                <span>⚠️</span> <span>Local image file not found (<code>{chosen_slide['image_file']}</code>) — Active dark-blue gradient fallback</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Optional Full High-Resolution Diagram Expander
    with st.expander("🔍 View Full High-Resolution Technical Diagram & Sensor Schematic", expanded=False):
        if data_uri:
            img_file_path = config.BASE_DIR / "assets" / "slides" / chosen_slide["image_file"]
            st.image(str(img_file_path), caption=f"Slide {chosen_slide['id']}: {chosen_slide['image_caption']}", use_container_width=True)
        else:
            st.warning(f"Image asset '{chosen_slide['image_file']}' is currently missing from assets/slides/.")

    # Display Slide Content (Plain high-contrast background to preserve math/table legibility)
    st.markdown(chosen_slide["content"])

    # Slide-Specific Clickable References & Search Queries (Plan 2)
    if "references" in chosen_slide and chosen_slide["references"]:
        ref_items_html = "".join([
            f"""
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px 16px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; gap: 14px; flex-wrap: wrap;">
                <div style="flex: 1; min-width: 240px;">
                    <span style="font-size: 11px; font-weight: 700; color: #0284c7; text-transform: uppercase; letter-spacing: 0.05em; background: #e0f2fe; padding: 2px 8px; border-radius: 4px; margin-right: 6px;">{r['source']}</span>
                    <strong style="font-size: 13px; color: #0f172a;">{r['title']}</strong>
                </div>
                <div style="display: flex; gap: 8px; align-items: center;">
                    <a href="{r['url']}" target="_blank" rel="noopener noreferrer" style="background: #0284c7; color: #ffffff; text-decoration: none; padding: 6px 12px; border-radius: 6px; font-size: 12px; font-weight: 500; display: inline-flex; align-items: center; gap: 4px;">
                        🔗 Source Link ↗
                    </a>
                    <a href="{r['search_url']}" target="_blank" rel="noopener noreferrer" style="background: #f1f5f9; color: #334155; border: 1px solid #cbd5e1; text-decoration: none; padding: 6px 12px; border-radius: 6px; font-size: 12px; font-weight: 500; display: inline-flex; align-items: center; gap: 4px;">
                        🔍 Google Search ↗
                    </a>
                </div>
            </div>
            """ for r in chosen_slide["references"]
        ])
        st.markdown(f"""
        <div style="background: #f8fafc; border: 1px solid #cbd5e1; border-left: 4px solid #0284c7; border-radius: 0 10px 10px 0; padding: 16px 20px; margin-top: 20px; margin-bottom: 24px;">
            <div style="font-size: 12px; font-weight: 700; color: #0f172a; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 12px; display: flex; align-items: center; gap: 6px;">
                <span>📚</span> Curated Literature & Search Queries for Slide {chosen_slide['id']}
            </div>
            {ref_items_html}
        </div>
        """, unsafe_allow_html=True)

    # Slide Next/Previous buttons
    c_prev, c_space, c_next = st.columns([1, 4, 1])
    with c_prev:
        if chosen_slide_idx > 0:
            if st.button("⬅ Previous Slide"):
                st.session_state["chosen_slide_idx"] = chosen_slide_idx - 1
                st.rerun()
    with c_next:
        if chosen_slide_idx < len(slides) - 1:
            if st.button("Next Slide ➡"):
                st.session_state["chosen_slide_idx"] = chosen_slide_idx + 1
                st.rerun()

    # -------------------------------------------------------------
    # Final Comprehensive References & Technical Bibliography (Plan 2)
    # -------------------------------------------------------------
    st.markdown("---")

    ref_banner_uri, _ = load_slide_image_base64("references_library.jpg")
    ref_bg_css = f"linear-gradient(135deg, rgba(15, 23, 42, 0.92) 0%, rgba(30, 41, 59, 0.85) 50%, rgba(3, 105, 161, 0.75) 100%), url('{ref_banner_uri}') center / cover no-repeat" if ref_banner_uri else "linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0369a1 100%)"

    st.markdown(f"""
    <div style="
        background: {ref_bg_css};
        border: 1px solid rgba(255, 255, 255, 0.18);
        border-radius: 14px;
        padding: 28px 32px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.25);
        margin-bottom: 24px;
    ">
        <span style="background: rgba(14, 165, 233, 0.28); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.5); padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; display: inline-block; margin-bottom: 10px;">
            Technical Bibliography & Regulatory Standards
        </span>
        <h2 style="color: #ffffff; margin: 0 0 6px 0; font-size: 26px; font-weight: 700; text-shadow: 0 2px 4px rgba(0,0,0,0.5);">
            📑 Comprehensive Project References & Authoritative Sources
        </h2>
        <p style="color: #cbd5e1; font-size: 14px; margin: 0; font-weight: 400; text-shadow: 0 1px 2px rgba(0,0,0,0.6);">
            Primary literature, investigative journalism, international water-loss auditing methodologies, and government research roadmaps.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # 2x2 Grid of Primary Regulatory & Academic References
    c1, c2 = st.columns(2)

    with c1:
        # Card 1: Hindustan Times Feature Article
        st.markdown("""
        <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 22px 24px; box-shadow: 0 2px 6px rgba(0,0,0,0.04); margin-bottom: 20px; height: 100%; display: flex; flex-direction: column; justify-content: space-between;">
            <div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span style="background: #fee2e2; color: #b91c1c; font-size: 11px; font-weight: 700; padding: 3px 10px; border-radius: 12px; text-transform: uppercase; letter-spacing: 0.05em;">Featured Media Analysis</span>
                    <span style="font-size: 12px; color: #64748b;">Hindustan Times</span>
                </div>
                <h4 style="color: #0f172a; margin: 0 0 8px 0; font-size: 16px; font-weight: 700; line-height: 1.4;">
                    Urban Agenda: How new tech is helping plug leaks and reshaping water management
                </h4>
                <p style="color: #475569; font-size: 13px; line-height: 1.5; margin-bottom: 16px;">
                    Investigative engineering analysis examining how modern IoT acoustic sensors, digital pressure transients, and automated network segregation empower municipal utilities to eliminate physical water losses and modernize aging conveyance trunks.
                </p>
            </div>
            <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                <a href="https://www.hindustantimes.com/analysis/urban-agenda-how-new-tech-is-helping-plug-leaks-and-reshaping-water-management-101713798800871.html" target="_blank" rel="noopener noreferrer" style="background: #0284c7; color: #ffffff; text-decoration: none; padding: 7px 14px; border-radius: 6px; font-size: 12px; font-weight: 600; display: inline-flex; align-items: center; gap: 4px;">
                    📖 Read Article (Hindustan Times) ↗
                </a>
                <a href="https://www.google.com/search?q=Hindustan+Times+Urban+Agenda+How+new+tech+is+helping+plug+leaks+and+reshaping+water+management" target="_blank" rel="noopener noreferrer" style="background: #f1f5f9; color: #334155; border: 1px solid #cbd5e1; text-decoration: none; padding: 7px 14px; border-radius: 6px; font-size: 12px; font-weight: 600; display: inline-flex; align-items: center; gap: 4px;">
                    🔍 Google Search ↗
                </a>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Card 3: US EPA Technical Guidance
        st.markdown("""
        <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 22px 24px; box-shadow: 0 2px 6px rgba(0,0,0,0.04); margin-bottom: 20px; height: 100%; display: flex; flex-direction: column; justify-content: space-between;">
            <div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span style="background: #dbeafe; color: #1d4ed8; font-size: 11px; font-weight: 700; padding: 3px 10px; border-radius: 12px; text-transform: uppercase; letter-spacing: 0.05em;">Regulatory Technical Report</span>
                    <span style="font-size: 12px; color: #64748b;">US EPA Office of Water</span>
                </div>
                <h4 style="color: #0f172a; margin: 0 0 8px 0; font-size: 16px; font-weight: 700; line-height: 1.4;">
                    Control and Mitigation of Drinking Water Losses in Distribution Systems
                </h4>
                <p style="color: #475569; font-size: 13px; line-height: 1.5; margin-bottom: 16px;">
                    Technical manual EPA 816-R-14-002 defining best-practice hydraulic head loss modeling, acoustic leak surveying, pressure surge reduction, and component analysis of non-revenue water in pressurized systems.
                </p>
            </div>
            <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                <a href="https://www.epa.gov/sites/default/files/2015-04/documents/epa816r14002.pdf" target="_blank" rel="noopener noreferrer" style="background: #0284c7; color: #ffffff; text-decoration: none; padding: 7px 14px; border-radius: 6px; font-size: 12px; font-weight: 600; display: inline-flex; align-items: center; gap: 4px;">
                    🏛️ EPA Report (PDF) ↗
                </a>
                <a href="https://www.google.com/search?q=EPA+Control+and+Mitigation+of+Drinking+Water+Losses+in+Distribution+Systems" target="_blank" rel="noopener noreferrer" style="background: #f1f5f9; color: #334155; border: 1px solid #cbd5e1; text-decoration: none; padding: 7px 14px; border-radius: 6px; font-size: 12px; font-weight: 600; display: inline-flex; align-items: center; gap: 4px;">
                    🔍 Google Search ↗
                </a>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        # Card 2: World Bank Water Global Practice
        st.markdown("""
        <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 22px 24px; box-shadow: 0 2px 6px rgba(0,0,0,0.04); margin-bottom: 20px; height: 100%; display: flex; flex-direction: column; justify-content: space-between;">
            <div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span style="background: #dcfce7; color: #15803d; font-size: 11px; font-weight: 700; padding: 3px 10px; border-radius: 12px; text-transform: uppercase; letter-spacing: 0.05em;">Global Standard</span>
                    <span style="font-size: 12px; color: #64748b;">The World Bank Group</span>
                </div>
                <h4 style="color: #0f172a; margin: 0 0 8px 0; font-size: 16px; font-weight: 700; line-height: 1.4;">
                    The Challenge of Reducing Non-Revenue Water (NRW) in Developing Countries
                </h4>
                <p style="color: #475569; font-size: 13px; line-height: 1.5; margin-bottom: 16px;">
                    Global Water Practice paper detailing the International Water Association (IWA) standardized water balance, root-sum-square error propagation in bulk metering, and utility performance indicator benchmarks.
                </p>
            </div>
            <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                <a href="https://www.worldbank.org/en/topic/water" target="_blank" rel="noopener noreferrer" style="background: #0284c7; color: #ffffff; text-decoration: none; padding: 7px 14px; border-radius: 6px; font-size: 12px; font-weight: 600; display: inline-flex; align-items: center; gap: 4px;">
                    🌐 World Bank Water ↗
                </a>
                <a href="https://www.google.com/search?q=World+Bank+reducing+non+revenue+water+NRW+guidelines" target="_blank" rel="noopener noreferrer" style="background: #f1f5f9; color: #334155; border: 1px solid #cbd5e1; text-decoration: none; padding: 7px 14px; border-radius: 6px; font-size: 12px; font-weight: 600; display: inline-flex; align-items: center; gap: 4px;">
                    🔍 Google Search ↗
                </a>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Card 4: US Department of Energy (DOE)
        st.markdown("""
        <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 22px 24px; box-shadow: 0 2px 6px rgba(0,0,0,0.04); margin-bottom: 20px; height: 100%; display: flex; flex-direction: column; justify-content: space-between;">
            <div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span style="background: #fef3c7; color: #b45309; font-size: 11px; font-weight: 700; padding: 3px 10px; border-radius: 12px; text-transform: uppercase; letter-spacing: 0.05em;">Energy & Technology Policy</span>
                    <span style="font-size: 12px; color: #64748b;">US Department of Energy</span>
                </div>
                <h4 style="color: #0f172a; margin: 0 0 8px 0; font-size: 16px; font-weight: 700; line-height: 1.4;">
                    Energy-Water Nexus: Smart Water Infrastructure and Advanced Sensor Technologies
                </h4>
                <p style="color: #475569; font-size: 13px; line-height: 1.5; margin-bottom: 16px;">
                    DOE strategic roadmap exploring edge telemetry microcontrollers, wireless IoT sensor networks, hydraulic friction optimization, and energy-conserving pumping schedules across municipal water grids.
                </p>
            </div>
            <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                <a href="https://www.energy.gov/policy/energy-water-nexus" target="_blank" rel="noopener noreferrer" style="background: #0284c7; color: #ffffff; text-decoration: none; padding: 7px 14px; border-radius: 6px; font-size: 12px; font-weight: 600; display: inline-flex; align-items: center; gap: 4px;">
                    ⚡ DOE Energy-Water Nexus ↗
                </a>
                <a href="https://www.google.com/search?q=US+Department+of+Energy+Energy+Water+Nexus+smart+sensor+infrastructure" target="_blank" rel="noopener noreferrer" style="background: #f1f5f9; color: #334155; border: 1px solid #cbd5e1; text-decoration: none; padding: 7px 14px; border-radius: 6px; font-size: 12px; font-weight: 600; display: inline-flex; align-items: center; gap: 4px;">
                    🔍 Google Search ↗
                </a>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Image Attribution & Licensing Registry Table
    with st.expander("📷 Image Attribution, Visual Asset Registry & Licensing Information", expanded=False):
        st.markdown("""
| Slide / Context | Local Asset Filename | Covered Technical Topic | Attribution / Visual Credit | License Terms |
|---|---|---|---|---|
| **Slide 1** | `assets/slides/slide1_water_network.jpg` | Water resources, dam impoundment, WTP & 3D transmission network | WaterGuard AI Engineering Asset (Digital Twin Photorealistic Render) | CC BY-NC 4.0 / Educational Open Use |
| **Slide 2** | `assets/slides/slide2_leak_detection.jpg` | Pipeline leak breach, acoustic hiss & pressure differential | WaterGuard AI Engineering Asset (Digital Twin Photorealistic Render) | CC BY-NC 4.0 / Educational Open Use |
| **Slide 3** | `assets/slides/slide3_risk_intelligence.jpg` | Explainable risk scoring, AI anomaly detection & deterioration | WaterGuard AI Engineering Asset (Digital Twin Photorealistic Render) | CC BY-NC 4.0 / Educational Open Use |
| **Slide 4** | `assets/slides/slide4_water_balance.jpg` | Volumetric water-loss analysis & flow balancing telemetry | WaterGuard AI Engineering Asset (Digital Twin Photorealistic Render) | CC BY-NC 4.0 / Educational Open Use |
| **Slide 5** | `assets/slides/slide5_predictive_maint.jpg` | Predictive maintenance, non-destructive testing & work orders | WaterGuard AI Engineering Asset (Digital Twin Photorealistic Render) | CC BY-NC 4.0 / Educational Open Use |
| **Slide 6** | `assets/slides/slide6_esp32_iot.jpg` | Sensor telemetry, ESP32 IoT node & 4-20mA hardware integration | WaterGuard AI Engineering Asset (Digital Twin Photorealistic Render) | CC BY-NC 4.0 / Educational Open Use |
| **Bibliography** | `assets/slides/references_library.jpg` | Technical bibliography, regulatory archives & global water data | WaterGuard AI Engineering Asset (Digital Twin Photorealistic Render) | CC BY-NC 4.0 / Educational Open Use |

*Note: All technical visualizations have been generated and calibrated specifically for the WaterGuard AI Educational and Research prototype.*
        """)
