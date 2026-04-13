import json
import html
import re
import os
from datetime import datetime, timezone

def clean_text(raw_html):
    if not raw_html:
        return ""
    text = html.unescape(raw_html)
    text = re.sub(r'<[^>]+>', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()

def context(item_id, raw_data, depth=0, max_items=55, count=None):
    if count is None:
        count = [0]
    item_id_str = str(item_id)
    if item_id_str not in raw_data or count[0] >= max_items:
        return ""
    item = raw_data[item_id_str]
    if item.get('deleted') or item.get('dead'):
        return ""
    result = ""
    indent = "  " * depth
    if item.get('type') == 'comment':
        author = item.get('by', 'anonymous')
        points = item.get('points', 0)
        time_str = datetime.fromtimestamp(item.get('time', 0), tz=timezone.utc).strftime('%Y-%m-%d %H:%M')
        text = clean_text(item.get('text', ''))
        if text:
            result += f"{indent}- [{author} | pts:{points} | {time_str}]: {text}\n"
            count[0] += 1
    if 'kids' in item and count[0] < max_items:
        kids_with_points = []
        for kid_id in item['kids']:
            kid = raw_data.get(str(kid_id), {})
            kids_with_points.append((kid_id, kid.get('points', 0)))
        kids_sorted = sorted(kids_with_points, key=lambda x: x[1], reverse=True)
        for kid_id, _ in kids_sorted:
            result += context(kid_id, raw_data, depth + 1, max_items, count)
            if count[0] >= max_items:
                break
    return result

if __name__ == "__main__":
    input_path = 'data/raw_hn_data.json'
    output_path = 'data/structured_chunks.json'
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: {input_path} not found. Please run fetcher.py first.")
        exit(1)
    final_dataset = []
    stories = [item for item in raw_data.values() if item.get('type') == 'story']
    stories.sort(key=lambda x: x.get('points', 0), reverse=True)
    for story in stories:
        story_id = story.get('id')
        story_title = story.get('title', 'Unknown Title')
        print(f"Structuring tree for: {story_title} (ID: {story_id})...")
        thread_text = f"STORY: {story_title}\n"
        count = [0]
        thread_text += context(
            story_id, raw_data, depth=0, max_items=55, count=count
        )
        final_dataset.append({
            "story_id": story_id,
            "story_title": story_title,
            "comments_retained": count[0],
            "thread_context": thread_text
        })
    os.makedirs('data', exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_dataset, f, indent=2)
    print(f"\nParsing complete. Processed {len(stories)} stories.")
    for data in final_dataset:
        print(f"  [{data['story_title']}] -> {data['comments_retained']} comments retained")