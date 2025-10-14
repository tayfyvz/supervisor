from sqlalchemy.orm import Session

from backend.core.models import PostLLMResponse, PostNodeLLM
from config import settings

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from backend.models.post import Post

class PostGenerator:

    @classmethod
    def generate_post(cls, db: Session, session_id: str) -> Post:

        post_parser = PydanticOutputParser(pydantic_object=PostLLMResponse)
        prompt = ChatPromptTemplate.from_messages([

        ])