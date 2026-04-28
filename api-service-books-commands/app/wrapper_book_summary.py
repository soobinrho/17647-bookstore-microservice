from google import genai


def get_book_500_words_summary(title: str, Author: str, ISBN: str) -> str:
    # Source: https://github.com/googleapis/python-genai?tab=readme-ov-file#client-context-managers
    try:
        with genai.Client() as client:
            prompt = (
                "You're Frank Herbert the author of Dune. I am a huge fan of yours. "
                + f"Please write a 500-words summary of the following book: {title} "
                + f"by the author {Author} with ISBN {ISBN}. I don't care if the book "
                + "actually exists or not, so please feel free to make up something "
                + "based on the book name and the book author. Please respond with a "
                + "summary of the book in exactly 500 words."
            )
            summary = (
                client.models.generate_content(
                    model="gemini-2.5-flash-lite",
                    contents=prompt,
                )
            ).text
    except Exception as e:
        summary = f"Gemini API returned the following error:\n{e}"

    return summary
