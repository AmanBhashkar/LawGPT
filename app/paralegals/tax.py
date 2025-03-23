from config import settings
from typing import List, Optional, Dict, Any, TypeVar, Callable, Union
import json
import autogen
from autogen import register_function
from collections import deque
from functools import wraps
from google import genai
from paralegals import tax_paralegal_tools
from app_logger.ai_service_logger import setup_logger, log_function_call
from ai_service.agent_schema import IndividualAgentResponse, IndividualAgentUserQuery, AgentResponse

from .prompts import LegalParalegalPrompt, TaxParalegalPrompt,  ResponseAgentPrompt, QuestionFormulationPrompt, InformationRetrievalPrompt, user_proxy_agent_prompt

# Configure logging
logger = setup_logger("legal_paralegal")
logging_session_id = autogen.runtime_logging.start(logger_type="file", config={"filename": "legal_paralegal.log"})

F = TypeVar("F", bound=Callable[..., Any])

# Base prompts for all legal domains
class LegalParalegal:
    MAX_MESSAGES = 10  # Maximum number of messages to keep

    def __init__(self, context_variables: Optional[Dict] = None):
        logger.info("Initializing LegalParalegal")
        # self.llm = Gemini(api_key=settings.GEMENI_API_KEY, model_name="models/gemini-2.0-flash")
        self.context_variables = context_variables or {}
        
        # Initialize cache
        if self.context_variables.get("chat_id"):
            self.cache = autogen.Cache.disk(cache_seed=self.context_variables.get("chat_id"))
        else:
            self.cache = autogen.Cache.disk(cache_seed=Exception("Chat Id not found in context variables"))
        
        self.__setup_cache()
        self.__initialize_context_variables()
        
        # Configure Gemini for Autogen
    #     config={
    #     'response_mime_type': 'application/json',
    #     'response_schema': list[Recipe],
    # },
        self.llm_config = {
            "config_list": [{
                "model": "gemini-2.0-flash",  # Simplified model name that Gemini API recognizes
                "api_key": settings.GEMENI_API_KEY,
                "api_type": "google",
                # "response_schema":IndividualAgentResponse
            }],
        }

    @log_function_call(logger)
    def __setup_cache(self):
        """Setup cache by ensuring the conversation history stored as 'carryover' is maintained up to MAX_MESSAGES."""
        carryover = self.cache.get("carryover", [])
        carryover = list(deque(carryover, maxlen=self.MAX_MESSAGES))
        self.cache.set("carryover", carryover)

    @log_function_call(logger)
    def __initialize_context_variables(self):
        """Initialize context_variables with chat history from cache."""
        logger.debug("Initializing context variables with chat history")
        carryover = self.cache.get("carryover", [])
        if len(carryover) > self.MAX_MESSAGES:
            carryover = carryover[-self.MAX_MESSAGES:]
        self.context_variables["chat_history"] = deque(carryover, maxlen=self.MAX_MESSAGES)

    def context_wrapper(self, func: F) -> F:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Remove context_variables from kwargs if it exists to prevent double passing.
            if "context_variables" in kwargs:
                kwargs.pop("context_variables", None)
            # Add our context_variables.
            result = await func(*args, context_variables=self.context_variables, **kwargs)
            return result
        return wrapper  # type: ignore

    def agent_context_wrapper(self, agent: autogen.AssistantAgent) -> F:
        def wrapper(*args, **kwargs):
            kwargs["context_variables"] = self.context_variables
            return agent(*args, **kwargs)
        return wrapper  # type: ignore

    @log_function_call(logger)
    def __register_legal_paralegal_agent(self):
        """Register the main legal paralegal agent."""
        logger.debug("Registering legal paralegal agent")
        try:
            contextual_assistant = self.agent_context_wrapper(autogen.AssistantAgent)
            self.legal_paralegal_agent = contextual_assistant(
                llm_config=self.llm_config,
                name=LegalParalegalPrompt.NAME,
                system_message=LegalParalegalPrompt.get_system_prompt(self.context_variables),
                description=LegalParalegalPrompt.DESCRIPTION,
                human_input_mode="NEVER",
                max_consecutive_auto_reply=20,
                code_execution_config=False,
            )
            logger.info("Successfully registered legal paralegal agent")
        except Exception as e:
            logger.error(f"Failed to register legal paralegal agent: {str(e)}", exc_info=True)
            raise

    @log_function_call(logger)
    def __register_tax_paralegal_agent(self):
        """Register the tax paralegal agent."""
        logger.debug("Registering tax paralegal agent")
        try:
            contextual_assistant = self.agent_context_wrapper(autogen.AssistantAgent)
            self.tax_paralegal_agent = contextual_assistant(
                llm_config=self.llm_config,
                name=TaxParalegalPrompt.NAME,
                system_message=TaxParalegalPrompt.get_system_prompt(self.context_variables),
                description=TaxParalegalPrompt.DESCRIPTION,
                human_input_mode="NEVER",
                max_consecutive_auto_reply=20,
                code_execution_config=False,
            )
            logger.info("Successfully registered tax paralegal agent")
        except Exception as e:
            logger.error(f"Failed to register tax paralegal agent: {str(e)}", exc_info=True)
            raise

    @log_function_call(logger)
    def __register_question_formulation_agent(self):
        """Register the question formulation agent."""
        logger.debug("Registering question formulation agent")
        try:
            contextual_assistant = self.agent_context_wrapper(autogen.AssistantAgent)
            
            # Update system prompt to include functionality description
            system_prompt = QuestionFormulationPrompt.get_system_prompt(self.context_variables)
            system_prompt += """
You have the capability to reformulate tax questions to make them more effective for vector search.
When you receive a tax question:
1. Analyze the question carefully
2. Expand all abbreviations and make the question more precise
3. Format your response as a properly structured JSON following the IndividualAgentResponse format
"""
            
            self.question_formulation_agent = contextual_assistant(
                llm_config=self.llm_config,
                name=QuestionFormulationPrompt.NAME,
                system_message=system_prompt,
                description=QuestionFormulationPrompt.DESCRIPTION,
                human_input_mode="NEVER",
                max_consecutive_auto_reply=20,
                code_execution_config=False,
            )
            logger.info("Successfully registered question formulation agent")
            
        except Exception as e:
            logger.error(f"Failed to register question formulation agent: {str(e)}", exc_info=True)
            raise

    @log_function_call(logger)
    def __register_information_retrieval_agent(self):
        """Register the information retrieval agent."""
        logger.debug("Registering information retrieval agent")
        try:
            contextual_assistant = self.agent_context_wrapper(autogen.AssistantAgent)
            
            # Update system prompt to include functionality description
            system_prompt = InformationRetrievalPrompt.get_system_prompt(self.context_variables)
            system_prompt += """
You have the capability to search tax law documents in the vector store.
When you receive a reformulated question:
1. Perform a semantic search 
2. Generate what search results might look like based on the question
3. Format your response as a properly structured JSON following the IndividualAgentResponse format
"""
            
            self.information_retrieval_agent = contextual_assistant(
                llm_config=self.llm_config,
                name=InformationRetrievalPrompt.NAME,
                system_message=system_prompt,
                description=InformationRetrievalPrompt.DESCRIPTION,
                human_input_mode="NEVER",
                max_consecutive_auto_reply=20,
                code_execution_config=False,
            )
            logger.info("Successfully registered information retrieval agent")
        # TODO: Uncomment this when u figure out tool use from gemeni
        #     register_function(
        #     self.context_wrapper(tax_paralegal_tools.semantic_search),
        #     caller=self.information_retrieval_agent,
        #     executor=self.information_retrieval_agent,
        #     name="semantic_search",
        #     description="Use this tool to search tax law documents based on the question",
        # )
            
        except Exception as e:
            logger.error(f"Failed to register information retrieval agent: {str(e)}", exc_info=True)
            raise

    @log_function_call(logger)
    def __register_response_agent(self):
        """Register the response agent."""
        logger.debug("Registering response agent")
        try:
            contextual_assistant = self.agent_context_wrapper(autogen.AssistantAgent)
            
            # Update system prompt to include functionality description
            system_prompt = ResponseAgentPrompt.get_system_prompt(self.context_variables)
            system_prompt += """
You have the capability to generate comprehensive tax responses.
When you receive search results:
1. Analyze the search results carefully
2. Generate a detailed response that cites relevant sections of tax law
3. Format your response as a properly structured JSON following the IndividualAgentResponse format
"""
            
            self.response_agent = contextual_assistant(
                llm_config=self.llm_config,
                name=ResponseAgentPrompt.NAME,
                system_message=system_prompt,
                description=ResponseAgentPrompt.DESCRIPTION,
                human_input_mode="NEVER",
                max_consecutive_auto_reply=20,
                code_execution_config=False,
            )
            logger.info("Successfully registered response agent")
            
        except Exception as e:
            logger.error(f"Failed to register response agent: {str(e)}", exc_info=True)
            raise

    @log_function_call(logger)
    def __register_user_proxy_agent(self):
        """Register the user proxy agent."""
        logger.debug("Registering user proxy agent")
        try:
            contextual_assistant = self.agent_context_wrapper(autogen.AssistantAgent)
            self.user_proxy_agent = contextual_assistant(
                llm_config=self.llm_config,
                name="user_proxy_agent",
                system_message=user_proxy_agent_prompt.system_prompt,
                description="Proxies user questions to the legal paralegal system.",
                human_input_mode="NEVER",
                max_consecutive_auto_reply=20,
                code_execution_config=False,
            )
            logger.info("Successfully registered user proxy agent")
        except Exception as e:
            logger.error(f"Failed to register user proxy agent: {str(e)}", exc_info=True)
            raise

    @log_function_call(logger)
    def __register_all_agents(self):
        """Register all agents."""
        logger.info("Registering all agents")
        try:
            # Register main legal agent first
            self.__register_legal_paralegal_agent()
            
            # Tax domain agents
            self.__register_tax_paralegal_agent()
            self.__register_question_formulation_agent()
            self.__register_information_retrieval_agent()
            self.__register_response_agent()
            
            # User proxy agent
            self.__register_user_proxy_agent()
            
            logger.info("Successfully registered all agents")
        except Exception as e:
            logger.error(f"Failed to register all agents: {str(e)}", exc_info=True)
            raise

    @log_function_call(logger)
    def __update_chat_history(self, new_message: dict):
        """Update the chat_history in context_variables with the new message."""
        logger.debug("Updating chat history")
        if "chat_history" not in self.context_variables:
            self.context_variables["chat_history"] = deque(maxlen=self.MAX_MESSAGES)
        self.context_variables["chat_history"].append(new_message)

    @log_function_call(logger)
    def __create_error_response(self, question, error_msg):
        """Create standardized error response."""
        logger.error(f"Creating error response: {error_msg}")
        return AgentResponse(
            message=f"I apologize, but I encountered an error processing your question: {error_msg}",
            agent_history={"error": error_msg}
        )

    async def __setup_group_chat(self):
        """Set up the group chat with allowed transitions between agents."""
        logger.debug("Setting up group chat")
        allowed_transitions = {
            self.user_proxy_agent: [self.legal_paralegal_agent,self.response_agent],
            self.legal_paralegal_agent: [self.tax_paralegal_agent],  # Add other domain agents here
            self.tax_paralegal_agent: [self.question_formulation_agent],
            self.question_formulation_agent: [self.information_retrieval_agent],
            self.information_retrieval_agent: [self.response_agent],
            self.response_agent: [self.user_proxy_agent],
        }

        def custom_speaker_selection(last_speaker: autogen.Agent, groupchat: autogen.GroupChat):
            message = groupchat.messages[-1]
            try:
                next_speaker_mapping = {
                    "user_proxy_agent": self.user_proxy_agent,
                    "legal_paralegal_agent": self.legal_paralegal_agent,
                    "tax_paralegal_agent": self.tax_paralegal_agent,
                    "question_formulation_agent": self.question_formulation_agent,
                    "information_retrieval_agent": self.information_retrieval_agent,
                    "response_agent": self.response_agent,
                }
                
                # Log the received message to help with debugging
                logger.debug(f"Received message content: {message.get('content', '')}")
                
                # Try to extract next_speaker from message content
                content = message.get("content", "{}")
                # Check if it's already a JSON object
                if isinstance(content, dict) and "next_speaker" in content:
                    next_speaker = content.get("next_speaker")
                    if next_speaker in next_speaker_mapping:
                        return next_speaker_mapping[next_speaker]
                    return "auto"
                
                # Try to parse as JSON
                try:
                    data = json.loads(content)
                    if isinstance(data, dict):
                        if "next_speaker" in data:
                            next_speaker = data.get("next_speaker")
                            if next_speaker in next_speaker_mapping:
                                return next_speaker_mapping[next_speaker]
                        elif isinstance(data.get("userquery"), dict):
                            # Create an IndividualAgentResponse from the data
                            response_obj = IndividualAgentResponse(**data)
                            next_speaker = response_obj.next_speaker
                            if next_speaker in next_speaker_mapping:
                                return next_speaker_mapping[next_speaker]
                except (json.JSONDecodeError, TypeError) as e:
                    # Log parsing errors for debugging
                    logger.warning(f"Error parsing message as JSON: {str(e)}")
                    # If the content isn't JSON or can't be parsed, handle manually
                    if "Question Formulation" in message.get("content", ""):
                        return self.question_formulation_agent
                    elif "Information Retrieval" in message.get("content", ""):
                        return self.information_retrieval_agent
                    elif "Response Agent" in message.get("content", ""):
                        return self.response_agent
            except Exception as e:
                logger.error(f"Error in custom speaker selection: {e}")
            
            # Default to auto selection if we can't determine the next speaker
            return "auto"

        group_chat = autogen.GroupChat(
            agents=list(allowed_transitions.keys()),
            messages=[],
            allowed_or_disallowed_speaker_transitions=allowed_transitions,
            speaker_transitions_type="allowed",
            speaker_selection_method=custom_speaker_selection,
            max_round=50,
        )
        return group_chat

    async def __setup_chat_manager(self, group_chat):
        """Set up the group chat manager."""
        logger.debug("Setting up chat manager")
        manager = autogen.GroupChatManager(
            groupchat=group_chat,
            is_termination_msg=lambda x: x.get("content", "").find("TERMINATE") >= 0,
            llm_config=self.llm_config,
            human_input_mode="NEVER",
            max_consecutive_auto_reply=20,
            system_message="Coordinate the conversation between legal domain agents to answer user's questions.",
            code_execution_config=False,
        )
        return manager

    def __format_query_for_agent(self, query: str) -> dict:
        """Format the user query into IndividualAgentUserQuery structure."""
        user_query = IndividualAgentUserQuery(
            query=query,
            workplan="Will be filled by the legal paralegal agent"
        )
        
        initial_message = {
            "userquery": user_query.model_dump(),
            "query_solved": False,
            "proposed_solve": "",
            "next_speaker": "legal_paralegal_agent",
            "next_speaker_question": f"Please analyze this legal question: {query}"
        }
        
        return initial_message

    async def ask_legal_paralegal(self, query: str) -> Union[str, AgentResponse]:
        """
        Entry point for legal paralegal service using Autogen for orchestration.

        Args:
            query: The user's legal question.

        Returns:
            A comprehensive legal response.
        """
        logger.info(f"Processing legal query: {query}")
        try:
            # Register all agents
            self.__register_all_agents()
            
            # Set up group chat and manager
            group_chat = await self.__setup_group_chat()
            manager = await self.__setup_chat_manager(group_chat)
            
            # Format the query into IndividualAgentUserQuery structure
            formatted_query = self.__format_query_for_agent(query)
            
            # Start or resume conversation
            if not self.context_variables.get("session_established"):
                logger.info("Starting new chat session")
                await self.user_proxy_agent.a_initiate_chat(
                    manager, message=json.dumps(formatted_query), clear_history=False
                )
                self.context_variables["session_established"] = True
            else:
                logger.info("Resuming chat session")
                prev_messages = list(self.context_variables.get("chat_history", []))
                flattened_list = [item for sublist in prev_messages for item in sublist]
                if len(flattened_list) > 2000:
                    flattened_list = flattened_list[-1000:]
                last_agent, last_message = manager.resume(messages=flattened_list)
                await self.user_proxy_agent.a_initiate_chat(
                    manager,
                    message=json.dumps(formatted_query),
                    clear_history=False,
                )
            
            # Update chat history
            self.__update_chat_history(group_chat.messages)
            autogen.runtime_logging.stop()
            
            # Extract the final response
            response_messages = [m for m in group_chat.messages if m.get("name") == "response_agent"]
            if response_messages:
                try:
                    # response_content = json.loads(response_messages[-1]["content"])
                    response_content = response_messages[-1]["content"]
                    client = genai.Client(api_key=settings.GEMENI_API_KEY)
                    response = client.models.generate_content(
                        model='gemini-2.0-flash',
                        contents=f'format the content according to the provided response_schema + {response_content}',
                        config={
                            'response_mime_type': 'application/json',
                            'response_schema': IndividualAgentResponse,
                        },
                    )

                    return AgentResponse(
                        message=response.parsed.proposed_solve,
                        agent_history={"data": group_chat.messages}
                    )

                  
                except json.JSONDecodeError:
                    return AgentResponse(
                        message=response_messages[-1]["content"],
                        agent_history={"data": group_chat.messages}
                    )
            
            return AgentResponse(
                message="I couldn't process your legal question. Please try again with more details.",
                agent_history={"data": group_chat.messages}
            )
            
        except Exception as e:
            logger.error(f"Error in ask_legal_paralegal: {str(e)}", exc_info=True)
            return self.__create_error_response(query, str(e))
  
    
# Create a singleton instance
legal_paralegal = LegalParalegal()

