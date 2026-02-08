import streamlit as st
import pandas as pd
import numpy as np
import json
import os
import sys
import plotly.express as px
import plotly.graph_objects as go
try:
    import hdbscan
    import umap
    import sklearn.preprocessing
except ImportError:
    st.error("Missing required libraries. Please run: pip install hdbscan umap-learn scikit-learn")
    st.stop()

# Set page configuration
st.set_page_config(
    page_title="NewsPilot Cluster Dashboard",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .reportview-container {
        background: #f0f2f6;
    }
    .news-card {
        background-color: white;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 10px;
        border-left: 4px solid #0078d4;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        transition: transform 0.2s;
    }
    .news-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .news-time {
        color: #666;
        font-size: 0.8rem;
        margin-bottom: 5px;
        font-weight: 500;
    }
    .news-title {
        color: #333;
        font-size: 1rem;
        font-weight: 700;
        margin-bottom: 8px;
        line-height: 1.4;
    }
    .news-abstract {
        color: #555;
        font-size: 0.9rem;
        line-height: 1.5;
    }
    .stButton>button {
        width: 100%;
    }
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(current_dir, "refined_news_data.json")
    
    if not os.path.exists(input_file):
        return None
        
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    df = pd.DataFrame(data)
    
    # Process timestamps - handle mixed formats
    try:
        df["published_at"] = pd.to_datetime(df["published_at"], format='mixed')
    except ValueError:
        df["published_at"] = pd.to_datetime(df["published_at"], errors='coerce')

    # Filter valid embeddings
    if 'embedding' in df.columns:
        df = df[df['embedding'].apply(lambda x: isinstance(x, list) and len(x) > 0)]
    
    return df

@st.cache_data
def perform_clustering(df, min_cluster_size, min_samples, n_neighbors):
    if len(df) == 0:
        return df, None
    
    # 1. Prepare Features
    X = np.vstack(df["embedding"].values)
    # Normalize for Cosine/Euclidean equivalence
    X = sklearn.preprocessing.normalize(X)
    
    # 2. HDBSCAN Clustering
    clusterer = hdbscan.HDBSCAN(
        metric="euclidean", 
        min_cluster_size=min_cluster_size,
        min_samples=min_samples
    )
    cluster_labels = clusterer.fit_predict(X)
    
    # 3. UMAP Projection
    # Ensure n_neighbors is valid
    effective_n_neighbors = min(n_neighbors, len(df) - 1)
    if effective_n_neighbors < 2: 
        effective_n_neighbors = 2
        
    reducer = umap.UMAP(
        n_neighbors=effective_n_neighbors,
        min_dist=0.1,
        metric="cosine",
        random_state=42
    )
    embedding_2d = reducer.fit_transform(X)
    
    # Update DataFrame
    df["cluster_id"] = cluster_labels
    df["x"] = embedding_2d[:, 0]
    df["y"] = embedding_2d[:, 1]
    
    return df

def main():
    # --- Sidebar Controls ---
    st.sidebar.title("🔧 Configuration")
    
    st.sidebar.subheader("Clustering Parameters")
    min_cluster_size = st.sidebar.slider("Min Cluster Size", 2, 50, 5)
    min_samples = st.sidebar.slider("Min Samples", 1, 20, 3)
    n_neighbors = st.sidebar.slider("UMAP Neighbors", 2, 50, 15)
    
    st.sidebar.divider()
    
    if st.sidebar.button("Reload Data & Re-Cluster"):
        st.cache_data.clear()
        st.rerun()

    # --- Load & Process Data ---
    with st.spinner("Loading and processing data..."):
        raw_df = load_data()
        if raw_df is None:
            st.error("Data file `refined_news_data.json` not found. Please run `export_refined_news.py` first.")
            st.stop()
            
        df = perform_clustering(raw_df, min_cluster_size, min_samples, n_neighbors)

    # --- Main Content ---
    st.title("NewsPilot Event Map")
    
    # Stats row
    n_clusters = len(set(df["cluster_id"])) - (1 if -1 in df["cluster_id"].values else 0)
    n_noise = (df["cluster_id"] == -1).sum()
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Total News", len(df))
    c2.metric("Identified Events", n_clusters)
    c3.metric("Unclustered (Noise)", n_noise)

    # --- Layout: Chart (Left) + Details (Right) ---
    col_chart, col_details = st.columns([1.6, 1])

    with col_chart:
        # Construct Hover Text
        df['time_str'] = df['published_at'].dt.strftime('%Y-%m-%d %H:%M')
        df['hover_label'] = df.apply(
            lambda row: f"<b>Event {row['cluster_id'] if row['cluster_id']!=-1 else 'Noise'}</b><br>{row['time_str']}<br>{row['title'][:50]}...", 
            axis=1
        )
        
        # Color Map handling to ensure Noise (-1) is distinct
        df['Cluster Label'] = df['cluster_id'].apply(lambda x: f"Event {x}" if x != -1 else "Noise")
        
        fig = px.scatter(
            df, 
            x="x", 
            y="y", 
            color="Cluster Label",
            hover_name="title",
            custom_data=["cluster_id", "title", "time_str", "abstract"],
            height=700,
            template="plotly_white",
            title="Interactive Event Map (Click to Inspect)"
        )
        
        fig.update_traces(
            marker=dict(size=8, opacity=0.7, line=dict(width=0.5, color='DarkSlateGrey')),
            hovertemplate="<b>%{customdata[1]}</b><br>%{customdata[2]}<br>Event: %{customdata[0]}<extra></extra>"
        )
        
        fig.update_layout(
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, title=''),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, title=''),
            margin=dict(l=0, r=0, t=30, b=0)
        )

        # Streamlit Plotly Chart
        # selection_mode="points" is available in newer streamlit versions
        # We can use it to drive the detail view
        try:
            event = st.plotly_chart(fig, use_container_width=True, on_select="rerun", selection_mode="points")
        except TypeError:
             # Fallback for older streamlit versions
            st.warning("Please upgrade Streamlit (`pip install --upgrade streamlit`) to enable click interactions.")
            event = st.plotly_chart(fig, use_container_width=True)

    with col_details:
        st.subheader("Event Details")
        
        # Determine current selection
        selected_cluster = None
        selected_points_indices = []
        
        # Check if user clicked points on chart
        if 'selection' in event and event['selection']['points']:
            # Get indices of selected points
            selected_points_indices = [p['point_index'] for p in event['selection']['points']]
            # Infer cluster from the first selected point (assuming usually people select a cluster area)
            if selected_points_indices:
                first_idx = selected_points_indices[0]
                selected_cluster = df.iloc[first_idx]['cluster_id']
                
        # Alternative Selection via Dropdown
        cluster_options = sorted(list(df['cluster_id'].unique()))
        # Move -1 to end or beginning
        if -1 in cluster_options:
            cluster_options.remove(-1)
            cluster_options = cluster_options + [-1]
            
        cluster_labels_map = {c: ("Unclustered News" if c == -1 else f"Event {c}") for c in cluster_options}
        
        # Sync dropdown if cluster selected from chart
        default_idx = 0
        if selected_cluster is not None:
             if selected_cluster in cluster_options:
                 default_idx = cluster_options.index(selected_cluster)
        
        selected_cluster_id = st.selectbox(
            "Select Event/Cluster:", 
            options=cluster_options,
            format_func=lambda x: cluster_labels_map[x],
            index=default_idx,
            key="cluster_selector"
        )
        
        # Search Box
        search_query = st.text_input("🔍 Search within list", "", placeholder="Type keywords...")

        # Filter Data
        filtered_df = df[df['cluster_id'] == selected_cluster_id].sort_values('published_at')

        if search_query:
            filtered_df = filtered_df[
                filtered_df['title'].str.contains(search_query, case=False, na=False) | 
                filtered_df['abstract'].str.contains(search_query, case=False, na=False)
            ]

        # Display Stats
        st.markdown(f"**Items found:** {len(filtered_df)}")
        if not filtered_df.empty:
            start_t = filtered_df['published_at'].iloc[0].strftime('%Y-%m-%d %H:%M')
            end_t = filtered_df['published_at'].iloc[-1].strftime('%Y-%m-%d %H:%M')
            st.caption(f"Time Range: {start_t} → {end_t}")

        # Render List (Scrollable container needed? Streamlit handles scrolling naturally)
        st.divider()
        
        if filtered_df.empty:
            st.info("No news items match your criteria.")
        else:
            # Custom rendering for Card View
            for idx, row in filtered_df.iterrows():
                with st.container():
                    st.markdown(f"""
                    <div class="news-card">
                        <div class="news-time">{row['time_str']}</div>
                        <div class="news-title">{row['title']}</div>
                        <div class="news-abstract">{row['abstract'][:200] + '...' if row['abstract'] and len(row['abstract']) > 200 else row.get('abstract', '')}</div>
                    </div>
                    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
