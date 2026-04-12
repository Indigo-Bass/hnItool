import json
import os
import re
import html
from datetime import datetime

def clean_html(raw_html):
    """Removes HTML tags and unescapes HTML entities."""
    if not raw_html:
        return ""
    # Unescape entities like &gt; to >
    text = html.unescape(raw_html)
    # Remove HTML tags using regex
    text = re.sub(r'<[^>]+>', ' ', text)
    # Clean up extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def format_timestamp(unix_time):
    """Converts Unix timestamp to readable string."""
    if not unix_time:
        return "Unknown Time"
    return datetime.fromtimestamp(unix_time).strftime('%Y-%m-%d %H:%M:%S')

def build_thread_context(item_id, raw_data, depth=0):
    """
    Recursively builds a formatted text string for a comment and all its replies (DFS).
    """
    item = raw_data.get(str(item_id))
    if not item:
        return ""

    # Skip deleted or dead comments
    if item.get('deleted') or item.get('dead'):
        return ""

    text_block = ""
    
    # Only process if it's a comment with text
    if item.get('type') == 'comment' and 'text' in item:
        author = item.get('by', 'anonymous')
        time_str = format_timestamp(item.get('time'))
        cleaned_text = clean_html(item['text'])
        
        # Create visual hierarchy for the LLM using indentation and explicit depth markers
        indent = "  " * depth
        text_block += f"\n{indent}--- [Depth: {depth} | User: {author} | Time: {time_str}] ---\n"
        text_block += f"{indent}{cleaned_text}\n"

    # Recursively fetch children (kids)
    if 'kids' in item:
        for kid_id in item['kids']:
            text_block += build_thread_context(kid_id, raw_data, depth + 1)
            
    return text_block

if __name__ == "__main__":
    input_path = 'data/raw_hn_data.json'
    output_path = 'data/structured_chunks.json'
    
    with open(input_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    # Find the root stories (items that are of type 'story')
    stories = [item for item in raw_data.values() if item.get('type') == 'story']
    
    structured_dataset = []

    for story in stories:
        story_id = story['id']
        title = story.get('title', 'Unknown Title')
        
        print(f"Structuring threads for story: {title}")
        
        # We chunk by top-level comments
        top_level_kids = story.get('kids', [])
        
        for kid_id in top_level_kids:
            # Build the full tree for this specific top-level comment
            thread_text = build_thread_context(kid_id, raw_data, depth=1)
            
            if thread_text.strip(): # Only save if the thread isn't empty
                chunk = {
                    "story_id": story_id,
                    "story_title": title,
                    "top_level_comment_id": kid_id,
                    "thread_context": thread_text
                }
                structured_dataset.append(chunk)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(structured_dataset, f, indent=2)

    print(f"\nParsing complete. Generated {len(structured_dataset)} logical conversation chunks. Saved to {output_path}")