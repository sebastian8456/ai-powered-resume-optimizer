import requests
from dotenv import load_dotenv
import os
import openai
from openai import OpenAI

# Use GPT-4o mini for prompts

def generate_resume(secret):
    prompt = "Create a software engineering resume example in a plain-text, single-string-friendly format in multiple lines, suitable for parsing by scripts or systems. Only produce the resume as output, nothing else."
    client = OpenAI(api_key=secret)
    response = client.chat.completions.create(
        model="gpt-4o-mini-2024-07-18",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content