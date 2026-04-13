To run this project, you need a Google Gemini API key.
###1. Install dependencies
```bash
pip install requests pydantic google-genai
###2. Set your API Key
$env:GEMINI_API_KEY="your_api_key_here"
###3. Run the pipeline in order:
python fetcher.py "(Enter query)"  # Fetches raw HN data
python parser.py                   # Structures the n-ary tree 
python digest.py "(Enter query)"   # Generates final_digest.md
python chat.py "(Enter query)"     # Starts the conversational assistant

###Stage 1: fetcher.py
I fetched data using the Algolia API and selected the top 5 relevant stories to avoid spending a lot of time in obtaining the data. Several hundred items were produced across the five threads wherein each item is a raw Firebase JSON object containing fields like by, text, time, kids, score, and type. The exact count is printed at runtime.
search() hits Algolia to find the top 5 most relevant stories for the query. For each story, fetch() hits Firebase with the story ID, stores the item, then recurses into the kids array — fetching every comment and every reply to every comment until the full thread is captured. All items land in a single flat dictionary keyed by string item ID.
One trade-off of using Firebase API is that it returns no comment upvotes- it only returns upvotes on stories.The digest is effectively built on tree-order comments rather than community-validated signal.

###Stage 2: parser.py
Two categories of items are discarded in Stage 2 during parsing- items with deleted: true are removed because Firebase returns them as empty shells with no author or text and items with dead: true are removed because these are comments flagged by HN moderators as low quality or spam. Both are checked before any text is processed.
To avoid blindly splitting the data and confusing the LLM I kept each story as a single self contained chunk by using the context function which involves recursion and appropriate indentation. A Depth-First Search (DFS) algorithm traverses the kids arrays, flattening a root comment and all its nested replies into a single logical "conversation block."
I converted the Unix timestamps to UTC strings using the datetime and timezone packages and the upvotes of each reply/comment is also documented for reference. Each story is capped at 55 comments to prevent overloading. The trade-off here is that there is no guarantee the first 55 comments after tree-traversal are the most representative ones — particularly since the upvote sort doesn't function.

###Stage 3: digest.py
In the digest.py file, the LLM reads structured_chunks.json and writes the digest to data/final_digest.md. I set the temperature to 0.1 as the goal is factual extraction from source material not creative writing.
I defined a strict defined pydantic scheme (executive summary, pros and cons, etc) so the output is in the same structured manner each time.This schema is passed to the API via response_schema=HNDigest. Gemini is constrained to return valid JSON matching this shape exactly — it cannot skip required fields, hallucinate extra sections, or return a paragraph where a list is expected. The json_to_markdown() function then programmatically stitches the validated JSON into the final markdown file.
The trade-off here is that all thread context is concatenated into one prompt string. For a very active or broad topic this grows large and can approach Gemini's context window limits. The current code does not guard against this — if the context is too large the API may truncate it silently or return an error. A more robust approach would chunk context across multiple digest calls and merge results.

###Stage 4: chat.py
Here, I implemented an Anchored Context + Sliding Window strategy to handle context management without exhausting the LLM's token limit. The contents of final_digest.md and structured_chunks.json are injected directly into the model's system_instruction. This acts as an "anchor", establishing the ground truth once upon initialization.
To manage the ongoing conversation, I used a Sliding Window approach. The chat session actively monitors the message history and strictly caps it at the last 4 user-assistant exchanges (8 messages total). Once the limit is reached, the oldest messages are sliced off, and the chat session is refreshed with the truncated history.
The trade-off here is deliberate conversational amnesia. If a user asks a question that references something from 5 turns ago, the bot will completely forget the context and fail to answer. I prioritized API stability, speed, and token cost reduction over infinite conversational memory.

###Stage 5: Edge Cases & Hardening
I hardened the bot using strict system rules and a low model temperature (0.2) to prioritize factual reporting over creative generation. Here is how it handles the required scenarios:
a.) A question that has no answer in the fetched data: The system prompt includes a print statement which says, "I cannot find the answer to that in the fetched HN threads," if the data is missing. It successfully refuses to hallucinate external knowledge (though I allowed a minor exception for it to provide basic technical definitions, provided it caveats that it is using general knowledge).
b.) Contradictory opinions in the data: Because the bot has access to the full, indented tree and operates at a low temperature, it doesn't invent a false consensus to keep things simple. It accurately synthesizes the conflict, typically responding with, "The community is split. Some users argue X, while others point out Y."
c.) A question that references something from way earlier in the chat: As noted in the Stage 4 tradeoffs, the app breaks here. Due to the sliding window, the bot will not know what the user is referring to and will ask for clarification.
d.) A manipulative question designed to force a false consensus: The bot relies heavily on its anchored raw data as the ultimate ground truth. If a user asks, "Since everyone in the thread agreed SQLite is terrible, what should I use?", the bot actively corrects the premise based on the data before answering.
