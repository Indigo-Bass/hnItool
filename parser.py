import requests
import json
import re
import html
from datetime import datetime

def clean_text(raw_html):
    """Strips HTML and unescapes entities for clean LLM ingestion."""
    if not raw_html:
        return ""
    text = html.unescape(raw_html)
    text = re.sub(r'<[^>]+>', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()

def get_snippet(text, max_length=60):
    """Generates a bounded snippet of the parent comment to maintain 1D context."""
    if not text:
        return ""
    return text[:max_length] + "..." if len(text) > max_length else text

def fetch_algolia_story_tree(story_id):
    """Fetches the entire n-ary comment tree in a single API call."""
    url = f"https://hn.algolia.com/api/v1/items/{story_id}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    print(f"Failed to fetch tree for {story_id}: {response.status_code}")
    return None

def flatten_and_filter_tree(node, parent_text="", depth=0):
    """
    Recursively flattens the comment tree into a 1D array while preserving 
    critical metadata (depth, points, parent_snippet).
    """
    comments = []
    
    # Base Case & Processing for Comments
    if node.get('type') == 'comment':
        raw_text = node.get('text', '')
        cleaned_text = clean_text(raw_text)
        author = node.get('author')
        
        # Noise Filter: Discard dead/deleted/empty comments
        if cleaned_text and author:
            comments.append({
                'id': node.get('id'),
                'author': author,
                'points': node.get('points') or 0,
                'depth': depth,
                'timestamp': node.get('created_at_i'),
                'parent_snippet': get_snippet(parent_text),
                'text': cleaned_text
            })
        
        current_text = cleaned_text
    else:
        # If it's the root story, the parent text for Level 1 comments is the story title
        current_text = clean_text(node.get('title', ''))

    # Recursive Step: Process 'children' array
    for child in node.get('children', []):
        comments.extend(flatten_and_filter_tree(child, current_text, depth + 1))
        
    return comments

if __name__ == "__main__":
    # Using the Algolia Search API to grab the top 5 story IDs first
    target_query = "SQLite in production"
    search_url = f"https://hn.algolia.com/api/v1/search?query={target_query}&tags=story"
    search_response = requests.get(search_url).json()
    top_story_ids = [hit['objectID'] for hit in search_response.get('hits', [])[:5]]
    
    final_dataset = []

    for story_id in top_story_ids:
        print(f"Processing tree for story ID: {story_id}...")
        tree_data = fetch_algolia_story_tree(story_id)
        
        if not tree_data:
            continue
            
        story_title = tree_data.get('title', 'Unknown Title')
        
        # 1. Flatten the n-ary tree and filter noise
        flattened_comments = flatten_and_filter_tree(tree_data)
        
        # 2. Rank by upvotes (points descending)
        flattened_comments.sort(key=lambda x: x['points'], reverse=True)
        
        # 3. Cap at top 55 to protect the LLM context window
        capped_comments = flattened_comments[:55]
        
        chunk = {
            "story_id": story_id,
            "story_title": story_title,
            "total_comments_parsed": len(flattened_comments),
            "comments_retained": len(capped_comments),
            "thread_data": capped_comments
        }
        final_dataset.append(chunk)

    # Save the optimized structure
    output_path = 'data/vision_structured_chunks.json'
    import os
    os.makedirs('data', exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_dataset, f, indent=2)

    print(f"\nArchitecture execution complete.")
    for data in final_dataset:
        print(f"[{data['story_title']}] -> Parsed: {data['total_comments_parsed']}, Retained: {data['comments_retained']}")