from google import genai
from google.genai import types
import json
import os

class HNResearchAssistant:
    def __init__(self, data_path, digest_path, history_limit=5):
        """
        Initializes the chat assistant with a sliding window strategy.
        history_limit: The maximum number of user/bot exchanges to remember.
        """
        self.history_limit = history_limit
        
        # 1. Load the data generated in previous stages
        self.raw_context = self._load_json(data_path)
        self.digest = self._load_text(digest_path)
        
        # 2. Configure the API using the NEW SDK
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set.")
        
        self.client = genai.Client(api_key=api_key)
        
        # 3. Build the "Anchor" System Instruction (Updated for definitions)
        system_instruction = f"""
        You are an elite developer research assistant. 
        Your job is to answer user questions about a specific Hacker News topic.
        
        CRITICAL RULES: 
        1. For opinions, technical arguments, pros/cons, and community consensus, you MUST use ONLY the provided Hacker News data.
        2. If a user asks for a basic definition (e.g., "What is SQLite?"), you may use your general knowledge to define it, but briefly mention that this is general knowledge.
        3. If a user asks a specific question about the discussion that cannot be answered by the context, explicitly state: "I cannot find the answer to that in the fetched HN threads."

        === PHASE 1: THE DIGEST ===
        {self.digest}

        === RAW THREAD CONTEXT ===
        {json.dumps(self.raw_context, indent=2)}
        """
        
        # Configure model settings
        self.config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.2 # Low temperature for factual, grounded answers
        )
        
        # Start the chat session using the new SDK syntax
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
        """
        Sends a message to the model while enforcing the sliding window context.
        """
        # --- CONTEXT MANAGEMENT: SLIDING WINDOW ---
        # The new SDK handles history as a list of Content objects.
        # A full interaction is 2 messages (User + Model). 
        max_messages = self.history_limit * 2
        
        history = self.chat_session.get_history()
        if len(history) > max_messages:
            # We must explicitly update the history list in the new SDK
            # Slicing keeps the most recent 'max_messages'
            new_history = history[-max_messages:]
            # Currently, the easiest way to reset sliding history in the new SDK 
            # is to create a new chat session with the truncated history
            self.chat_session = self.client.chats.create(
                model='gemini-2.5-flash',
                config=self.config,
                history=new_history
            )
            
        # Send the message
        response = self.chat_session.send_message(user_message)
        return response.text

# ==========================================
# Execution / Terminal UI
# ==========================================
if __name__ == "__main__":
    DATA_FILE = 'data/structured_chunks.json'
    DIGEST_FILE = 'data/final_digest.md'
    
    print("Booting up HN Research Assistant...")
    try:
        assistant = HNResearchAssistant(DATA_FILE, DIGEST_FILE, history_limit=4)
        
        print("\n" + "="*50)
        print("🤖 HN Thread Intelligence Active.")
        print("Topic: SQLite in production")
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