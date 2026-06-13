import os
from typing import Optional
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_ai_response(prompt: str, content: str) -> str:
    """Get AI response from OpenAI API.

    Args:
        prompt: System prompt for the AI
        content: User content to process

    Returns:
        AI response content
    """
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    model = os.getenv("GPT4_MODEL", "gpt-4o")
    response = client.chat.completions.create(
        model=model,  # Use the model from environment variables
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": content}
        ],
        max_tokens=1000,  # Adjust as needed
        n=1,
        stop=None,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()

def content_optimization(content: str) -> str:
    """Optimize content for clarity, engagement, and readability.

    Args:
        content: Input content to optimize

    Returns:
        Optimized content with improved clarity and engagement
    """
    prompt = """
    You are an expert editor tasked with optimizing articles for clarity, engagement, and readability. Your goal is to improve the overall quality of the text while preserving the core message and key information.

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
    return get_ai_response(prompt, content)

def nlp_narrative_enhancement(content: str) -> str:
    """Enhance content using neuro-linguistic programming techniques.

    Args:
        content: Input content to enhance

    Returns:
        Enhanced content with NLP techniques applied
    """
    prompt = """
    You are an expert in neuro-linguistic programming and narrative techniques. Your task is to enhance the given text using NLP principles to make it more engaging, persuasive, and impactful.

    Instructions:
    1. Analyze the input text for opportunities to apply NLP techniques.
    2. Enhance the narrative using the following NLP principles:
       - Sensory-rich language: Incorporate vivid descriptions that appeal to multiple senses.
       - Pacing and leading: Guide the reader's thought process by pacing their current experience and then leading them to new ideas.
       - Framing: Present information in a way that influences how the reader perceives it.
       - Presuppositions: Use language that presupposes certain ideas or outcomes.
       - Metaphors and analogies: Introduce relatable comparisons to simplify complex ideas.
       - Future pacing: Help the reader visualize future scenarios or outcomes.
       - Embedded commands: Subtly incorporate suggestions or calls to action within the text.
       - Rapport building: Use inclusive language to create a connection with the reader.
    3. Maintain the core message and key information from the input text.
    4. Ensure the enhanced text flows naturally and doesn't feel manipulative or overly sales-like.
    5. Preserve the overall tone and style appropriate for the subject matter.
    """
    return get_ai_response(prompt, content)

def grapheme_optimization(content: str) -> str:
    """Optimize content at the grapheme (character) level.

    Args:
        content: Input content to optimize

    Returns:
        Content optimized at character level
    """
    prompt = """
    You are a linguistic expert specializing in grapheme-level text optimization. Your task is to refine the text by making small, character-level changes that enhance readability and engagement without altering the overall meaning.

    Instructions:
    1. Analyze the input text for potential grapheme-level improvements.
    2. Make character-level or small character group changes to:
       - Simplify complex words (e.g., changing "utilize" to "use")
       - Improve rhythm and flow by adjusting punctuation or word breaks
       - Enhance clarity by modifying word choice at a granular level
       - Optimize for readability by adjusting spelling variants (e.g., "-ize" vs "-ise" endings)
    3. Ensure that changes do not alter the meaning or tone of the text.
    4. Maintain a natural, human-written feel to the text.
    5. Preserve technical terms, proper nouns, and essential jargon.
    """
    return get_ai_response(prompt, content)

def optimize_content(input_content: str) -> str:
    """Optimize content through multiple enhancement stages.

    Args:
        input_content: Original content to optimize

    Returns:
        Fully optimized content
    """
    print("Step 1: Content Optimization")
    optimized_content = content_optimization(input_content)
    print("Step 1 completed.")

    print("Step 2: NLP Narrative Enhancement")
    nlp_enhanced_content = nlp_narrative_enhancement(optimized_content)
    print("Step 2 completed.")

    print("Step 3: Grapheme-level Optimization")
    final_content = grapheme_optimization(nlp_enhanced_content)
    print("Step 3 completed.")

    return final_content

if __name__ == "__main__":
    input_content = input("Please enter the content you want to optimize: ")

    optimized_content = optimize_content(input_content)

    print("\nOptimized Content:")
    print(optimized_content)