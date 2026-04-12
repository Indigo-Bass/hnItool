import requests
import json
import os

def search_hn_stories(query, num_stories=2):
    print(f"Searching for top {num_stories} stories about: '{query}'...")
    search_url = f"https://hn.algolia.com/api/v1/search?query={query}&tags=story"
    response = requests.get(search_url)
    if response.status_code == 200:
        return response.json().get('hits', [])[:num_stories]
    return []

def fetch_item_and_kids(item_id, storage_dict):
    """
    Recursively fetches an item and all its descendant comments.
    Saves them into a flat dictionary using the item ID as the key.
    """
    # Skip if we've already fetched this ID
    if str(item_id) in storage_dict:
        return

    item_url = f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
    response = requests.get(item_url)
    
    if response.status_code == 200:
        item_data = response.json()
        if item_data:
            storage_dict[str(item_id)] = item_data
            
            # If this item has children, fetch them recursively
            if 'kids' in item_data:
                for kid_id in item_data['kids']:
                    fetch_item_and_kids(kid_id, storage_dict)

if __name__ == "__main__":
    target_query = "SQLite in production"
    raw_data_storage = {}
    
    top_stories = search_hn_stories(target_query)
    
    for story in top_stories:
        story_id = story['objectID']
        print(f"Fetching full thread for: {story['title']} (ID: {story_id})")
        fetch_item_and_kids(story_id, raw_data_storage)
        
    # Create a data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # Save the raw data to disk
    output_path = 'data/raw_hn_data.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(raw_data_storage, f, indent=2)
        
    print(f"\nData acquisition complete. {len(raw_data_storage)} total items saved to {output_path}")