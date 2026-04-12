Stage 1: Data Acquisition & Audit

Data Volume: Pulled the top 2 stories matching the query "SQLite in production" using the Algolia Search API. Recursively fetched the entire comment tree using the Firebase API, resulting in a dataset of individual JSON objects representing stories and comments.


Data Quality Assessment: * Formatting: The raw text fields contain unescaped HTML entities (e.g., &gt;) and structural HTML tags (<p>, <i>), requiring sanitization before LLM processing.

Metadata Limitations: The Firebase API does not expose upvote scores for individual comments, so chronological ordering and thread depth will be used as primary context indicators instead of upvotes. Timestamps are in raw Unix integer format.

Discard Strategy: * Objects flagged with "deleted": true or "dead": true contain no text and provide no value to the LLM context. These are discarded during the parsing phase to conserve context window space.

Comments with empty text fields are also dropped.
