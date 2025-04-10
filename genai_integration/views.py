from django.shortcuts import render
from django.conf import settings
from google import genai
from google.genai import types
from markdownify import markdownify as md
from typing import List
from core.models import NewsArticle


def summarize(htmls: List[str], question: str) -> str:
    '''
    Parameters
    ----------
    htmls : List[str]
        List of html documents to parse and send to LLM
    question : str
        User question
    
    Returns
    -------
    str
        The generated answer from Gemini
    '''
    prompt = f'''You are Gemini, a helpful assistant to help user get the latest financial informations and answer their questions.

For the user's questions, you have these informations to refer to:

{'\n---\n'.join(map(md, htmls))}'''
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    response = client.models.generate_content(
        model='gemini-2.5-pro-exp-03-25',
        contents=[
            types.Content(role='system', parts=types.Part.from_text(prompt)),
            types.Content(role='user', parts=types.Part.from_text(question)),
        ],
    )
    return response.text


def summarize_for_category(category, articles) -> str:
    """
    Generate a professional summary for a specific news category

    Parameters
    ----------
    category : str
        The news category (e.g., "Regulatory Actions")
    articles : List[Dict]
        List of article dictionaries containing:
        - title: str
        - source: str
        - date: str
        - content: str (optional)

    Returns
    -------
    str
        The generated summary from Gemini
    """
    # Prepare the news content for the prompt
    articles_text = "\n\n".join(
        f"Article {i + 1}: {article['title']}\n"
        f"Source: {article['source']}\n"
        f"Date: {article['date']}\n"
        f"{article.get('content', '')[:500]}..."  # Include first 500 chars of content if available
        for i, article in enumerate(articles)
    )

    prompt = f"""You are a senior financial analyst creating an executive summary about {category}.
    Here are {len(articles)} recent articles in this category:{articles_text}
    Please provide a 3-paragraph professional summary that:
    1. Identifies the 2-3 most important trends or developments
    2. Highlights any significant events or regulatory changes
    3. Notes the key players or institutions involved
    4. Provides context about potential market impacts
    5. Uses concise, professional language suitable for executives

    Structure your response with:
    - Brief introduction
    - Key findings
    - Potential implications"""

    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    try:
        response = client.models.generate_content(
            model='gemini-2.5-pro-exp-03-25',
            contents=[
                types.Content(role='system', parts=types.Part.from_text(
                    "You are a financial expert summarizing news for C-level executives.")),
                types.Content(role='user', parts=types.Part.from_text(prompt)),
            ],
            generation_config={
                "temperature": 0.3,  # More factual and focused
                "top_p": 0.9,
                "max_output_tokens": 1000,
            }
        )
        return response.text
    except Exception as e:
        return f"⚠️ Summary generation failed. Error: {str(e)}"