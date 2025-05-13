from django.shortcuts import render
from django.conf import settings
from typing import List
from core.models import NewsArticle
from openai import OpenAI

client = OpenAI(base_url="https://api.deepseek.com", api_key=settings.DEEPSEEK_API_KEY)

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

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a financial expert summarizing news for C-level executives."},
                {"role": "user", "content": prompt},
            ],
            stream=False,
            temperature=0.3,
            top_p=0.9,
            max_completion_tokens=1000,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ Summary generation failed. Error: {str(e)}"
