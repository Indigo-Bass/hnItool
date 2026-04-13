import requests
import json
import os

def search_hn_stories(query, num_stories=5):
    print(f"Searching for top {num_stories} stories about: '{query}'...")
    search_url = f"https://hn.algolia.com/api/v1/search?query={query}&tags=story&hitsPerPage={num_stories}"
    response = requests.get(search_url)
    if response.status_code == 200:
        return response.json().get('hits', [])[:num_stories]
    return []

def fetch_full_thread_algolia(story_id):
    """
    Fetches the full comment tree via Algolia's items endpoint.
    Unlike Firebase, this returns 'points' on comments too.
    Returns the nested item dict.
    """
    url = f"https://hn.algolia.com/api/v1/items/{story_id}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

def flatten_item(item, storage_dict):
    """
    Recursively flattens the nested Algolia response into a flat dict
    keyed by item ID — same structure the rest of the pipeline expects.
    """
    if not item:
        return
    item_id = str(item.get('id'))
    if not item_id or item_id in storage_dict:
        return

    # Normalize Algolia field names to match Firebase conventions
    storage_dict[item_id] = {
        'id': item.get('id'),
        'type': item.get('type'),
        'by': item.get('author'),
        'text': item.get('text'),
        'time': item.get('created_at_i'),
        'points': item.get('points') or 0,
        'title': item.get('title'),
        'deleted': item.get('deleted', False),
        'dead': item.get('dead', False),
        'kids': [child['id'] for child in item.get('children', []) if child]
    }

    for child in item.get('children', []):
        flatten_item(child, storage_dict)

if __name__ == "__main__":
    target_query = "SQLite in production"
    raw_data_storage = {}

    top_stories = search_hn_stories(target_query, num_stories=5)

    for story in top_stories:
        story_id = story['objectID']
        print(f"Fetching full thread for: {story['title']} (ID: {story_id})")
        thread = fetch_full_thread_algolia(story_id)
        if thread:
            flatten_item(thread, raw_data_storage)
        else:
            print(f"  Warning: Could not fetch story {story_id}")

    os.makedirs('data', exist_ok=True)
    output_path = 'data/raw_hn_data.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(raw_data_storage, f, indent=2)

    print(f"\nData acquisition complete. {len(raw_data_storage)} total items saved to {output_path}")