from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.core.config import settings
from backend.routers import post, job
from backend.db.database import create_tables
from langgraph.graph import StateGraph
from langgraph.types import RunnableConfig
from post_generator_agent import graph as post_generator_graph, PostGeneratorState
from supervisor import graph as supervisor_graph, SupervisorState
from langchain_core.messages import HumanMessage, AIMessageChunk
from rich.console import Console
from rich.panel import Panel

load_dotenv()

# Import all models to ensure they are registered with SQLAlchemy
from backend.models.job import PostJob
from backend.models.post import Post, PostNode
create_tables()
app = FastAPI(
    title="Supervisor",
    description="api to generate posts",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(post.router, prefix=settings.API_PREFIX)
app.include_router(job.router, prefix=settings.API_PREFIX)

def get_responsive_width(console: Console) -> int:
    """Get responsive width with margins for panels."""
    return min(120, console.size.width - 4) if console.size.width > 10 else 80


async def run_graph_once(
        input: SupervisorState,
        graph: StateGraph,
        console: Console,
        **kwargs
):
    """Run the graph once without streaming."""
    result = await graph.ainvoke(input=input, **kwargs)

    # Display final messages in panels
    AGENT_STYLES = {
        'PostGenerator': {'color': 'blue', 'emoji': '🚀', 'name': 'Post Generator'},
        'researcher': {'color': 'cyan', 'emoji': '🔬', 'name': 'Researcher'},
        'copywriter': {'color': 'magenta', 'emoji': '✍️', 'name': 'Copywriter'},
        'supervisor': {'color': 'green', 'emoji': '🎯', 'name': 'Supervisor'},
    }

    for message in result.get("messages", []):
        if hasattr(message, "name") and message.name in AGENT_STYLES:
            style = AGENT_STYLES[message.name]
        else:
            style = AGENT_STYLES["supervisor"]

        panel = Panel(
            message.content.strip(),
            title=f"{style['emoji']} {style['name']}",
            border_style=style['color'],
            title_align="left",
            padding=(1, 2),
            width=get_responsive_width(console)
        )
        console.print(panel)
        console.print()


async def stream_graph_responses(
        input: SupervisorState,
        graph: StateGraph,
        console: Console,
        **kwargs
):
    """Asynchronously stream the result of the graph run with subgraph support.

    Args:
        input: The input to the graph.
        graph: The compiled graph.
        console: Rich console for output.
        **kwargs: Additional keyword arguments.

    Returns:
        str: The final LLM or tool call response
    """
    # Agent styling configuration
    AGENT_STYLES = {
        'PostGenerator': {'color': 'blue', 'emoji': '🚀', 'name': 'Post Generator'},
        'researcher': {'color': 'cyan', 'emoji': '🔬', 'name': 'Researcher'},
        'copywriter': {'color': 'magenta', 'emoji': '✍️', 'name': 'Copywriter'},
        'supervisor': {'color': 'green', 'emoji': '🎯', 'name': 'Supervisor'},
    }

    # Track current AI message source to detect transitions
    current_ai_source = None
    current_content = ""
    current_tool_args = ""
    current_tool_name = ""

    async for chunk in graph.astream(
            input=input,
            stream_mode="messages",
            subgraphs=True,
            **kwargs
    ):
        # When subgraphs=True, the structure is (namespace, (message_chunk, metadata))
        namespace, (message_chunk, _) = chunk

        if isinstance(message_chunk, AIMessageChunk):
            # Determine the source of this AI message directly from namespace
            if namespace:
                # This is from a subgraph - detect agent from namespace
                namespace_str = str(namespace)
                if "call_researcher" in namespace_str:
                    ai_source = "researcher"
                elif "call_copywriter" in namespace_str:
                    ai_source = "copywriter"
                else:
                    # Fallback for unknown subgraphs
                    ai_source = "researcher"
            else:
                # This is from the main graph (supervisor)
                ai_source = "supervisor"

            # Check if we're transitioning between different AI sources
            if current_ai_source != ai_source:
                # Finalize previous agent's content in a panel
                if current_content.strip() and current_ai_source:
                    style = AGENT_STYLES[current_ai_source]
                    panel = Panel(
                        current_content.strip(),
                        title=f"{style['emoji']} {style['name']}",
                        border_style=style['color'],
                        title_align="left",
                        padding=(1, 2),
                        width=get_responsive_width(console)
                    )
                    console.print(panel)
                    console.print()  # Add spacing after completed panel

                # Start new agent
                current_ai_source = ai_source
                current_content = ""
            elif current_ai_source is None:
                # First AI message
                current_ai_source = ai_source
                current_content = ""

            # Handle tool calls
            if message_chunk.response_metadata:
                finish_reason = message_chunk.response_metadata.get("finish_reason", "")
                if finish_reason == "tool_calls":
                    # Print accumulated tool args if we have them
                    if current_tool_args.strip():
                        if current_ai_source:
                            style = AGENT_STYLES[current_ai_source]
                            console.print(f"  [dim {style['color']}]{current_tool_args.strip()}[/dim {style['color']}]")
                        else:
                            console.print(f"  [dim]{current_tool_args.strip()}[/dim]")
                        current_tool_args = ""
                    console.print("  🔧 [yellow]Tool call completed[/yellow]")
                    console.print()  # Add spacing after tool completion

            if message_chunk.tool_call_chunks:
                tool_chunk = message_chunk.tool_call_chunks[0]
                tool_name = tool_chunk.get("name", "")
                args = tool_chunk.get("args", "")

                if tool_name and tool_name != current_tool_name:
                    # New tool call - print the name
                    console.print(f"  🔧 [yellow]TOOL CALL: {tool_name}[/yellow]")
                    current_tool_name = tool_name
                    current_tool_args = ""  # Reset args for new tool

                if args:
                    # Accumulate args instead of printing immediately
                    current_tool_args += args
            else:
                # Just accumulate content for panel display
                if message_chunk.content:
                    current_content += message_chunk.content
        else:
            # Handle other message types
            pass

    # Print any remaining tool args
    if current_tool_args.strip():
        if current_ai_source:
            style = AGENT_STYLES[current_ai_source]
            console.print(f"  [dim {style['color']}]{current_tool_args.strip()}[/dim {style['color']}]")
        else:
            console.print(f"  [dim]{current_tool_args.strip()}[/dim]")
        console.print()

    # Finalize the last agent's content in a panel
    if current_content.strip() and current_ai_source:
        style = AGENT_STYLES[current_ai_source]
        panel = Panel(
            current_content.strip(),
            title=f"{style['emoji']} {style['name']}",
            border_style=style['color'],
            title_align="left",
            padding=(1, 2),
            width=get_responsive_width(console)
        )
        console.print(panel)
        console.print()  # Add spacing after final panel


async def main():
    """Main function to run the supervisor with subgraphs."""
    # Create console without fixed width - let it be responsive
    console = Console()

    try:
        config = RunnableConfig(configurable={
            "thread_id": "1",
            "recursion_limit": 50,
        })

        # Welcome panel with responsive width
        welcome_panel = Panel(
            "Multi-Agent Interactive Post Generator\nType 'exit' or 'quit' to stop\n\nRequest an interactive post on any theme!",
            title="Social Media Content Creator",
            border_style="blue",
            title_align="center",
            padding=(1, 2),  # Add padding to welcome panel
            width=get_responsive_width(console)
        )
        console.print(welcome_panel)
        console.print()  # Add spacing after welcome

        while True:
            console.print()
            user_input = console.input("[bold blue]User:[/bold blue] ")
            console.print()  # Add spacing after user input

            if user_input.lower() in ["exit", "quit"]:
                console.print("\n[yellow]Exit command received. Goodbye! 👋[/yellow]\n")
                break

            # Use PostGenerator as the main entry point
            graph_input = PostGeneratorState(
                messages=[HumanMessage(content=user_input)]
            )

            # await stream_graph_responses(graph_input, post_generator_graph, console, config=config)
            await run_graph_once(graph_input, post_generator_graph, console, config=config)
    except Exception as e:
        console.print(f"[red]Error: {type(e).__name__}: {str(e)}[/red]")
        raise


if __name__ == "__main__":
    import asyncio
    import nest_asyncio
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    #
    # nest_asyncio.apply()
    # asyncio.run(main())

# Example prompts
# write a linkedin post on the top AI tools that small businesses and entrepreneurs need to be using to scale their businesses. include real-world examples and case studies where businesses are using these tools to scale their business with real numbers. include a call to action at the end for readers to follow me for more actionable playbooks on how to generate real value for their business.