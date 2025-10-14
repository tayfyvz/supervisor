from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class PostOptionLLM(BaseModel):
    text: str = Field(description="the text of the option shown to the user")
    nextNode: Dict[str, Any] = Field(description="the next node content and its options")

class PostNodeLLM(BaseModel):
    content: str = Field(description="the main content of the post node")
    isEnding: bool = Field(description="whether this node is an ending node")
    options: Optional[List[PostOptionLLM]] = Field(default=None, description="the options for this node")

class PostLLMResponse(BaseModel):
    title: str = Field(description="the title of the post")
    rootNode: PostNodeLLM = Field(description="the root node of the post")