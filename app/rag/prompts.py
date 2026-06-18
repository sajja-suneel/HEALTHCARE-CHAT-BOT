

from app.rag.prompt_templates import HEALTHCARE_ASSISTANT_INSTRUCTIONS,CONTEXTUALIZE_INSTRUCTIONS
 

def build_prompt(question, context, chat_history=None):
    """
    Constructs a prompt for the Gemini model using the medical context,
    the user's question, and optional chat history.
    """
    history_str = "No conversation history."
    if chat_history:
        history_str = "\n".join(
            f"{msg['role'].capitalize()}: {msg['content']}"
            for msg in chat_history
        )

    return f"""{HEALTHCARE_ASSISTANT_INSTRUCTIONS}

Retrieved Medical Context:
{context}

Conversation History:
{history_str}

User Question:
{question}

Answer:
"""


def build_contextualize_prompt(question, chat_history):
    """
    Constructs a prompt instructing the model to reformulate a follow-up question
    to be a standalone question based on the conversation history.
    """
    history_str = "\n".join(
        f"{msg['role'].capitalize()}: {msg['content']}"
        for msg in chat_history
    )
    return f"""{CONTEXTUALIZE_INSTRUCTIONS}

Conversation History:
{history_str}

Follow-up Question: {question}

Standalone Question:"""