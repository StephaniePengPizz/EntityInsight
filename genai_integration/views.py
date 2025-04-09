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


def summarize_news(request):
    article_id = request.GET.get('id')
    article = NewsArticle.objects.get(id=article_id)
    # WARNING: remove google.generativeai as it is deprecated March 19, 2025
    # genai.configure(api_key=settings.GEMINI_API_KEY)
    # model = genai.GenerativeModel('gemini-pro')
    # response = model.generate_content(f"Summarize this article: {article.processed_content}")
    # return render(request, 'summary.html', {'summary': response.text})