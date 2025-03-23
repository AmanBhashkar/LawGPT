from typing import Optional, Dict, Any
import json
import os
from pinecone_service import pinecone_service
from llama_index.llms.gemini import Gemini
from config import settings
from llama_index.core.prompts import PromptTemplate
from app_logger.ai_service_logger import setup_logger, log_function_call
from ai_service.agent_schema import IndividualAgentResponse, IndividualAgentUserQuery

# Configure logging
logger = setup_logger("tax_paralegal_tools")

# Initialize the LLM
llm = Gemini(api_key=settings.GEMENI_API_KEY, model_name="models/gemini-2.0-flash")

# Ensure environment variables are set for the tools
os.environ["AUTOGEN_USE_DOCKER"] = "True"

async def formulate_tax_questions(query: str, context_variables: Optional[Dict] = None) -> str:
    """
    Formulates tax questions from a given query to improve search results.
    
    Args:
        query: The user's tax-related query.
        
    Returns:
        A reformulated question optimized for vector search.
    """
    logger.info(f"Formulating tax questions for: {query}")
    
    prompt_template = PromptTemplate(
        """
        You are an experienced tax consultant who has been working in the tax law field for more than 20 years in client facing role. You know that the tax law is complex and it is not easy to understand for a layman. So you job is the formulate proper questions that will help user to understand the client's question better. You should expand the abbreviations and acronyms in the question. like TDS as Tax Deducted at Source. TCS as Tax Collected at Source.etc.
        Keep in mind that the user is a ai-agent that has access to the full tax law document in its vector store. You should formulate the question in such a way that will match the vector store. Make sure to keep the question precise and to the point yet covering all the aspects of the question. The question should be maximum 20 more than the original question. 
        Question: {query}
        NOTE: Keep the question direct and remove all kinds of fluff words.
        example:
        Question: What is the tax rate for income from salary?
        How to formulate the question:
        Step 1: Identify the main subject of the question.
        Step 2: Identify the key terms and concepts in the question.
        Step 3: Expand the key terms and concepts.
        Step 4: Formulate the question using the expanded key terms and concepts and your know about indian tax law by asking what type of question you can get the answer from the vector store which has all the tax law documents.
            for example: If the user asks about deductions available for salaried person you can ask for deductions under 80C and other sections.
            For these use ur knowledge about indian tax law 1961 and 1972 to formulate the question.
        """
    )
    
    try:
        # Extract the original user query and workplan if it exists
        if context_variables and "userquery" in context_variables:
            original_query = context_variables["userquery"]
            workplan = context_variables.get("workplan", "")
        else:
            # Create a default if not found
            original_query = query
            workplan = "Formulate a precise tax question to improve vector search results"
            
        prompt = prompt_template.format(query=query)
        llm_response = llm.complete(prompt)
        reformulated_question = llm_response.text
        logger.info(f"Successfully formulated tax questions: {reformulated_question[:100]}...")

        # Create an IndividualAgentUserQuery object
        user_query = IndividualAgentUserQuery(
            query=original_query,
            workplan=workplan
        )
        
        # Create the response in IndividualAgentResponse format
        response = IndividualAgentResponse(
            userquery=user_query,
            query_solved=True,
            proposed_solve=reformulated_question,
            next_speaker="information_retrieval_agent",
            next_speaker_question="Please search for relevant tax documents based on this reformulated question"
        )
        
        return json.dumps(response.model_dump())
    except Exception as e:
        logger.error(f"Error in formulate_tax_questions: {str(e)}")
        raise e

async def semantic_search(query: str, context_variables: Optional[Dict] = None) -> str:
    """
    Performs semantic search on the vector store to find relevant tax documents.
    
    Args:
        query: The formulated tax-related query.
        
    Returns:
        A string containing the search results in IndividualAgentResponse format.
    """
    logger.info(f"Performing semantic search for: {query}")
    try:
        # Extract the original user query and workplan if it exists
        if context_variables and "userquery" in context_variables:
            user_query_obj = context_variables["userquery"]
        else:
            # Create a default if not found
            user_query_obj = IndividualAgentUserQuery(
                query=query,
                workplan="Search for relevant tax law documents"
            ).model_dump()
        
        # Perform search
        result = pinecone_service.semantic_search(query, 12)
        logger.info("Successfully retrieved search results")
        
        # Create the response in IndividualAgentResponse format
        response = IndividualAgentResponse(
            userquery=user_query_obj,
            query_solved=True if result else False,
            proposed_solve=result,
            next_speaker="response_agent",
            next_speaker_question="Please synthesize these search results into a comprehensive answer"
        )
        
        return json.dumps(response.model_dump())
    except Exception as e:
        logger.error(f"Error in semantic_search: {str(e)}")
        raise e

async def generate_tax_response(query: str, search_results: str, context_variables: Optional[Dict] = None) -> str:
    """
    Generates a tax response based on the query and search results.
    
    Args:
        query: The tax-related query.
        search_results: The search results from the vector store.
        
    Returns:
        A comprehensive tax response in IndividualAgentResponse format.
    """
    logger.info(f"Generating tax response for: {query}")
    tax_prompt = f"""
    You are an experienced tax lawyer who has been working in the tax law field for more than 20 years. You are given a question and a list of documents, these documents are about tax law.
    You need to answer the question based on the documents. If it contains info about different section you must cite the section in your answer.
    Question: {query}
    Documents: {search_results}
    Answer:
    """
    try:
        # Extract the original user query and workplan if it exists
        if context_variables and "userquery" in context_variables:
            user_query_obj = context_variables["userquery"]
        else:
            # Create a default if not found
            user_query_obj = IndividualAgentUserQuery(
                query=query,
                workplan="Generate a comprehensive tax response"
            ).model_dump()
        
        # Generate response
        llm_response = llm.complete(tax_prompt)
        response_text = llm_response.text
        logger.info(f"Successfully generated tax response: {response_text[:100]}...")
        
        # Create the response in IndividualAgentResponse format
        response = IndividualAgentResponse(
            userquery=user_query_obj,
            query_solved=True,
            proposed_solve=response_text,
            next_speaker="user_proxy_agent",
            next_speaker_question="Here is the final answer to your tax question"
        )
        
        return json.dumps(response.model_dump())
    except Exception as e:
        logger.error(f"Error in generate_tax_response: {str(e)}")
        raise e