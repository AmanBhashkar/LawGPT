# TODO: migrate to autogen and split the responsibility of the paralegals add orchestrator
from ai_service.base import AIBase
from pinecone_service import pinecone_service
from llama_index.llms.gemini import Gemini
from llama_index.core.query_engine import CitationQueryEngine
from config import settings
from llama_index.core import VectorStoreIndex
from pydantic import BaseModel, Field
from typing import List, Optional
from llama_index.core.prompts import PromptTemplate

class FormulatedTaxQuestions(BaseModel):
    """Schema for formulated tax questions."""
    questions: str = Field(..., description="A formulated tax questions.")

class TaxParalegal(AIBase):
    def __init__(self):
        super().__init__()
        self.model = settings.TAX_PARALEGAL_MODEL
        self.llm = Gemini(api_key=settings.GEMENI_API_KEY, model_name="models/gemini-2.0-flash")

    # def ask_tax_paralegal(self, query: str) -> str:
    #     try:
    #         # Create a VectorStoreIndex from the existing vector store
    #         index = VectorStoreIndex.from_vector_store(self.vector_store)
    #         print("index", index)
    #         print("self.llm", self.llm)
            
    #         # Create a citation query engine from the index
    #         query_engine = CitationQueryEngine.from_args(
    #             index=index,
    #             llm=self.llm,
    #             similarity_top_k=12, 
    #             citation_chunk_size=512
    #         )
    #         print("query_engine", query_engine)
    #         # Execute the query
    #         response = query_engine.query(query)
    #         print(f"Query response: {response}")
    #         return str(response)
    #     except Exception as e:
    #         print(f"Error in ask_tax_paralegal: {str(e)}")
    #         raise e

  


    def formulate_tax_questions(self, query: str) -> FormulatedTaxQuestions:
        """
        Formulates tax questions from a given query, ensuring the output conforms to the FormulatedTaxQuestions Pydantic schema.

        Args:
            query: The user's tax-related query.

        Returns:
            An instance of FormulatedTaxQuestions, containing the formulated questions.
        """
        # Create a proper prompt template instead of a raw string
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
            # Use structured_predict with the proper prompt template
            validated_response = self.llm.structured_predict(
                FormulatedTaxQuestions,
                prompt=prompt_template,
                query=query  # Pass the query as a parameter to the template
            )
            
            print("questions", validated_response)
            return validated_response.questions
        except Exception as e:
            print(f"Error in formulate_tax_questions: {str(e)}")
            raise e
    
    def response_tax_paralegal(self, query: str) -> str:
        questions = self.formulate_tax_questions(query)
        result = pinecone_service.semantic_search(questions, 12)
        tax_prompt = f"""
        You are an experienced tax paralegal who has been working in the tax law field for more than 20 years.  You are given a question and a list of documents, these documents are about tax law.
        You need to answer the question based on the documents. If it contains info about different section you must cite the section in your answer.
        Question: {query}
        Documents: {result}
        Answer:
        """
        try:
            llm_response = self.llm.complete(tax_prompt)
            return llm_response.text
        except Exception as e:
            print(f"Error in response_tax_paralegal: {str(e)}")
            raise e
    
    def ask_tax_paralegal(self, query: str) -> str:
        # TODO: migrate to autogen and split the responsibility of the paralegals
        questions = self.formulate_tax_questions(query)
        response = self.response_tax_paralegal(questions)
        prompt = f"""
        You are an experienced tax lawyer who has been working in the tax law field for more than 20 years as a Solicitor. You know everything about indian tax law 1961 and 1972. You are given a question and answer from a search service.
        Your job is to review the answer and make sure it is correct and to the point.

        If you don't get any answer, then you should use your knowledge to answer the question.
        
        Question: {query}
        Answer: {response}
        """
        try:
            llm_response = self.llm.complete(prompt)
            return llm_response.text
        except Exception as e:
            print(f"Error in ask_tax_paralegal: {str(e)}")
            raise e
        
        
        return response


    

tax_paralegal = TaxParalegal()
