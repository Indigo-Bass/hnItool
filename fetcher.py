import requests
import json
import os

def search(query, num=5):
    print(f"Searching for top {num} stories about: '{query}':")
    url = f"https://hn.algolia.com/api/v1/search?query={query}&tags=story&hitsPerPage={num}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get('hits', [])[:num]
    return []

def fetch(item_id, storage_dict):
    item_id_str = str(item_id)
    if item_id_str in storage_dict:
        return
    url = f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
    response = requests.get(url)
    if response.status_code != 200 or not response.json():
        return
    item = response.json()
    storage_dict[item_id_str] = item
    for kid_id in item.get('kids', []):
        fetch(kid_id, storage_dict)

if __name__ == "__main__":
    target_query = "SQLite in production"
    rawdata = {}
    top_stories = search(target_query, num=5)
    for story in top_stories:
        story_id = story['objectID']
        print(f"Fetching full thread for: {story['title']} (ID: {story_id})")
        fetch(story_id, rawdata)
    os.makedirs('data', exist_ok=True)
    output_path = 'data/raw_hn_data.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(rawdata, f, indent=2)
    print(f"\nData fetching complete. {len(rawdata)} total items saved to {output_path}")