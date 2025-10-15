# Interactive Post Creation Workflow

This document explains the new interactive workflow for creating social media posts with user path selection.

## System Architecture

### Agent Roles

1. **PostGenerator Agent** 🚀
   - **Main Entry Point**: Receives user input about topics
   - **Mission**: Orchestrates the entire process
   - **Interaction**: Communicates only with Supervisor
   - **Tools**: `start_post_creation_process`, `handle_user_path_selection`, `finalize_post_generation`

2. **Supervisor Agent** 🎯
   - **Mission**: Manages research and content creation team
   - **Interaction**: Works with Researcher and Copywriter
   - **Status**: Works fine (no changes needed)

3. **Researcher Agent** 🔬
   - **Mission**: Gathers comprehensive information
   - **Interaction**: Works through Supervisor
   - **Status**: Works fine (no changes needed)

4. **Copywriter Agent** ✍️
   - **Mission**: Creates content and presents path options to users
   - **Interaction**: Works through Supervisor
   - **New Feature**: Presents options and waits for user choice
   - **Tools**: `present_path_options` (new), `generate_linkedin_post`, `generate_blog_post`

## Interactive Workflow

### Step 1: User Input
```
User: "Create a LinkedIn post about remote work productivity"
```

### Step 2: PostGenerator Starts Process
```
PostGenerator → start_post_creation_process(topic="remote work productivity")
PostGenerator → call_supervisor()
```

### Step 3: Supervisor Coordinates Research
```
Supervisor → coordinates with Researcher
Researcher → gathers information about remote work productivity
Supervisor → coordinates with Copywriter
```

### Step 4: Copywriter Presents Options
```
Copywriter → present_path_options([
    "Focus on productivity tools and apps",
    "Emphasize work-life balance strategies", 
    "Target managers and team leaders",
    "Lead with statistics and data"
])
System → WAITS for user choice
```

### Step 5: User Selects Path
```
User: "I choose option 2: Emphasize work-life balance strategies"
PostGenerator → handle_user_path_selection(chosen_path="work-life balance strategies")
PostGenerator → call_supervisor() (with chosen path)
```

### Step 6: Copywriter Creates Content
```
Copywriter → creates content based on chosen path
Copywriter → may present more options if needed
System → continues until post is complete
```

### Step 7: Finalization
```
PostGenerator → finalize_post_generation(post_id)
System → Post complete!
```

## Key Changes Made

### 1. PostGenerator Agent
- **New Mission**: Main orchestrator that gets user input
- **Communication**: Only with Supervisor (no direct Copywriter interaction)
- **Tools**: Updated to handle path selection and process management
- **State**: Tracks topic, chosen paths, and waiting status

### 2. Copywriter Agent
- **New Role**: Presents path options and waits for user choice
- **New Tool**: `present_path_options` for user interaction
- **Process**: Creates content based on user-selected paths
- **Behavior**: Waits for user input before continuing

### 3. Removed "Theme" Keyword
- **Replaced**: All instances of "theme" with "topic"
- **Updated**: Database models, schemas, and API endpoints
- **Consistent**: Throughout the entire system

### 4. Interactive Flow
- **User Choice**: System waits for user path selection
- **Dynamic Content**: Content adapts based on user choices
- **Multiple Iterations**: Can present multiple choice points
- **Completion**: Stops when user is satisfied with the post

## Example Usage

### Via Main Interface
```bash
python main.py

# User: "Create a blog post about AI tools for small businesses"
# System: Presents options like:
#   1. Focus on free/low-cost tools
#   2. Target specific industries
#   3. Emphasize implementation challenges
#   4. Lead with success stories

# User: "I choose option 1"
# System: Continues creating content focused on free/low-cost tools
# System: May present more options or complete the post
```

### Via API
```bash
curl -X POST "http://localhost:8000/api/posts/create" \
     -H "Content-Type: application/json" \
     -d '{"topic": "How to choose the right marketing strategy"}'
```

## Benefits of New System

1. **User Control**: Users can guide the content creation process
2. **Personalized Content**: Content adapts to user preferences
3. **Interactive Experience**: Engaging process with multiple choice points
4. **Quality Assurance**: Users can ensure content meets their needs
5. **Flexible Flow**: Can handle simple or complex content creation

## Technical Implementation

### State Management
- **PostGeneratorState**: Tracks topic, chosen paths, waiting status
- **User Interaction**: System pauses for user input when needed
- **Path Continuation**: Resumes process with chosen path

### Tool Integration
- **present_path_options**: Formats and displays choices to user
- **handle_user_path_selection**: Processes user choice and continues
- **start_post_creation_process**: Initiates the entire workflow

### Error Handling
- **Fallback**: Direct generation if multi-agent system fails
- **Validation**: Ensures user choices are valid
- **Recovery**: Can restart process if needed

This new system provides a much more interactive and user-controlled experience for creating social media posts, while maintaining the robust multi-agent architecture you already had in place.
