from sqlalchemy.orm import Session

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from backend.core.models import PostLLMResponse, PostNodeLLM
from backend.models.post import Post, PostNode
from dotenv import load_dotenv

load_dotenv()

class PostGenerator:

    @classmethod
    def _get_llm(cls):
        return ChatOpenAI(
            name="Post Generator",
            model="gpt-5-mini-2025-08-07",
            reasoning_effort="minimal",
        )

    @classmethod
    def generate_post(cls, db: Session, session_id: str, topic: str = "social media content") -> Post:
        """Generate an interactive post using the multi-agent system."""
        # Import here to avoid circular imports
        from post_generator_agent import graph as post_generator_graph, PostGeneratorState
        from langchain_core.messages import HumanMessage
        from langgraph.types import RunnableConfig
        import asyncio
        
        # Create the input for the post generator agent
        agent_input = PostGeneratorState(
            messages=[HumanMessage(content=f"Create a social media post with topic: {topic}")]
        )
        
        # Configure the agent run
        config = RunnableConfig(configurable={
            "thread_id": f"post_gen_{session_id}",
            "recursion_limit": 50,
        })
        
        # Run the multi-agent system
        async def run_agents():
            return await post_generator_graph.ainvoke(agent_input, config=config)
        
        # Execute the async function
        result = asyncio.run(run_agents())
        
        # Extract the final content from the agent response
        final_content = result.get("final_content")
        if not final_content:
            # Fallback to direct generation if agent system doesn't provide content
            return cls._generate_post_directly(db, session_id, topic)
        
        # Parse and store the generated content
        return cls._store_generated_post(db, session_id, final_content)

    @classmethod
    def _generate_post_directly(cls, db: Session, session_id: str, topic: str) -> Post:
        """Fallback method for direct post generation without multi-agent system."""
        llm = cls._get_llm()
        post_parser = PydanticOutputParser(pydantic_object=PostLLMResponse)

        # Load the post generation prompt
        post_prompt = cls._get_post_prompt()

        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                post_prompt
            ),
            (
                "human",
                f"Create a post with this topic: {topic}"
            )
        ]).partial(format_instructions=post_parser.get_format_instructions())

        raw_response = llm.invoke(prompt.invoke({}))

        response_text = raw_response
        if hasattr(raw_response, "content"):
            response_text = raw_response.content

        post_structure = post_parser.parse(response_text)
        return cls._store_generated_post(db, session_id, post_structure)

    @classmethod
    def _store_generated_post(cls, db: Session, session_id: str, post_data) -> Post:
        """Store the generated post data in the database."""
        if isinstance(post_data, str):
            # If it's a string, try to parse it as JSON
            import json
            post_data = json.loads(post_data)
        
        if not isinstance(post_data, dict):
            raise ValueError("Invalid post data format")

        post_db = Post(title=post_data.get("title", "Generated Post"), session_id=session_id)
        db.add(post_db)
        db.flush()

        root_node_data = post_data.get("rootNode", {})
        if isinstance(root_node_data, dict):
            root_node_data = PostNodeLLM.model_validate(root_node_data)

        cls._process_post_node(db, post_db.id, root_node_data, is_root=True)

        db.commit()
        return post_db

    @classmethod
    def _process_post_node(cls, db: Session, post_id: int, node_data: PostNodeLLM, is_root: bool = False) -> PostNode:
        node = PostNode(
            post_id=post_id,
            content=node_data.content if hasattr(node_data, "content") else node_data["content"],
            is_root=is_root,
            is_ending=node_data.isEnding if hasattr(node_data, "isEnding") else node_data["isEnding"],
            options=[]
        )
        db.add(node)
        db.flush()

        if not node.is_ending and (hasattr(node_data, "options") and node_data.options):
            options_list = []
            for option_data in node_data.options:
                next_node = option_data.nextNode

                if isinstance(next_node, dict):
                    next_node = PostNodeLLM.model_validate(next_node)

                child_node = cls._process_post_node(db, post_id, next_node, False)

                options_list.append({
                    "text": option_data.text,
                    "node_id": child_node.id
                })

            node.options = options_list

        db.flush()
        return node

    @classmethod
    def _get_post_prompt(cls) -> str:
        """Load the post generation prompt from prompts directory"""
        try:
            with open("prompts/post_generator.md", "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            # Fallback prompt if file doesn't exist
            return """
You are a creative content generator that creates interactive social media posts with multiple engagement paths.

Create a post with multiple options that users can choose from, similar to a choose-your-own-adventure format.

The post should have:
- A compelling title
- A root node with engaging content
- Multiple options that lead to different paths
- Some paths should lead to ending nodes
- The content should be engaging and encourage user interaction

Format your response according to the provided schema.
"""
