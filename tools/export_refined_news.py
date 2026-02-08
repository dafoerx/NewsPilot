import json
import os
import sys
from datetime import datetime

# Add project root to path so we can import src modules
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from src.storage.db_config import DatabaseManager
from src.storage.models import RefinedNews

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def export_refined_news():
    db_manager = DatabaseManager()
    session = db_manager.get_session()

    try:
        print("Querying RefinedNews table...")
        results = session.query(RefinedNews).all()
        
        data = []
        for row in results:
            item = {
                "unique_id": row.unique_id,
                "title": row.title,
                "abstract": row.abstract,
                "source_channel": row.source_channel,
                "published_at": row.published_at,
                "categories": row.categories,
                "embedding": row.embedding,
                "evaluation_score": row.evaluation_score
            }
            data.append(item)
        
        output_file = os.path.join(current_dir, "refined_news_data.json")
        print(f"Exporting {len(data)} records to {output_file}...")
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, default=json_serial, ensure_ascii=False, indent=2)
            
        print("Export completed successfully.")
        
    except Exception as e:
        print(f"Error extracting data: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    export_refined_news()
