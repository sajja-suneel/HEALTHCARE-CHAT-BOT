# C:\Users\sajja\vscode\health\backend\app\rag\generator.py
import os
import time
import uuid
import json
from dotenv import load_dotenv
from openai import OpenAI  # OpenAI client compatible with Groq's API

from app.rag.retriever import retrieve_context
from app.rag.prompts import build_prompt, build_contextualize_prompt
from app.rag.chat_history import init_db, save_message, get_history
from app.rag.log import logger
from app.rag.redis_cache import get_cached_response, set_cached_response

load_dotenv()

# Initialize OpenAI client pointed to Groq Cloud's API endpoint
client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

init_db()

def generate_answer(question, session_id=None):
    """Non-streaming generation wrapper."""
    if session_id is None:
        session_id = str(uuid.uuid4())
    
    # Check cache first
    cached_payload = get_cached_response(question)
    if cached_payload:
        try:
            return json.loads(cached_payload)
        except Exception:
            pass

    context_window = get_history(session_id, limit=6)
    standalone_question = question
    if context_window:
        rewrite_prompt = build_contextualize_prompt(question, context_window)
        try:
            rewrite_response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",  
                messages=[{"role": "user", "content": rewrite_prompt}],
                temperature=0.0,
                max_tokens=150
            )
            candidate_question = rewrite_response.choices[0].message.content.strip()
            if candidate_question:
                standalone_question = candidate_question
        except Exception as e:
            logger.error(f"Error reformulating question: {e}")

    docs = retrieve_context(standalone_question)
    if not docs:
        no_info_ans = "Information not found in the medical knowledge base."
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

    context = "\n\n".join(
        f"[Source Document: {doc.get('source', 'Unknown')}, Page: {doc.get('page', 'Unknown')}]\nText: {doc['text']}"
        for doc in docs
    )

    prompt = build_prompt(question=question, context=context, chat_history=context_window)

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",  
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=1000
        )
        answer_text = response.choices[0].message.content.strip()
        save_message(session_id, "user", question)
        save_message(session_id, "model", answer_text)

        chunk_details = []
        for index, doc in enumerate(docs):
            chunk_details.append({
                "chunk_no": index + 1,
                "score": round(float(doc.get("score", 0.0)), 4),
                "chunk_text": doc.get("text", ""),
                "page_no": doc.get("page", "Unknown"),
                "source": doc.get("source", "Unknown")
            })

        metadata = {
            "session_id": session_id,
            "question": question,
            "standalone_question": standalone_question,
            "chunk_count": len(docs),
            "source": docs[0].get("source", "Unknown") if docs else "Unknown",
            "chunks": chunk_details
        }  

        result = {
            "answer": answer_text,
            "sources": [{"page": d.get("page", "Unknown"), "source": d.get("source", "Unknown")} for d in docs],
            "metadata": metadata
        }

        # Cache result
        set_cached_response(question, json.dumps(result))
        return result

    except Exception as e:
        logger.error(f"Groq Error: {e}")
        return {"answer": "Error generating response.", "sources": [], "metadata": {"error": str(e)}}


def generate_answer_stream(question, session_id=None):
    """Streams responses, pulling directly from Redis on a cache hit."""
    if session_id is None:
        session_id = str(uuid.uuid4())

    logger.info("=" * 60)
    logger.info(f"QUESTION RECEIVED (Session Stream: {session_id})")
    
    # 1. REDIS CACHE LOOKUP
    cached_payload = get_cached_response(question)
    if cached_payload:
        try:
            logger.info("CACHE HIT 🚀 Streaming from Redis memory")
            parsed = json.loads(cached_payload)
            
            # Send metadata packet first so citations render instantly
            yield f"data: {json.dumps({'metadata': parsed['metadata']})}\n\n"
            
            # Stream the cached answer text in small chunks
            cached_text = parsed["answer"]
            chunk_size = 25
            for i in range(0, len(cached_text), chunk_size):
                yield f"data: {json.dumps({'token': cached_text[i:i+chunk_size]})}\n\n"
                time.sleep(0.02)  # Short pause to simulate standard typing flow
                
            yield "data: [DONE]\n\n"
            return
        except Exception as e:
            logger.error(f"Failed to read from cache: {e}")

    # 2. CACHE MISS -> QUERY DATABASE & MODEL
    context_window = get_history(session_id, limit=6)
    standalone_question = question
    if context_window:
        rewrite_prompt = build_contextualize_prompt(question, context_window)
        try:
            rewrite_response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",  
                messages=[{"role": "user", "content": rewrite_prompt}],
                temperature=0.0,
                max_tokens=150
            )
            candidate_question = rewrite_response.choices[0].message.content.strip()
            if candidate_question:
                standalone_question = candidate_question
        except Exception as e:
            logger.error(f"Error reformulating question: {e}")

    docs = retrieve_context(standalone_question)
    save_message(session_id, "user", question)

    if not docs:
        no_info_ans = "Information not found in the medical knowledge base."
        save_message(session_id, "model", no_info_ans)
        yield f"data: {json.dumps({'token': no_info_ans, 'metadata': {'session_id': session_id, 'question': question, 'chunk_count': 0, 'chunks': []}})}\n\n"
        yield "data: [DONE]\n\n"
        return

    context = "\n\n".join(
        f"[Source Document: {doc.get('source', 'Unknown')}, Page: {doc.get('page', 'Unknown')}]\nText: {doc['text']}"
        for doc in docs
    )

    prompt = build_prompt(question=question, context=context, chat_history=context_window)

    chunk_details = []
    for index, doc in enumerate(docs):
        chunk_details.append({
            "chunk_no": index + 1,
            "score": round(float(doc.get("score", 0.0)), 4),
            "chunk_text": doc.get("text", ""),
            "page_no": doc.get("page", "Unknown"),
            "source": doc.get("source", "Unknown")
        })

    metadata = {
        "session_id": session_id,
        "question": question,
        "standalone_question": standalone_question,
        "chunk_count": len(docs),
        "source": docs[0].get("source", "Unknown") if docs else "Unknown",
        "chunks": chunk_details
    }
    
    # Yield metadata package first
    yield f"data: {json.dumps({'metadata': metadata})}\n\n"

    try:
        response_stream = client.chat.completions.create(
            model="llama-3.3-70b-versatile",  
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=1000,
            stream=True
        )

        full_answer = []
        for chunk in response_stream:
            token = chunk.choices[0].delta.content
            if token:
                full_answer.append(token)
                yield f"data: {json.dumps({'token': token})}\n\n"

        final_answer = "".join(full_answer)
        save_message(session_id, "model", final_answer)

        # 3. SAVE FINAL ANSWER + METADATA TO REDIS CACHE
        cache_data = {
            "answer": final_answer,
            "metadata": metadata
        }
        set_cached_response(question, json.dumps(cache_data))

    except Exception as e:
        logger.error(f"Groq Streaming Error: {e}")
        yield f"data: {json.dumps({'error': str(e)})}\n\n"

    yield "data: [DONE]\n\n"