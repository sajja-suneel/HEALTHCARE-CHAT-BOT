import os
import time
import uuid

from dotenv import load_dotenv
from google import genai

from app.rag.retriever import retrieve_context
from app.rag.prompts import build_prompt, build_contextualize_prompt
from app.rag.chat_history import init_db, save_message, get_history
from app.rag.log import logger

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

# Initialize the chat history database
init_db()


def generate_answer(question, session_id=None):
    if session_id is None:
        session_id = str(uuid.uuid4())
    total_start = time.time()

    logger.info("=" * 60)
    logger.info(f"QUESTION RECEIVED (Session: {session_id})")
    logger.info(question)

    # 1. Fetch recent history (context window) for this session
    context_window = get_history(session_id, limit=6)

    # 2. Contextualize the question if history exists
    standalone_question = question
    if context_window:
        logger.info("Chat history found. Reformulating question...")
        rewrite_prompt = build_contextualize_prompt(question, context_window)
        try:
            rewrite_response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=rewrite_prompt,
                config={
                    "temperature": 0.0,
                    "max_output_tokens": 150
                }
            )
            candidate_question = rewrite_response.text.strip()
            if candidate_question:
                standalone_question = candidate_question
                logger.info(f"Reformulated standalone question: {standalone_question}")
        except Exception as e:
            logger.error(f"Error reformulating question: {e}")

    # 3. Retrieve context using the standalone question
    logger.info(f"RETRIEVING CONTEXT FOR: {standalone_question}")

    retrieval_start = time.time()
    docs = retrieve_context(standalone_question)
    retrieval_time = round(
        (time.time() - retrieval_start) * 1000,
        2
    )

    if not docs:
        no_info_ans = "Information not found in the medical knowledge base."
        # Store in history so the conversational flow is preserved
        save_message(session_id, "user", question)
        save_message(session_id, "model", no_info_ans)
        return {
            "answer": no_info_ans,
            "sources": [],
            "metadata": {
                "session_id": session_id,
                "question": question,
                "standalone_question": standalone_question,
                "chunk_count": 0,
                "chunks": []
            }
        }

        # Prepend source file and page metadata so the LLM knows which file each chunk belongs to
    context = "\n\n".join(
        f"[Source Document: {doc.get('source', 'Unknown')}, Page: {doc.get('page', 'Unknown')}]\nText: {doc['text']}"
        for doc in docs
    )

    # Build prompt passing context window (without intent)
    prompt = build_prompt(
        question=question,
        context=context,
        chat_history=context_window
    )

    logger.info("SENDING TO GEMINI")

    try:
        generation_start = time.time()

        # Call Gemini model
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "temperature": 0.2,
                "max_output_tokens": 1000
            }
        )

        generation_time = round(
            (time.time() - generation_start) * 1000,
            2
        )

        total_time = round(
            (time.time() - total_start) * 1000,
            2
        )

        logger.info("RESPONSE GENERATED")

        answer_text = response.text.strip()

        # 4. Save question and generated response to update the context window
        save_message(session_id, "user", question)
        save_message(session_id, "model", answer_text)

        chunk_details = []
        scores = []

        for index, doc in enumerate(docs):
            score = round(
                float(doc.get("score", 0.0)),
                4
            )
            scores.append(score)

            chunk_details.append(
                {
                    "chunk_no": index + 1,
                    "score": score,
                    "chunk_text": doc.get("text", ""),
                    "page_no": doc.get("page", "Unknown"),
                    "source": doc.get("source", "Unknown")
                }
            )

        metadata = {
            "session_id": session_id,
            "question": question,
            "standalone_question": standalone_question,
            "chunk_count": len(docs),
            "source": doc.get("source", "Unknown"),
            "chunks": chunk_details
        }  

        return {
            "answer": answer_text,
            "sources": [
                {
                    "page": doc.get(
                        "page",
                        "Unknown"
                    ),
                    "source": doc.get(
                        "source",
                        "Unknown"
                    )
                }
                for doc in docs
            ],
            "metadata": metadata
        }

    except Exception as e:
        logger.error(
            f"Gemini Error: {e}"
        )

        return {
            "answer": (
                "Error generating response."
            ),
            "sources": [],
            "metadata": {
                "error": str(e)
            }
        }


if __name__ == "__main__":
    question = "What is cancer?"

    result = generate_answer(
        question
    )

    print("\n")
    print("=" * 60)
    print("FINAL ANSWER")
    print("=" * 60)

    print(result["answer"])

    print("\n")
    print("=" * 60)
    print("METADATA")
    print("=" * 60)

    print(result["metadata"])