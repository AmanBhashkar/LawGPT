# # Ensure the OPENAI_API_KEY is set in the environment
# from autogen import ConversableAgent
# from autogen import AfterWorkOption, ConversableAgent, initiate_swarm_chat
# from autogen.agents.experimental import DocAgent
# from autogen.agentchat.contrib.rag import LlamaIndexQueryEngine
# from llama_index.vector_stores.pinecone import PineconeVectorStore
# from config import settings 

# llm_config = {"model": "gpt-4o", "api_type": "openai", "cache_seed": None}
# pinecone_vector_store =  PineconeVectorStore(pinecone_index=settings.PINECONE_INDEX)

# pinecone_query_engine = LlamaIndexQueryEngine(
#     vector_store=pinecone_vector_store,
#     llm=OpenAI(model="gpt-4o", temperature=0.0),  # Default model for querying, change if needed
# )


# question = "How much money did Nvidia spend in research and development"
# answer = pinecone_query_engine.query(question)
# print(answer)