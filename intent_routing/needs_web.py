from ddgs import DDGS
from core.generation import generate_response
system_prompt = (
    "You are Operus, an advanced local AI assistant. Your current task is to synthesize "
    "and summarize live information retrieved from the web to answer the user's question accurately.\n\n"
    "CRITICAL CONSTRAINTS:\n"
    "1. Rely ONLY on the facts explicitly mentioned in the provided Web Search Results. Do not extrapolate, "
    "guess, or assume missing metrics.\n"
    "2. If the results contain multiple conflicting answers (e.g., varying temperatures from different sources), "
    "briefly note the range or state the primary source's figure cleanly.\n"
    "3. Keep the output highly concise, objective, and conversational. Avoid meta-commentary like "
    "'Based on the text provided...' or 'According to my search...'. Just answer the user directly using the facts.\n"
    "4. If the search results do not contain enough relevant data to satisfy the user's question, "
    "explicitly state that you couldn't find the real-time details in the fetched results."
    "CONTEXT UTILIZATION GUIDE:\n"
    "5. If the provided 'Web Search Context' contains relevant, real-time data answering the prompt (like weather or news), "
    "synthesize it cleanly into your answer.\n"
    "6. If the user's question is a general knowledge question (e.g., science, history, coding) and the web context is "
    "repetitive or unhelpful, ignore the context completely and use your own broad internal knowledge base to answer.\n"
    "7. Keep your response conversational, authoritative, and direct. Avoid saying phrases like 'Based on the context provided...' "
    "or 'According to my web search...'. Just give the answer."
    "CRITICAL GROUNDING RULES:\n"
    "1. You must prioritize the provided Web Search Results over your own internal knowledge base.\n"
    "2. If the search results state a fact that contradicts what you think you know, use the search result fact anyway.\n"
    "3. Do not mention your internal training limits or state 'Based on my training data...'. Just speak the facts directly from the text.\n"
    "4. If the data is missing from the search block, say 'I couldn't verify that cleanly from current web contexts.'"
)
def web_search(query, history=None):
    if history is not None:
        search_keywords=generate_response(query=query,system_prompt="You are a helpful assistant. You are provided with user's web search query and their prevous chat logs. Use it to create a new query pointing their exact query. IMPORTANT: Only output raw keywords and absolutely nothing else.",max_new_tokens=40,conversation_history=history)
    else:
        search_keywords=query
    with DDGS() as ddgs:
        results = list(ddgs.text(search_keywords, max_results=3))
    chunks = [r["body"] for r in results]
    searched_content = "\n".join(chunk for chunk in chunks)

    summarized_result = generate_response(query = f"User question: {query}\n\nWeb results:\n{searched_content}",system_prompt=system_prompt,max_new_tokens=200,conversation_history=history)
    return summarized_result
    
