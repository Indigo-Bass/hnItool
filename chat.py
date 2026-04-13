from google import genai
from google.genai import types
import json
import os
import sys

class HNResearchAssistant:
    def __init__(self, data_path, digest_path, history_limit=5):
        self.history_limit = history_limit
        self.raw_context = self._load_json(data_path)
        self.digest = self._load_text(digest_path)
        
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set.")
        self.client = genai.Client(api_key=api_key)
        
        system_instruction = f"""
        You are an elite developer research assistant. 
        Your job is to answer user questions about a specific Hacker News topic.
        CRITICAL RULES: 
        1. For opinions, technical arguments, pros/cons, and community consensus, you MUST use ONLY the provided Hacker News data.
        2. If a user asks for a basic definition (e.g., "What is SQLite?"), you may use your general knowledge to define it, but briefly mention that this is general knowledge.
        3. If a user asks a specific question about the discussion that cannot be answered by the context, explicitly state: "I cannot find the answer to that in the fetched HN threads."
        Phase 1: The Digest
        {self.digest}
        Raw Thread Context
        {json.dumps(self.raw_context, indent=2)}
        """

        self.config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.2 
        )
        self.chat_session = self.client.chats.create(
            model='gemini-2.5-flash',
            config=self.config
        )

    def _load_json(self, filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return "Raw data not found."

    def _load_text(self, filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return "Digest not found."

    def ask(self, user_message):
        max_messages = self.history_limit * 2
        history = self.chat_session.get_history()
        if len(history) > max_messages:
            new_history = history[-max_messages:]
            self.chat_session = self.client.chats.create(
                model='gemini-2.5-flash',
                config=self.config,
                history=new_history
            )
            
        response = self.chat_session.send_message(user_message)
        return response.text

if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "SQLite in production"
    DATA_FILE = 'data/structured_chunks.json'
    DIGEST_FILE = 'data/final_digest.md'
    print("Booting up HN Research Assistant...")
    try:
        assistant = HNResearchAssistant(DATA_FILE, DIGEST_FILE, history_limit=4)
        print("\n" + "="*50)
        print("HN Thread Intelligence Active.")
        print(f"Topic: {query}")
        print("Type 'exit' or 'quit' to end the session.")
        print("="*50 + "\n")
        while True:
            user_input = input("\nYou: ")
            if user_input.lower() in ['exit', 'quit']:
                print("Ending session. Goodbye!")
                break
            if not user_input.strip():
                continue
            print("\nThinking...")
            answer = assistant.ask(user_input)
            print(f"\nAssistant: {answer}")
    except Exception as e:
        print(f"\nFailed to start chat: {e}")