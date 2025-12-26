import streamlit as st
import graphviz
import json
from core.crawler import crawl_website
from core.agent1 import analyze_docs
from core.database import init_db, save_result, fetch_logs

# Must be the first streamlt command
st.set_page_config(page_title="Pulse | Module Extractor", layout="wide")

# Ensure DB is ready on app startup
init_db()

# --- Custom Styling ---
st.markdown("""
<style>
    .main-title { font-size: 3rem; color: #2E7D32; font-weight: 700; }
    .stButton>button { width: 100%; border-radius: 5px; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🧬 PULSE AGENT</div>', unsafe_allow_html=True)
st.caption("Automated Documentation Mapper & Hierarchy Extractor")

# --- Helper to match the strict Assignment PDF format ---
def convert_to_strict_format(modules_list):
    """
    The assignment requires a dictionary for submodules and Capitalized Keys.
    This function handles that transformation.
    """
    final_output = []
    for m in modules_list:
        # Convert List -> Dict mapping
        subs = {sub.name: sub.description for sub in m.submodules}
        
        final_output.append({
            "module": m.module_name,
            "Description": m.description,
            "Submodules": subs,
            "Confidence": f"{m.confidence_score}%"  # Added bonus feature
        })
    return final_output

# --- Sidebar: History Log ---
with st.sidebar:
    st.header("📜 Past Extractions")
    if st.button("Reload History"):
        logs = fetch_logs()
        for url, date, _ in logs:
            st.text(f"[{date}] {url}")

# --- Main UI ---
col1, col2 = st.columns([2, 1])

with col1:
    target_urls = st.text_area("Enter Documentation URL(s)", height=150, placeholder="https://docs.python.org/3/\nhttps://fastapi.tiangolo.com/")

with col2:
    st.write("### Configuration")
    page_limit = st.slider("Depth Limit (Pages)", 1, 10, 3)
    st.info("💡 Tip: Lower depth is faster for demos.")

if st.button("🚀 Run Extraction Agent", type="primary"):
    # Split by newline and remove empty strings
    urls = [u.strip() for u in target_urls.split('\n') if u.strip()]
    
    if not urls:
        st.warning("Please enter at least one URL.")
    else:
        for url in urls:
            st.divider()
            st.subheader(f"Analyzing: `{url}`")
            
            # Step 1: Crawl
            with st.spinner(f"Crawling {url} (Max {page_limit} pages)..."):
                raw_data = crawl_website(url, page_limit)
            
            if not raw_data:
                st.error("Could not crawl this URL. Check if it's valid or blocking bots.")
                continue
                
            # Step 2: AI Analysis
            with st.spinner("AI Agent is constructing the hierarchy..."):
                combined_text = "\n".join(raw_data)
                result = analyze_docs(combined_text)
            
            if result:
                # Save to DB for persistence
                save_result(url, result.modules)
                st.success("Extraction Complete!")
                
                # --- Visualization Section ---
                tab1, tab2 = st.tabs(["📊 Visual Graph", "💾 JSON Output"])
                
                with tab1:
                    # Draw the graph using Graphviz
                    g = graphviz.Digraph()
                    g.attr(rankdir='LR')
                    
                    for mod in result.modules:
                        g.node(mod.module_name, shape='box', style='filled', fillcolor='#c8e6c9')
                        for sub in mod.submodules:
                            g.edge(mod.module_name, sub.name)
                            
                    st.graphviz_chart(g)
                
                with tab2:
                    # Convert to strict PDF format
                    formatted_json = convert_to_strict_format(result.modules)
                    st.json(formatted_json)
            else:
                st.error("AI failed to extract structure. Try again.")