import requests
import json

def search_hn_stories(query, num_stories=2):
    """
    Uses the Algolia API to search for top stories based on a query.
    """
    print(f"Searching for top {num_stories} stories about: '{query}'...")
    
    # The Algolia API endpoint for searching stories 
    search_url = f"https://hn.algolia.com/api/v1/search?query={query}&tags=story"
    response = requests.get(search_url)
    
    if response.status_code == 200:
        data = response.json()
        # Extract just the top results based on our limit
        stories = data.get('hits', [])[:num_stories]
        return stories
    else:
        print(f"Error fetching stories: {response.status_code}")
        return []

def get_hn_item(item_id):
    """
    Uses the Firebase API to fetch a specific item (a story or a comment) by its ID.
    """
    # The Firebase API endpoint for individual items 
    item_url = f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
    response = requests.get(item_url)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching item {item_id}: {response.status_code}")
        return None

# --- Main Execution ---
if __name__ == "__main__":
    # We use the specific query required for the final demo [cite: 63]
    target_query = "SQLite in production" 
    
    # 1. Get the top stories
    top_stories = search_hn_stories(target_query)
    
    for story in top_stories:
        story_id = story['objectID']
        title = story['title']
        print(f"\n--- Story: {title} (ID: {story_id}) ---")
        
        # 2. Fetch the full story details from Firebase to see its 'kids' (comments)
        story_details = get_hn_item(story_id)
        
        if story_details and 'kids' in story_details:
            top_level_comment_ids = story_details['kids']
            print(f"Found {len(top_level_comment_ids)} top-level comments.")
            
            # Let's just fetch the very first comment to see what the data looks like
            if top_level_comment_ids:
                first_comment_id = top_level_comment_ids[0]
                first_comment_data = get_hn_item(first_comment_id)
                
                print("\nRaw Data for the first comment:")
                # Pretty-print the JSON dictionary
                print(json.dumps(first_comment_data, indent=2))
        else:
            print("No comments found for this story.")