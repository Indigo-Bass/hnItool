from google import genai
from google.genai import types
import json
import os
from pydantic import BaseModel, Field
import sys
class HNDigest(BaseModel):
    executive_summary: str = Field(
        description="A highly technical, concise TL;DR of the community's consensus."
    )
    main_technical_arguments: list[str] = Field(
        description="The core technical debates, architectural points, and arguments made."
    )
    pros: list[str] = Field(
        description="Explicit advantages of using SQLite in production mentioned in the text."
    )
    cons_and_risks: list[str] = Field(
        description="Bottlenecks, scaling risks, and disadvantages mentioned."
    )
    alternative_tools: list[str] = Field(
        description="Specific alternative databases or tools recommended by the community."
    )

def load_data(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def json_to_markdown(digest_dict):
    md = f"Executive Summary\n{digest_dict['executive_summary']}\n\n" 

    md += "Main Technical Arguments\n"
    for arg in digest_dict['main_technical_arguments']:
        md += f"* {arg}\n"
    md += "\n"

    md += "Pros of Using this Tech in Production\n"
    for pro in digest_dict['pros']:
        md += f"* {pro}\n"
    md += "\n"
    
    md += "Cons and Risks\n"
    for con in digest_dict['cons_and_risks']:
        md += f"* {con}\n"
    md += "\n"
    
    md += "Alternative Tools Mentioned\n"
    if digest_dict['alternative_tools']:
        for tool in digest_dict['alternative_tools']:
            md += f"* {tool}\n"
    else:
        md += "* None explicitly mentioned.\n"
    return md

def generate(dataset, query):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set.")
    client = genai.Client(api_key=api_key)
    context_string = "\n\nNext Thread Chunk:\n\n".join(
        [chunk['thread_context'] for chunk in dataset]
    )
    system_instruction = """
    You are a Senior Staff Data Engineer. Your task is to analyze Hacker News discussion 
    threads and output a highly technical, structured digest.
    You must rely strictly on the provided conversation context. Do not invent information.
    Do not use generic phrases like 'opinions are mixed'.
    Provide concrete, technical details for every field.
    """
    prompt = f"Analyze the following Hacker News threads regarding '{query}' and populate the required JSON schema:\n\n{context_string}"
    print("Initializing Gemini model and sending data (this may take a few seconds)")
    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=0.1,
        response_mime_type="application/json",
        response_schema=HNDigest, 
    )
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=config
    )
    digest_json = json.loads(response.text)
    return json_to_markdown(digest_json)

if __name__ == "__main__":
    input_path = 'data/structured_chunks.json'
    output_path = 'data/final_digest.md'
    query = sys.argv[1] if len(sys.argv) > 1 else "SQLite in production"
    dataset = load_data(input_path)
    try:
        digest_markdown = generate(dataset, query)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(digest_markdown)
        print(f"\nSuccess! Digest generated and saved to {output_path}")
        print("\nPreview: ")
        print(digest_markdown[:500] + "...\n")
    
    except Exception as e:
        print(f"An error occurred during generation: {e}")