import operator
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from typing import Annotated
from langchain_core.messages import SystemMessage, ToolMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, add_messages, END
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool, InjectedToolCallId
from langgraph.checkpoint.memory import MemorySaver
from datetime import datetime
from supervisor import graph as supervisor_graph
from langgraph.types import Command, RunnableConfig

load_dotenv()

# Load the post generator system prompt
post_generator_prompt = open("prompts/post_generator_agent.md", "r").read()


class PostGeneratorState(BaseModel):
    """The state of the post generator agent.
    
    This agent is the main orchestrator for creating social media posts interactively.
    It gets user input and communicates with the Supervisor to start the process.
    """
    messages: Annotated[list, add_messages] = []
    topic: str | None = None
    post_id: int | None = None
    research_reports: Annotated[list, operator.add] = []
    current_options: list = []
    waiting_for_user_choice: bool = False
    chosen_path: str | None = None
    final_content: str | None = None


@tool
async def start_post_creation_process(
        topic: str,
        tool_call_id: Annotated[str, InjectedToolCallId],
):
    """Start the post creation process by communicating with the Supervisor.
    
    Args:
        topic: The detailed or general topic for the social media post.
    """
    # Store the topic in state for the supervisor to use
    update = {
        "topic": topic,
        "messages": [ToolMessage(
            name="start_post_creation_process",
            content=f"Starting post creation process for topic: {topic}",
            tool_call_id=tool_call_id,
        )],
    }
    
    return Command(
        goto="call_supervisor",
        update=update
    )


@tool
async def handle_user_path_selection(
        chosen_path: str,
        tool_call_id: Annotated[str, InjectedToolCallId],
):
    """Handle user's path selection and continue the post creation process.
    
    Args:
        chosen_path: The path option chosen by the user.
    """
    update = {
        "chosen_path": chosen_path,
        "waiting_for_user_choice": False,
        "messages": [ToolMessage(
            name="handle_user_path_selection",
            content=f"User selected path: {chosen_path}. Continuing post creation...",
            tool_call_id=tool_call_id,
        )],
    }
    
    return Command(
        goto="call_supervisor",
        update=update
    )


@tool
async def finalize_post_generation(
        post_id: int,
        tool_call_id: Annotated[str, InjectedToolCallId],
):
    """Finalize the post generation process.
    
    Args:
        post_id: The ID of the generated post.
    """
    update = {
        "post_id": post_id,
        "final_content": f"Post completed with ID: {post_id}",
        "messages": [ToolMessage(
            name="finalize_post_generation",
            content=f"Post generation completed! Post ID: {post_id}",
            tool_call_id=tool_call_id,
        )],
    }
    
    return Command(
        goto=END,
        update=update
    )


async def call_supervisor(state: PostGeneratorState, config: RunnableConfig):
    """Call the supervisor agent to coordinate research and content creation."""
    # Create a task description for the supervisor
    if state.chosen_path:
        # Continue with the chosen path
        task_description = f"""Continue creating the social media post for topic: "{state.topic}"

The user has chosen the following path: "{state.chosen_path}"

Please coordinate with the copywriter to continue the post creation process with this chosen path. The copywriter should:
1. Review the research reports
2. Continue creating content based on the user's chosen path
3. If more options are needed, present them to the user
4. If the post is complete, finalize it

Current research reports available: {len(state.research_reports)}"""
    else:
        # Start the process
        task_description = f"""Create a social media post (LinkedIn/Blog) for the topic: "{state.topic}"

Please coordinate the research and content creation process:
1. Break down the topic into research tasks
2. Have the researcher gather comprehensive information
3. Have the copywriter start creating the post and present path options to the user

The copywriter should create content that allows users to choose different paths for how the post should flow. Present options to the user and wait for their choice before continuing."""

    supervisor_response = await supervisor_graph.ainvoke(
        input={
            "messages": [HumanMessage(content=task_description)],
            "research_reports": state.research_reports,
        },
        config=config,
    )

    # Extract any research reports from the supervisor's response
    research_reports = supervisor_response.get("research_reports", [])
    
    ai_message = AIMessage(
        name="supervisor", 
        content=f"Supervisor completed coordination for topic: {state.topic}. Research reports: {len(research_reports)} found."
    )

    return {
        "research_reports": research_reports,
        "messages": [ai_message],
    }




llm = ChatOpenAI(
    name="PostGenerator",
    model="gpt-5-mini-2025-08-07",
    reasoning_effort="low",
)

tools = [
    start_post_creation_process,
    handle_user_path_selection,
    finalize_post_generation,
]
llm_with_tools = llm.bind_tools(tools, parallel_tool_calls=False)


async def post_generator(state: PostGeneratorState):
    """The main post generator agent."""
    response = llm_with_tools.invoke([
        SystemMessage(
            content=post_generator_prompt.format(current_datetime=datetime.now())
        )
    ] + state.messages)
    return {"messages": [response]}


async def post_generator_router(state: PostGeneratorState) -> str:
    """Route based on the post generator's decisions."""
    if state.messages[-1].tool_calls:
        return "tools"
    return END


builder = StateGraph(PostGeneratorState)

builder.add_node(post_generator)
builder.add_node("tools", ToolNode(tools))
builder.add_node(call_supervisor)

builder.set_entry_point("post_generator")

builder.add_conditional_edges(
    "post_generator",
    post_generator_router,
    {
        "tools": "tools",
        END: END,
    }
)

# Add edges for the tool-based routing
builder.add_edge("call_supervisor", "post_generator")

graph = builder.compile(checkpointer=MemorySaver())

# Visualize the graph
# from IPython.display import Image
# Image(graph.get_graph(xray=True).draw_mermaid_png())
# print(graph.get_graph(xray=True).draw_mermaid())
