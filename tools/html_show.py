"""
News Event Clustering → Interactive HTML Report

输出:
- news_cluster_report.html
"""

import json
import os
import sys
import numpy as np
import pandas as pd
import sklearn.preprocessing
import hdbscan
import umap
import plotly.express as px
import plotly.io as pio



# =========================
# 1. 数据准备
# =========================

def load_data():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(current_dir, "refined_news_data.json")
    
    if not os.path.exists(input_file):
        print(f"File not found: {input_file}")
        print("Please run export_refined_news.py first.")
        sys.exit(1)
        
    print(f"Loading data from {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

news_items = load_data()
df = pd.DataFrame(news_items)

# Data validation
if 'embedding' not in df.columns:
    print("Error: Data file does not contain 'embedding' field.")
    sys.exit(1)

# Filter out rows with missing or empty embeddings
df = df[df['embedding'].apply(lambda x: isinstance(x, list) and len(x) > 0)]

if len(df) == 0:
    print("No valid embeddings found in data.")
    sys.exit(1)

X = np.vstack(df["embedding"].values)
# Normalize embeddings to unit length so Euclidean distance is equivalent to Cosine distance
X = sklearn.preprocessing.normalize(X)

# Use format='mixed' to handle ISO8601 with/without microseconds/timezones automatically
try:
    df["published_at"] = pd.to_datetime(df["published_at"], format='mixed')
except ValueError:
    # Fallback if format='mixed' is not supported or fails, try generic parsing
    df["published_at"] = pd.to_datetime(df["published_at"])

print(f"Loaded {len(df)} news items")
print(f"Embedding shape: {X.shape}")


# =========================
# 2. HDBSCAN 聚类
# =========================

clusterer = hdbscan.HDBSCAN(
    metric="euclidean",
    min_cluster_size=5,
    min_samples=3
)

df["cluster_id"] = clusterer.fit_predict(X)

num_clusters = len(set(df["cluster_id"])) - (1 if -1 in df["cluster_id"].values else 0)
num_noise = (df["cluster_id"] == -1).sum()

print(f"Detected clusters: {num_clusters}")
print(f"Noise points: {num_noise}")


# =========================
# 3. UMAP 降维（仅用于展示）
# =========================

reducer = umap.UMAP(
    n_neighbors=15,
    min_dist=0.1,
    metric="cosine",
    random_state=42
)

X_2d = reducer.fit_transform(X)
df["x"] = X_2d[:, 0]
df["y"] = X_2d[:, 1]


# =========================
# 4. 为 hover 构造「事件级描述」以及 Side Panel 详情
# =========================

event_summaries = {}
cluster_details = {} # Store full timeline HTML for each cluster

for cid in df["cluster_id"].unique():
    group = df[df["cluster_id"] == cid].sort_values("published_at")
    
    # Common formats
    start_time = group['published_at'].iloc[0].strftime('%Y-%m-%d %H:%M')
    end_time = group['published_at'].iloc[-1].strftime('%Y-%m-%d %H:%M')
    
    # --- 1. Construct Full Sidebar Detail HTML ---
    is_noise = (cid == -1)
    title_str = "Unclustered News (Noise)" if is_noise else f"Event {cid}"
    
    # Header for the content within the scrollable area
    detail_html = (
        f"<div class='cluster-header'>"
        f"<div class='cluster-title'>{title_str}</div>"
        f"<div class='cluster-meta'>"
        f"<span class='cluster-tag'>{len(group)} Items</span>"
        f"<span>{start_time} → {end_time}</span>"
        f"</div></div>"
        f"<div class='news-list'>"
    )
    
    # Limit noise items if too many to prevent browser lag (optional, but good practice)
    # Showing all for now as requested "complete list", but adding a warning caption if huge
    
    for _, row in group.iterrows():
        row_time = row['published_at'].strftime('%m-%d %H:%M')
        row_title = row.get('title', 'No Title')
        row_abstract = str(row.get('abstract', ''))
        
        detail_html += (
            f"<div class='news-item'>"
            f"<div class='news-time'>{row_time}</div>"
            f"<div class='news-title'>{row_title}</div>"
        )
        if row_abstract and len(row_abstract) > 5:
             # truncate for initial view but show full on title hover
             abs_short = (row_abstract[:150] + '...') if len(row_abstract) > 150 else row_abstract
             detail_html += f"<div class='news-abstract' title='{row_abstract}'>{abs_short}</div>"
        
        detail_html += "</div>"
    
    detail_html += "</div>"
    cluster_details[str(cid)] = detail_html

    # --- 2. Construct Hover Tooltip (Summary) ---
    if is_noise:
        continue # handled in build_hover individually

    # Force font-family in HTML to avoid encoding/font issues on Windows
    summary = (
        f"<div style='max-width:400px; font-family: \"Microsoft YaHei\", \"SimHei\", Arial, sans-serif;'>"
        f"<b style='font-size:1.1em;'>Event {cid}</b> | <span style='font-size:0.9em; color:#555'>Click for details</span><br>"
        f"Size: {len(group)} items<br>"
        f"Period: {start_time} <br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;→ {end_time}<br>"
        f"<hr style='margin:8px 0; border:0; border-top:1px solid #ddd;'>"
        f"<b>Top Stories:</b><br>"
    )

    for _, row in group.head(5).iterrows():
        title = row.get('title', 'No Title')
        abstract = str(row.get('abstract', ''))
        # 截断摘要以优化显示
        disp_abstract = (abstract[:150] + "...") if len(abstract) > 150 else abstract
        
        # Precise timestamp for each item
        item_time = row['published_at'].strftime('%m-%d %H:%M')
        
        summary += (
            f"<div style='margin-bottom:8px;'>"
            f"<b>[{item_time}] {title}</b><br>"
        )
        if disp_abstract:
            # 增加摘要显示
            summary += f"<span style='color:#555; font-size:0.9em;'>{disp_abstract}</span>"
        summary += "</div>"

    if len(group) > 5:
        summary += f"<i>... ({len(group)-5} more items)</i>"
    
    summary += "</div>"
    event_summaries[cid] = summary


def build_hover(row):
    if row["cluster_id"] == -1:
        title = row.get('title', 'No Title')
        abstract = str(row.get('abstract', ''))
        disp_abstract = (abstract[:400] + "...") if len(abstract) > 400 else abstract
        
        return (
            f"<div style='max-width:400px; font-family: \"Microsoft YaHei\", \"SimHei\", Arial, sans-serif;'>"
            f"<b style='color:#666;'>Unclustered News</b> | {row['published_at'].strftime('%Y-%m-%d %H:%M')}<br>"
            f"<hr style='margin:5px 0; border:0; border-top:1px solid #ddd;'>"
            f"<b style='font-size:1.1em;'>{title}</b><br><br>"
            f"{disp_abstract}"
            f"</div>"
        )
    return event_summaries.get(row["cluster_id"], "No details")


df["hover"] = df.apply(build_hover, axis=1)


# =========================
# 5. Plotly 交互式可视化
# =========================

fig = px.scatter(
    df,
    x="x",
    y="y",
    color=df["cluster_id"].astype(str),
    hover_data={"hover": True, "x": False, "y": False},
    title="News Event Clustering Report (HDBSCAN + UMAP)",
    labels={"color": "Cluster ID"},
    template="plotly_white"
)

fig.update_traces(
    marker=dict(size=8, opacity=0.7, line=dict(width=0.5, color='DarkSlateGrey')),
    hovertemplate="%{customdata[0]}<extra></extra>",
    customdata=df[['hover', 'cluster_id']].values
)

fig.update_layout(
    margin=dict(l=0, r=0, t=40, b=0), # maximize space
    legend_title_text="Event Cluster",
    legend=dict(
        orientation="v",
        yanchor="top",
        y=1,
        xanchor="right",
        x=1.1
    ),
    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, title=''),
    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, title=''),
    hoverlabel=dict(
        bgcolor="white",
        font_size=13,
        font_family="'Microsoft YaHei', 'SimHei', Arial, sans-serif"
    ),
    font=dict(
        family="'Microsoft YaHei', 'SimHei', Arial, sans-serif"
    )
)

# =========================
# 6. 导出 HTML 报告 (Custom HTML with Sidebar)
# =========================

output_path = r"E:\code\NewsPilot\tools\news_cluster_report.html"

# 1. Get Plotly HTML div
plot_div = pio.to_html(fig, full_html=False, include_plotlyjs='cdn')

# 2. Serialize Data for JS
try:
    cluster_data_json = json.dumps(cluster_details, ensure_ascii=False)
except Exception as e:
    print(f"Error serializing cluster data: {e}")
    cluster_data_json = "{}"

# 3. Build Full HTML Page
html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>News Event Clustering Analysis</title>
    <style>
        body {{ margin: 0; padding: 0; font-family: "Microsoft YaHei", "Segoe UI", sans-serif; height: 100vh; overflow: hidden; display: flex; flex-direction: column; background-color: #f8f9fa; }}
        #header {{ height: 48px; background: #fff; border-bottom: 1px solid #e0e0e0; display: flex; align-items: center; padding: 0 24px; box-shadow: 0 1px 2px rgba(0,0,0,0.03); z-index: 20; }}
        #title {{ font-weight: 700; font-size: 1.25em; color: #1a1a1a; letter-spacing: -0.01em; display: flex; align-items: center; gap: 10px; }}
        #title span {{ color: #0078d4; }}
        #subtitle {{ margin-left: 24px; font-size: 0.9em; color: #666; font-weight: 400; }}
        
        #main-container {{ display: flex; flex: 1; height: calc(100vh - 48px); overflow: hidden; }}
        #chart-container {{ flex: 1; height: 100%; min-width: 0; position: relative; background: white; }}
        
        #side-panel {{ 
            width: 420px; 
            border-left: 1px solid #e5e5e5; 
            background: #fcfcfc; 
            height: 100%; 
            display: flex;
            flex-direction: column;
            box-shadow: -4px 0 20px rgba(0,0,0,0.04);
            z-index: 10;
            transition: transform 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
        }}

        /* Search Bar Area */
        #panel-header {{
            padding: 16px;
            background: #fff;
            border-bottom: 1px solid #eee;
            flex-shrink: 0;
        }}
        
        #search-box {{
            position: relative;
            width: 100%;
        }}
        
        #search-input {{
            width: 100%;
            padding: 10px 12px 10px 36px;
            border: 1px solid #e0e0e0;
            border-radius: 6px;
            font-size: 14px;
            background: #f8f9fa;
            transition: all 0.2s;
            box-sizing: border-box;
            outline: none;
            font-family: inherit;
        }}
        
        #search-input:focus {{
            background: #fff;
            border-color: #0078d4;
            box-shadow: 0 0 0 3px rgba(0,120,212,0.1);
        }}

        #search-icon {{
            position: absolute;
            left: 12px;
            top: 50%;
            transform: translateY(-50%);
            color: #999;
            pointer-events: none;
        }}

        /* Content Area */
        #panel-content {{ 
            flex: 1; 
            overflow-y: auto; 
            padding: 0;
            scroll-behavior: smooth;
        }}
        
        .content-padding {{ padding: 20px; }}

        #empty-state {{ 
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 80%;
            color: #888;
            text-align: center;
            padding: 40px;
        }}
        #empty-state svg {{ color: #e0e0e0; margin-bottom: 20px; width: 64px; height: 64px; }}
        #empty-state p {{ max-width: 240px; line-height: 1.5; }}

        /* Cluster Info Header within content */
        .cluster-header {{
            position: sticky;
            top: 0;
            background: rgba(255,255,255,0.95);
            backdrop-filter: blur(10px);
            padding: 16px 20px;
            border-bottom: 1px solid #eee;
            margin-bottom: 10px;
            z-index: 5;
        }}
        .cluster-title {{ font-size: 1.4em; font-weight: 700; color: #1a1a1a; margin: 0 0 4px 0; }}
        .cluster-meta {{ 
            font-size: 0.85em; 
            color: #666; 
            display: flex; 
            gap: 12px;
            align-items: center;
        }}
        .cluster-tag {{ background: #eff6fc; color: #0078d4; padding: 2px 8px; border-radius: 10px; font-weight: 600; font-size: 0.9em; }}

        /* News List Items */
        .news-list {{ padding: 0 16px 40px 16px; }}
        
        .news-item {{ 
            background: #fff; 
            padding: 14px; 
            margin-bottom: 12px; 
            border-radius: 8px; 
            box-shadow: 0 1px 2px rgba(0,0,0,0.06); 
            border: 1px solid transparent; 
            transition: all 0.2s ease;
            position: relative;
            overflow: hidden;
        }}
        
        .news-item:hover {{ 
            transform: translateY(-2px); 
            box-shadow: 0 4px 12px rgba(0,0,0,0.08); 
            border-color: #e0e0e0;
        }}
        
        .news-item::before {{
            content: '';
            position: absolute;
            left: 0;
            top: 0;
            bottom: 0;
            width: 4px;
            background: #0078d4;
            opacity: 0.7;
        }}

        .news-time {{ 
            color: #666; 
            font-size: 0.75em; 
            font-weight: 500; 
            margin-bottom: 6px; 
            display: flex; 
            align-items: center; 
            gap: 6px; 
        }}
        .news-title {{ 
            font-weight: 600; 
            font-size: 1em; 
            color: #2d2d2d; 
            line-height: 1.45; 
            margin-bottom: 6px;
        }}
        .news-abstract {{ 
            font-size: 0.85em; 
            color: #555; 
            line-height: 1.6; 
            margin-top: 8px;
            padding-top: 8px;
            border-top: 1px dashed #f0f0f0;
        }}
        
        .highlight {{ background-color: #fff3cd; padding: 0 2px; border-radius: 2px; }}

        /* Custom Scrollbar */
        ::-webkit-scrollbar {{ width: 8px; height: 8px; }}
        ::-webkit-scrollbar-track {{ background: transparent; }}
        ::-webkit-scrollbar-thumb {{ background: #d0d0d0; border-radius: 4px; border: 2px solid transparent; background-clip: content-box; }}
        ::-webkit-scrollbar-thumb:hover {{ background: #999; border: 2px solid transparent; background-clip: content-box; }}
    </style>
</head>
<body>
    <div id="header">
        <div id="title">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color:#0078d4">
                <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
                <polyline points="7.5 4.21 12 6.81 16.5 4.21"></polyline>
                <polyline points="7.5 19.79 7.5 14.6 3 12"></polyline>
                <polyline points="21 12 16.5 14.6 16.5 19.79"></polyline>
                <polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline>
                <line x1="12" y1="22.08" x2="12" y2="12"></line>
            </svg>
            NewsPilot <span>Cluster Map</span>
        </div>
        <div id="subtitle">Explore thematic events and narrative clusters</div>
    </div>
    
    <div id="main-container">
        <div id="chart-container">
            {plot_div}
        </div>
        <div id="side-panel">
            <div id="panel-header">
                <div id="search-box">
                    <div id="search-icon">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <circle cx="11" cy="11" r="8"></circle>
                            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                        </svg>
                    </div>
                    <input type="text" id="search-input" placeholder="Filter news in list..." disabled>
                </div>
            </div>
            <div id="panel-content">
                <div id="empty-state">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                    </svg>
                    <p style="font-weight:500; color:#333; margin-bottom:8px;">No Event Selected</p>
                    <p style="font-size:0.9em;">Click on any dot in the scatter plot to reveal the detailed news timeline for that cluster.</p>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        var clusterData = {cluster_data_json};
        var currentClusterId = null;
        var searchInput = document.getElementById('search-input');
        var panelContent = document.getElementById('panel-content');
        
        // Search functionality
        searchInput.addEventListener('input', function(e) {{
            var filter = e.target.value.toLowerCase().trim();
            var items = document.querySelectorAll('.news-item');
            var visibleCount = 0;
            
            items.forEach(function(item) {{
                var title = item.querySelector('.news-title').innerText.toLowerCase();
                var abstract = item.querySelector('.news-abstract') ? item.querySelector('.news-abstract').innerText.toLowerCase() : '';
                
                if(title.includes(filter) || abstract.includes(filter)) {{
                    item.style.display = "";
                    visibleCount++;
                }} else {{
                    item.style.display = "none";
                }}
            }});
        }});

        document.addEventListener('DOMContentLoaded', function() {{
            var graphDiv = document.querySelector('.plotly-graph-div');
            
            if (graphDiv) {{
                graphDiv.on('plotly_click', function(data){{
                    if(data.points && data.points.length > 0){{
                        var point = data.points[0];
                        if (point.customdata && point.customdata.length >= 2) {{
                            var clusterId = point.customdata[1];
                            currentClusterId = clusterId;
                            
                            // Reset search
                            searchInput.value = '';
                            searchInput.disabled = false;
                            
                            // Update content
                            if(clusterData.hasOwnProperty(clusterId)){{
                                panelContent.innerHTML = clusterData[clusterId];
                                panelContent.scrollTop = 0;
                                searchInput.focus();
                            }} else {{
                                panelContent.innerHTML = '<div class="content-padding">No data available for this cluster.</div>';
                            }}
                        }}
                    }}
                }});
                
                // Clear selection on double click background (optional, plotly doesn't trigger easily on bg double click for custom events)
            }}
        }});
    </script>
</body>
</html>
"""

print(f"Writing report to {output_path}...")
with open(output_path, "w", encoding="utf-8") as f:
    f.write(html_content)

print("Done. Opening report...")
try:
    if sys.platform == 'win32':
        os.startfile(output_path)
    else:
        import subprocess
        subprocess.call(['xdg-open', output_path])
except:
    pass

print(f"HTML report saved to: {output_path}")
