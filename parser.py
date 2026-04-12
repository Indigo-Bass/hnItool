import json
import html
import re
import os
from datetime import datetime

def clean_text(raw_html):
    """Strips HTML and unescapes entities for clean LLM ingestion."""
    if not raw_html:
        return ""
    text = html.unescape(raw_html)
    text = re.sub(r'<[^>]+>', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()

def build_thread_context(item_id, raw_data, depth=0, max_items=55, current_count=None):
    """
    Recursively builds a formatted text representation of the comment tree.
    Preserves hierarchy via indentation so the LLM understands the exact reply chain.
    """
    if current_count is None:
        current_count = [0]

    item_id_str = str(item_id)
    if item_id_str not in raw_data or current_count[0] >= max_items:
        return ""

    item = raw_data[item_id_str]
    
    # Noise Filter: Discard dead or deleted items
    if item.get('deleted') or item.get('dead'):
        return ""

    result = ""
    # Use indentation to visually represent thread depth for the LLM
    indent = "  " * depth 
    
    if item.get('type') == 'comment':
        author = item.get('by', 'anonymous')
        # Format timestamp to human-readable string
        time_str = datetime.utcfromtimestamp(item.get('time', 0)).strftime('%Y-%m-%d %H:%M')
        text = clean_text(item.get('text', ''))
        
        if text:
            result += f"{indent}- [{author} at {time_str}]: {text}\n"
            current_count[0] += 1
            
    # Recursive Step: Process 'kids' array (replies)
    if 'kids' in item and current_count[0] < max_items:
        for kid_id in item['kids']:
            result += build_thread_context(kid_id, raw_data, depth + 1, max_items, current_count)
            if current_count[0] >= max_items:
                break # Stop processing if we hit our token/item cap
                
    return result

if __name__ == "__main__":
    input_path = 'data/raw_hn_data.json'
    
    # We output to structured_chunks.json to match digest.py's input path
    output_path = 'data/structured_chunks.json' 
    
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: {input_path} not found. Please run fetcher.py first.")
        exit(1)
        
    final_dataset = []
    
    # Find all root stories in our local datastore
    stories = [item for item in raw_data.values() if item.get('type') == 'story']
    
    for story in stories:
        story_id = story.get('id')
        story_title = story.get('title', 'Unknown Title')
        print(f"Structuring tree for story: {story_title} (ID: {story_id})...")
        
        # Build the hierarchical text representation
        thread_text = f"STORY: {story_title}\n"
        current_count = [0]
        thread_text += build_thread_context(story_id, raw_data, depth=0, max_items=55, current_count=current_count)
        
        chunk = {
            "story_id": story_id,
            "story_title": story_title,
            "comments_retained": current_count[0],
            # Use 'thread_context' to fix the KeyError in digest.py
            "thread_context": thread_text 
        }
        final_dataset.append(chunk)

    # Save the optimized structure
    os.makedirs('data', exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_dataset, f, indent=2)

    print(f"\nArchitecture execution complete. Processed {len(stories)} stories.")
    for data in final_dataset:
        print(f"[{data['story_title']}] -> Comments Retained in Context: {data['comments_retained']}")