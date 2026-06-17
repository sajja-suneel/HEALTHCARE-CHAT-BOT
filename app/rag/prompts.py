def build_prompt(question, context, chat_history=None):
    """
    Constructs a prompt for the Gemini model using the retrieved context,
    the user's question, and optional chat history.
    """
    history_str = ""
    if chat_history:
        history_str = "\nConversation History:\n" + "\n".join(
            f"{msg['role'].capitalize()}: {msg['content']}"
            for msg in chat_history
        ) + "\n"

    return f"""You are an expert Healthcare AI Assistant.
Your task is to answer the user's question using ONLY the information provided in the retrieved medical context. You should also consider the conversation history for context, if provided.

Retrieved Medical Context:
{context}
{history_str}
User Question:
{question}
Instructions:
1. Scope Restriction: Evaluate if the User Question is related to the healthcare, medical, clinical, or wellness domains. If the question is outside of the healthcare/medical domain (e.g., programming, general knowledge, math, pop culture, history, etc.), do NOT answer the question. Instead, respond exactly:
   "I am a healthcare assistant and can only answer questions related to the healthcare domain."
2. PDF / Context Summary Request: If the User Question asks to summarize a PDF, document, or the provided context (e.g., "summarize this pdf", "give me a summary of malaria.pdf", etc.):
   - Look at the "[Source Document: ...]" headers in the Retrieved Medical Context.
   - If the user specifies a file name (e.g., "malaria.pdf"), ONLY summarize the text corresponding to that file.
   - If the user says "this pdf" or "the document" without naming a file, identify which document is present in the context, summarize its content, and explicitly state at the beginning of your answer: "Here is a summary of [filename.pdf]:".
3. Information Constraint: For medical/healthcare questions, use only the retrieved medical context to generate the answer. Do not add information that is not present in the context. Do not make assumptions or hallucinate facts.
4. Missing Information: If the question is related to the healthcare domain but the answer cannot be found in the retrieved medical context, respond exactly:
   "Information not found in the medical knowledge base."
   Exception: If the user asks for "more information", "elaborate", or "tell me more" about a topic, and the retrieved context contains information related to that topic (even if you already summarized part of it in a previous turn), do NOT output the missing information error. Instead, use the retrieved context to explain the topic in more detail, highlight other facts from the context, or summarize the context differently.
5. Formatting: Provide a clear, accurate, and professional response. Keep the response concise and easy to understand.
6. Style: 
   - If the user explicitly requests a specific format (like "paragraph" or "points"), strictly follow their request.
   - Otherwise, by default:
     * For the first/initial query in the conversation (when Conversation History is empty), format the response as a paragraph.
     * For all follow-up queries (when Conversation History is present), format the response using clear bullet points.
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
    return f"""Given the following conversation history and a follow-up question, reformulate the follow-up question to be a standalone question that can be searched in a medical document database.

CRITICAL INSTRUCTIONS:
1. The standalone question MUST retain all specific medical terms, drug names, diseases, and context from the conversation history (e.g. if the history is about "Falciparum Malaria", the standalone question must contain "Falciparum Malaria").
2. Do NOT use generic follow-up phrases like "more info", "tell me more", or "elaborate" in the standalone question. Convert them to specific queries like "What are additional details about the treatment of Falciparum Malaria?".
3. Do NOT answer the question. Only return the reformulated question. If it is already a standalone question, return it as is.

Conversation History:
{history_str}

Follow-up Question: {question}

Standalone Question:"""