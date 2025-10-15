# Backend Implementation Guide

This document explains the backend implementation that brings choose-your-own-adventure style functionality to your social media content generator.

## Overview

The backend has been implemented following the same pattern as your Choose-Your-Own-Adventure-AI project, adapted for social media content generation. It includes:

1. **PostGenerator**: Similar to StoryGenerator, creates hierarchical interactive content
2. **Database Models**: Support for posts with multiple nodes and options
3. **API Endpoints**: RESTful API for creating and navigating interactive posts
4. **Integration**: Seamless integration with your existing supervisor system

## Architecture

### Core Components

- `backend/core/post_generator.py`: Main post generation logic
- `backend/models/post.py`: Database models for posts and nodes
- `backend/schemas/post.py`: Pydantic schemas for API responses
- `backend/routers/post.py`: FastAPI routes for post management

### Database Structure

```
Post (id, title, session_id, created_at)
  └── PostNode (id, post_id, content, is_root, is_ending, options, created_at)
```

Each post contains multiple nodes connected through options, creating a tree structure.

## API Endpoints

### Posts

- `GET /api/posts/` - List all posts
- `POST /api/posts/create` - Create a new interactive post (async)
- `GET /api/posts/{post_id}/complete` - Get complete post tree
- `GET /api/posts/nodes/{node_id}` - Get specific node

### Jobs

- `GET /api/jobs/{job_id}` - Check post generation status

## Usage Examples

### 1. Creating an Interactive Post

```bash
# Start the server
uvicorn main:app --reload

# Create a post via API
curl -X POST "http://localhost:8000/api/posts/create" \
     -H "Content-Type: application/json" \
     -d '{"theme": "How to choose the right AI tool for your business"}'

# Response includes job_id for tracking
```

### 2. Using the Supervisor System

The copywriter agent now has access to the `generate_interactive_post` tool:

```python
# The copywriter can now create interactive posts
# Example prompt: "Create an interactive guide for choosing AI tools"
# The copywriter will use the generate_interactive_post tool
```

### 3. Navigating Interactive Content

```bash
# Get the complete post structure
curl "http://localhost:8000/api/posts/1/complete"

# Navigate to a specific node
curl "http://localhost:8000/api/posts/nodes/5"
```

## Integration with Existing System

The backend integrates seamlessly with your existing supervisor system:

1. **Researcher**: Continues to research topics as before
2. **Copywriter**: Now has access to `generate_interactive_post` tool
3. **Supervisor**: Can coordinate research and interactive post creation

### Example Workflow

1. User requests: "Create an interactive guide about remote work tools"
2. Supervisor breaks down into research tasks
3. Researcher gathers information about different tool categories
4. Copywriter creates interactive post with multiple paths:
   - "I'm a startup" → Startup-focused tools
   - "I'm enterprise" → Enterprise solutions
   - "I'm freelancer" → Individual tools
   - "I need security" → Security-focused options

## Configuration

### Environment Variables

Make sure your `.env` file includes:

```env
DATABASE_URL=sqlite:///./database.db
OPENAI_API_KEY=your_openai_key
TAVILY_API_KEY=your_tavily_key
```

### Database Setup

The database tables are created automatically when you start the server. For production, consider using PostgreSQL instead of SQLite.

## Key Features

### 1. Hierarchical Content Structure
- Posts can have multiple branches and paths
- Each node can have multiple options
- Users can navigate through different content paths

### 2. Async Post Generation
- Posts are generated in the background
- Job tracking system for monitoring progress
- Error handling and status reporting

### 3. Flexible Content Types
- Works with any theme or topic
- Adapts to different content styles
- Supports both educational and marketing content

### 4. Session Management
- Tracks user sessions
- Maintains post ownership
- Supports multiple concurrent users

## Development Notes

### Adding New Content Types

To add support for new content types (e.g., video scripts, email sequences):

1. Update the prompt in `prompts/post_generator.md`
2. Modify the `PostLLMResponse` schema if needed
3. Add new tools to the copywriter if required

### Customizing the Generation Logic

The `PostGenerator` class follows the same pattern as your StoryGenerator:

- `generate_post()`: Main generation method
- `_process_post_node()`: Recursive node processing
- `_get_llm()`: LLM configuration
- `_get_post_prompt()`: Prompt loading

### Database Migrations

For production deployments, consider using Alembic for database migrations:

```bash
pip install alembic
alembic init alembic
# Configure and run migrations
```

## Testing

### Manual Testing

1. Start the server: `uvicorn main:app --reload`
2. Visit `http://localhost:8000/docs` for interactive API docs
3. Test post creation and navigation

### Example Test Flow

```bash
# 1. Create a post
curl -X POST "http://localhost:8000/api/posts/create" \
     -H "Content-Type: application/json" \
     -d '{"theme": "Guide to social media marketing"}'

# 2. Check job status
curl "http://localhost:8000/api/jobs/{job_id}"

# 3. Get complete post when ready
curl "http://localhost:8000/api/posts/{post_id}/complete"
```

## Next Steps

Consider implementing:

1. **User Authentication**: Add user accounts and post ownership
2. **Analytics**: Track user navigation paths and popular choices
3. **Content Versioning**: Allow editing and version control
4. **Export Options**: Export posts to different formats (Markdown, PDF, etc.)
5. **Template System**: Pre-defined post templates for common use cases

## Troubleshooting

### Common Issues

1. **Database Connection**: Ensure DATABASE_URL is correctly set
2. **OpenAI API**: Verify OPENAI_API_KEY is valid and has sufficient credits
3. **Import Errors**: Make sure all dependencies are installed with `pip install -r requirements.txt`

### Debug Mode

Enable debug mode by setting `DEBUG=True` in your environment variables for more detailed error messages.
