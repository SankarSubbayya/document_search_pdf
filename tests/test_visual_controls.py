#!/usr/bin/env python3
"""
Test script to verify the new visual controls in the Streamlit apps.
This demonstrates the knob-style controls for threshold and document count.
"""

import streamlit as st

st.set_page_config(
    page_title="Visual Controls Demo",
    page_icon="🎛️",
    layout="wide"
)

st.title("🎛️ Visual Search Controls Demo")
st.markdown("This demonstrates the new knob-style controls for search settings.")

# Create the control panel
st.markdown("### 🎚️ Interactive Search Controls")

# Main controls in columns
col1, col2, col3 = st.columns([1.5, 1.5, 2])

with col1:
    st.markdown("#### 📊 Number of Documents")
    # Select slider for discrete values - more like a knob
    doc_count = st.select_slider(
        "Select number of documents",
        options=[1, 3, 5, 10, 15, 20, 25, 30, 40, 50],
        value=10,
        label_visibility="collapsed"
    )

    # Visual feedback with gradient
    st.markdown(f"""
    <div style='text-align: center; padding: 15px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 15px; color: white; font-size: 1.8em;
                font-weight: bold; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
        📚 {doc_count} Docs
    </div>
    """, unsafe_allow_html=True)

    # Progress bar to show relative value
    st.progress(doc_count / 50)

with col2:
    st.markdown("#### 🎯 Similarity Threshold")
    # Continuous slider for threshold
    threshold = st.slider(
        "Set minimum similarity",
        min_value=0.0,
        max_value=1.0,
        value=0.3,
        step=0.05,
        format="%.2f",
        label_visibility="collapsed"
    )

    # Color-coded visual feedback
    if threshold == 0:
        text = "All Results"
        bg_color = "linear-gradient(135deg, #11998e 0%, #38ef7d 100%)"
        emoji = "🟢"
    elif threshold < 0.5:
        text = f"{threshold:.0%} Minimum"
        bg_color = "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)"
        emoji = "🟡"
    else:
        text = f"{threshold:.0%} Minimum"
        bg_color = "linear-gradient(135deg, #fa709a 0%, #fee140 100%)"
        emoji = "🔴"

    st.markdown(f"""
    <div style='text-align: center; padding: 15px;
                background: {bg_color};
                border-radius: 15px; color: white; font-size: 1.8em;
                font-weight: bold; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
        {emoji} {text}
    </div>
    """, unsafe_allow_html=True)

    # Visual threshold meter
    st.progress(threshold)

with col3:
    st.markdown("#### ⚙️ Search Mode")

    # Radio buttons styled as toggle
    mode = st.radio(
        "Search precision",
        ["⚡ Fast Mode", "🎯 Exact Mode"],
        horizontal=True,
        label_visibility="collapsed"
    )

    if "Fast" in mode:
        mode_desc = "Approximate search - Quick results"
        mode_color = "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
        speed = "~50ms"
        accuracy = "95%"
    else:
        mode_desc = "Exact search - Maximum precision"
        mode_color = "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)"
        speed = "~200ms"
        accuracy = "100%"

    st.markdown(f"""
    <div style='padding: 10px; background: {mode_color};
                border-radius: 10px; color: white; text-align: center;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
        <div style='font-size: 1.2em; font-weight: bold;'>{mode}</div>
        <div style='font-size: 0.9em; margin-top: 5px;'>{mode_desc}</div>
        <div style='display: flex; justify-content: space-around; margin-top: 10px;'>
            <span>⏱️ {speed}</span>
            <span>🎯 {accuracy}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# Show current settings summary
st.markdown("### 📋 Current Search Configuration")

config_col1, config_col2, config_col3, config_col4 = st.columns(4)

with config_col1:
    st.metric("Documents", doc_count, f"{doc_count/50:.0%} of max")

with config_col2:
    st.metric("Threshold", f"{threshold:.2f}", f"Top {(1-threshold)*100:.0f}%")

with config_col3:
    st.metric("Mode", mode.split()[1], speed)

with config_col4:
    estimated_time = doc_count * (50 if "Fast" in mode else 200) / 1000
    st.metric("Est. Time", f"{estimated_time:.1f}s", accuracy)

st.divider()

# Example query box
st.markdown("### 🔍 Try a Search")
query = st.text_input("Enter search query", placeholder="machine learning transformers...")

if st.button("🚀 Search with These Settings", type="primary", use_container_width=True):
    with st.spinner(f"Searching for '{query}' with your settings..."):
        st.success(f"""
        ✅ Search configured with:
        - Returning top {doc_count} documents
        - Minimum similarity: {threshold:.0%}
        - Mode: {mode}
        """)

# Instructions
with st.expander("ℹ️ How to Use These Controls"):
    st.markdown("""
    ### Visual Search Controls Guide

    **📊 Number of Documents**
    - Use the select slider to choose how many results to return
    - Visual indicator shows your selection with gradient background
    - Progress bar shows relative to maximum (50 docs)

    **🎯 Similarity Threshold**
    - Slide to set minimum relevance score (0.0 - 1.0)
    - Color changes based on strictness:
      - 🟢 Green (0.0): Show all results
      - 🟡 Yellow (0.1-0.5): Moderate filtering
      - 🔴 Red (>0.5): Strict filtering
    - Progress bar shows threshold level

    **⚙️ Search Mode**
    - Fast Mode: Quick approximate search (95% accuracy)
    - Exact Mode: Slower but 100% accurate
    - Visual indicator shows speed/accuracy tradeoffs

    ### Integration
    These controls are now integrated into:
    1. **PDF Manager App**: In the main search interface
    2. **Upload App**: In the sidebar

    Run the apps with:
    ```bash
    uv run streamlit run apps/pdf_manager_app.py
    uv run streamlit run apps/streamlit_upload_app.py
    ```
    """)

if __name__ == "__main__":
    st.sidebar.success("🎛️ Visual Controls Demo")
    st.sidebar.info("This demo shows the new knob-style search controls")