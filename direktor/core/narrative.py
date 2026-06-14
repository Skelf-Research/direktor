"""
Narrative optimization module for Direktor.

Provides content optimization, NLP narrative enhancement, and grapheme-level
optimization using the OpenAI API.
"""

from __future__ import annotations

from .logger import get_logger
from .settings import get_settings

logger = get_logger("narrative")

_CONTENT_OPTIMIZATION_PROMPT = """\
You are an expert editor tasked with optimizing articles for clarity, engagement,
and readability. Your goal is to improve the overall quality of the text while
preserving the core message and key information.

Instructions:
1. Analyze the input article for areas of improvement.
2. Enhance the article by:
   - Clarifying complex ideas
   - Improving sentence structure and flow
   - Strengthening the introduction and conclusion
   - Ensuring logical progression of ideas
   - Removing unnecessary repetition or filler content
   - Adjusting tone for better engagement
3. Maintain the original article's core message and key points.
4. Preserve any technical terms or jargon that are essential to the topic.
5. Aim for a natural, professional writing style.
"""

_NLP_PROMPT = """\
You are an expert in neuro-linguistic programming and narrative techniques.
Enhance the given text using NLP principles to make it more engaging,
persuasive, and impactful.

Instructions:
1. Analyze the input text for opportunities to apply NLP techniques.
2. Enhance the narrative using the following NLP principles:
   - Sensory-rich language
   - Pacing and leading
   - Framing
   - Presuppositions
   - Metaphors and analogies
   - Future pacing
   - Embedded commands
   - Rapport building
3. Maintain the core message and key information.
4. Ensure the text flows naturally and doesn't feel manipulative.
5. Preserve the overall tone and style appropriate for the subject matter.
"""

_GRAPHEME_PROMPT = """\
You are a linguistic expert specializing in grapheme-level text optimization.
Refine the text by making small, character-level changes that enhance
readability and engagement without altering the overall meaning.

Instructions:
1. Analyze the input text for potential grapheme-level improvements.
2. Make character-level or small character group changes to:
   - Simplify complex words (e.g., changing "utilize" to "use")
   - Improve rhythm and flow by adjusting punctuation or word breaks
   - Enhance clarity by modifying word choice at a granular level
   - Optimize for readability by adjusting spelling variants
3. Ensure that changes do not alter the meaning or tone.
4. Maintain a natural, human-written feel.
5. Preserve technical terms, proper nouns, and essential jargon.
"""


def get_ai_response(prompt: str, content: str, max_tokens: int = 1000) -> str:
    """Get an AI response from the OpenAI API.

    Args:
        prompt: System prompt for the AI.
        content: User content to process.
        max_tokens: Maximum tokens in the response.

    Returns:
        AI response content.

    Raises:
        ValueError: If the response content is empty.
    """
    settings = get_settings()
    response = settings.client.chat.completions.create(
        model=settings.gpt4_model,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": content},
        ],
        max_tokens=max_tokens,
        n=1,
        temperature=0.7,
    )
    result = response.choices[0].message.content
    if result is None:
        raise ValueError("OpenAI returned empty response content.")
    return result.strip()


def content_optimization(content: str) -> str:
    """Optimize content for clarity, engagement, and readability."""
    logger.info("Running content optimization")
    return get_ai_response(_CONTENT_OPTIMIZATION_PROMPT, content)


def nlp_narrative_enhancement(content: str) -> str:
    """Enhance content using neuro-linguistic programming techniques."""
    logger.info("Running NLP narrative enhancement")
    return get_ai_response(_NLP_PROMPT, content)


def grapheme_optimization(content: str) -> str:
    """Optimize content at the grapheme (character) level."""
    logger.info("Running grapheme-level optimization")
    return get_ai_response(_GRAPHEME_PROMPT, content)


def optimize_content(input_content: str) -> str:
    """Optimize content through multiple enhancement stages.

    Args:
        input_content: Original content to optimize.

    Returns:
        Fully optimized content.
    """
    logger.info("Starting content optimization")
    optimized_content = content_optimization(input_content)
    nlp_enhanced_content = nlp_narrative_enhancement(optimized_content)
    final_content = grapheme_optimization(nlp_enhanced_content)
    logger.info("Content optimization complete")
    return final_content
