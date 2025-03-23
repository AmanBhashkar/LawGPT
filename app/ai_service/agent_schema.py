from pydantic import BaseModel, Field
from typing import Optional, List, Union


class AgentResponse(BaseModel):
    message: str
    action: Optional[List[dict]] = None
    agent_history: Optional[dict] = None


class IndividualAgentUserQuery(BaseModel):
    query: str = Field(description="copy the original user request, without edit into this field. If it has things like 'current_chat':<some_value>, then ignore that and only copy <some_value> part") 
    workplan: str = Field(
        description="Give elaborated summary of what you think the user is asking for. Describe elaborately the workplan of how the answer is going to be generated and which all agents are going to be involved to get final answer. Always include sam_agent as your final agent to check the final answer. No other agents except orchestrator should edit this workplan"
    )


class IndividualAgentResponse(BaseModel):
    userquery: IndividualAgentUserQuery
    query_solved: bool = Field(
        description="true if an answer is proposed by one of the agents and the proposed_solve actually addresses the question"
    )
    proposed_solve: str = Field(
        description="""A Text string used by Agents to propose an answer to the user query.If necessary this should include questions that can be asked to the user. Orchestration agent should never populate this value, and this should only be populated by other agents. This can include questions that can be asked to the user to get more information.
     """
    )
    next_speaker: str = Field(
        description="Name of one of the agents who should speak next in order to answer the user's question. This selection should be strictly abided to the workplan. If no other agent should speak, this should go to sam_agent."
    )
    next_speaker_question: str = Field(
        description="Instructions to the next speaker on what needs to be done to answer the user's questions"
    )


class PayloadData(BaseModel):
    """
    Represents the payload data structure for form updates.
    """
    propertyName: str = Field(..., description="The name of the property to update")
    value: str | int | bool = Field(..., description="The value to store")
    table: str = Field(..., description="The table name where the data should be stored")
    application_id: int | None = Field(None, description="The ID of the current application")
    user_id: int | None = Field(None, description="The ID of the user")

    @classmethod
    def create_payload(
        cls, data: Union[dict, BaseModel],
        application_id: int | None = None,
        user_id: int | None = None
    ) -> "PayloadData":
        """
        Factory method to create a PayloadData instance with optional ID updates.
        Automatically converts a BaseModel instance to a dictionary and unwraps a nested 'payload' key if needed.
        """
        if isinstance(data, BaseModel):
            data = data.model_dump()
        # Unwrap nested payload if present
        if "payload" in data and isinstance(data["payload"], dict):
            data = data["payload"]
        payload = cls(**data)
        if application_id is not None:
            payload.application_id = application_id
        if user_id is not None:
            payload.user_id = user_id
        return payload
