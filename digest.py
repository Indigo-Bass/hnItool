import os
import json
from google import genai
from google.genai import types

def load_structured_data(filepath):
    """Loads the parsed chunk data from Stage 2."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_hn_digest(dataset):
    """
    Constructs the prompt and calls the modern Gemini API to synthesize the digest.
    """
    # 1. Securely load the API key from the environment
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set. Please run: $env:GEMINI_API_KEY=\"your_key\"")
    
    # Initialize the modern client
    client = genai.Client(api_key=api_key)

    # 2. Concatenate the structured chunks
    context_string = "\n\n=== NEXT THREAD CHUNK ===\n\n".join(
        [chunk['thread_context'] for chunk in dataset]
    )

    # 3. Strict instructions for the LLM
    system_instruction = """
    You are a Senior Staff Data Engineer. Your task is to analyze Hacker News discussion threads and output a highly technical, structured digest.
    You must rely strictly on the provided conversation context. Do not invent information.
    Do not use generic phrases like "opinions are mixed". 
    Format your response in Markdown with the following exact headers:
    
    ## Executive Summary
    ## Main Technical Arguments
    ## Pros of Using this Tech in Production
    ## Cons and Risks
    ## Alternative Tools Mentioned
    """

    prompt = f"Analyze the following Hacker News threads regarding 'SQLite in production' and generate the required digest:\n\n{context_string}"

    print("Initializing modern Gemini client and sending data (this may take a few seconds)...")
    
    # Generate content using the updated syntax
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.1,
        )
    )

    return response.text

if __name__ == "__main__":
    input_path = 'data/structured_chunks.json'
    output_path = 'data/final_digest.md'
    
    dataset = load_structured_data(input_path)
    
    try:
        digest_markdown = generate_hn_digest(dataset)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(digest_markdown)
            
        print(f"\nSuccess! Digest generated and saved to {output_path}")
        print("\n--- PREVIEW ---")
        print(digest_markdown[:500] + "...\n")
        
    except Exception as e:
        print(f"An error occurred during generation: {e}")