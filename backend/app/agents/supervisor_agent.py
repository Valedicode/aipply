"""
Supervisor Agent - Orchestration Hub for Multi-Agent System

This agent manages the overall workflow:
1. Routes user requests to appropriate specialized agents
2. Manages CV and Job agents as tools (tool calling pattern)
3. Hands off to Writer agent for extended refinement sessions
4. Maintains conversation state and context
5. Handles clarification loops for CV extraction

Architecture:
- CV Agent: Tool calling (with supervisor-managed clarifications)
- Job Agent: Tool calling (data extraction)
- Writer Agent: Hand-off (extended collaborative session)
"""

from typing import TypedDict, Annotated, Literal
from operator import add
from pathlib import Path
import json

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# Import specialized agents
from .cv_agent import (
    agent as cv_agent,
    extract_resume_info,
    identify_ambiguities,
    update_resume_with_clarifications
)
from .job_agent import (
    agent as job_agent,
    retrieve_web,
    retrieve_text,
    collect_company_info
)
# Lazy import writer_agent to avoid WeasyPrint dependency issues on startup
# writer_agent will be imported when needed in handoff_to_writer function

import dotenv
dotenv.load_dotenv()

# ============================================
# State Definition
# ============================================

class SupervisorState(TypedDict):
    """
    Comprehensive state for supervisor orchestration.
    
    This state tracks:
    - Conversation history and context
    - Data from specialized agents
    - Routing and control flow
    - Clarification management
    """
    # Conversation
    messages: Annotated[list[dict], add]  # Full conversation history
    user_input: str                        # Current user message
    supervisor_response: str               # Current supervisor response
    
    # Routing & Control
    current_agent: str                     # "supervisor", "writer", "cv", "job"
    next_action: str                       # Next step to take
    intent: str                            # User's detected intent
    
    # Data Storage (from specialized agents)
    cv_data: str | None                    # JSON from CV agent
    cv_file_path: str | None               # Path to CV file
    job_data: str | None                   # JSON from Job agent
    company_data: str | None               # Optional company research
    
    # CV Clarification Management
    pending_questions: str | None          # Questions awaiting user response
    clarifications: str | None             # User's clarification responses
    needs_clarification: bool              # Flag for clarification loop
    
    # Session Metadata
    session_stage: str                     # "init", "collecting_cv", "collecting_job", "writer_session", "complete"
    conversation_count: int                # Number of exchanges
    ready_for_writer: bool                 # Both CV and job data ready


# ============================================
# Intent Analysis
# ============================================

class UserIntent(BaseModel):
    """Structured output for intent classification."""
    intent: Literal[
        "upload_cv",           # User wants to provide CV
        "provide_job_url",     # User has job posting URL
        "provide_job_text",    # User has job description text
        "research_company",    # User wants company research
        "start_tailoring",     # Ready to tailor CV
        "answer_clarification",# Answering CV questions
        "general_question",    # General inquiry
        "greeting",            # Hello/Hi
        "help"                 # Asking for help
    ]
    reasoning: str
    requires_data: bool  # Does this intent need CV/job data?


def analyze_user_intent(state: SupervisorState) -> dict:
    """
    Node 1: Analyze what the user wants to do.
    
    Uses LLM to classify user intent based on:
    - Current message
    - Conversation context
    - Current session stage
    """
    user_input = state.get("user_input", "")
    session_stage = state.get("session_stage", "init")
    has_cv = state.get("cv_data") is not None
    has_job = state.get("job_data") is not None
    pending_questions = state.get("pending_questions")
    
    # Debug: Log what the intent analyzer sees
    print(f"\n=== Intent Analyzer State ===")
    print(f"User Input: {user_input[:50]}...")
    print(f"Session Stage: {session_stage}")
    print(f"Has CV: {has_cv}")
    print(f"Has Job: {has_job}")
    print(f"============================\n")
    
    # Build context for LLM
    context = f"""
    Session Stage: {session_stage}
    Has CV Data: {has_cv}
    Has Job Data: {has_job}
    Awaiting Clarification: {pending_questions is not None}
    Ready for Writer: {has_cv and has_job}
    """
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    structured_llm = llm.with_structured_output(UserIntent)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are analyzing user intent in a job application assistant conversation.
        
        Context:
        {context}
        
        Classify the user's intent accurately. Consider:
        - If they're answering pending questions, intent is "answer_clarification"
        - If they mention CV/resume file, intent is "upload_cv"
        - If they provide URL, intent is "provide_job_url"
        - If they paste job description, intent is "provide_job_text"
        - If asking about company, intent is "research_company"
        - If they want to start writing/tailoring, intent is "start_tailoring"
        
        IMPORTANT: Check if CV Data and Job Data are already available in the context.
        - If BOTH are available (Has CV Data: True, Has Job Data: True), and the user is asking about tailoring, analysis, or next steps, classify as "start_tailoring"
        - If BOTH are available and user asks general questions like "what now" or "help", also classify as "start_tailoring" since they're ready
        - Only ask for CV/job if they're actually missing
        """),
        ("user", "{user_input}")
    ])
    
    chain = prompt | structured_llm
    result = chain.invoke({
        "context": context,
        "user_input": user_input
    })
    
    return {
        "intent": result.intent,
        "messages": [{"role": "system", "content": f"Intent: {result.intent} - {result.reasoning}"}]
    }


# ============================================
# CV Agent Integration (Tool Calling)
# ============================================

def invoke_cv_agent(state: SupervisorState) -> dict:
    """
    Node 2: Extract CV information using CV agent as a tool.
    
    Workflow:
    1. Extract resume info from PDF
    2. Check for ambiguities
    3. If ambiguities exist, set them as pending questions
    4. If no ambiguities, mark CV as complete
    """
    user_input = state.get("user_input", "")
    
    # Extract file path from user input (simple pattern matching)
    # In production, this would be more sophisticated
    cv_path = user_input.strip().strip('"').strip("'")
    
    # Check if file exists
    if not Path(cv_path).exists():
        return {
            "supervisor_response": f"I couldn't find the CV file at: {cv_path}\n\nPlease provide a valid file path.",
            "next_action": "wait_for_input",
            "messages": [{"role": "assistant", "content": f"CV file not found: {cv_path}"}]
        }
    
    try:
        # Step 1: Extract resume info
        cv_data = extract_resume_info.invoke({"pdf_path": cv_path})
        
        # Step 2: Check for ambiguities
        questions = identify_ambiguities.invoke({"resume_json": cv_data})
        
        # Step 3: Determine if clarification needed
        needs_clarification = "no questions" not in questions.lower()
        
        if needs_clarification:
            response = f"""Great! I've extracted your CV information. 

I have a few clarifying questions to ensure everything is accurate:

{questions}

Please provide your answers, and I'll update your CV data accordingly."""
            
            return {
                "cv_data": cv_data,
                "cv_file_path": cv_path,
                "pending_questions": questions,
                "needs_clarification": True,
                "supervisor_response": response,
                "next_action": "wait_for_clarification",
                "session_stage": "collecting_cv",
                "messages": [{"role": "assistant", "content": response}]
            }
        else:
            response = f"""Perfect! I've successfully extracted your CV information.

Here's a quick summary:
{_format_cv_summary(cv_data)}

Now, please provide the job posting. You can either:
- Share a URL to the job posting
- Paste the job description text directly"""
            
            return {
                "cv_data": cv_data,
                "cv_file_path": cv_path,
                "needs_clarification": False,
                "supervisor_response": response,
                "next_action": "wait_for_job",
                "session_stage": "collecting_job",
                "messages": [{"role": "assistant", "content": response}]
            }
            
    except Exception as e:
        return {
            "supervisor_response": f"I encountered an error processing your CV: {str(e)}\n\nPlease try again or provide a different file.",
            "next_action": "wait_for_input",
            "messages": [{"role": "assistant", "content": f"Error extracting CV: {str(e)}"}]
        }


def handle_cv_clarification(state: SupervisorState) -> dict:
    """
    Node 3: Process user's clarification answers and update CV data.
    """
    cv_data = state.get("cv_data", "")
    clarifications = state.get("user_input", "")
    
    try:
        # Update CV with clarifications
        updated_cv = update_resume_with_clarifications.invoke({
            "resume_json": cv_data,
            "clarifications": clarifications
        })
        
        response = f"""Thank you! I've updated your CV with that information.

Here's the updated summary:
{_format_cv_summary(updated_cv)}

Now, please provide the job posting. You can either:
- Share a URL to the job posting
- Paste the job description text directly"""
        
        return {
            "cv_data": updated_cv,
            "pending_questions": None,
            "needs_clarification": False,
            "supervisor_response": response,
            "next_action": "wait_for_job",
            "session_stage": "collecting_job",
            "messages": [{"role": "assistant", "content": response}]
        }
        
    except Exception as e:
        return {
            "supervisor_response": f"I had trouble updating the CV: {str(e)}\n\nCould you please rephrase your answers?",
            "next_action": "wait_for_clarification",
            "messages": [{"role": "assistant", "content": f"Error updating CV: {str(e)}"}]
        }


# ============================================
# Job Agent Integration (Tool Calling)
# ============================================

def invoke_job_agent(state: SupervisorState) -> dict:
    """
    Node 4: Extract job information using Job agent as a tool.
    
    Handles both URL and text input.
    """
    user_input = state.get("user_input", "")
    intent = state.get("intent", "")
    
    try:
        if intent == "provide_job_url":
            # Extract URL (simple pattern - in production use regex)
            url = user_input.strip()
            if not url.startswith("http"):
                # Try to find URL in text
                words = user_input.split()
                url = next((w for w in words if w.startswith("http")), None)
                if not url:
                    return {
                        "supervisor_response": "I couldn't find a valid URL in your message. Please provide the job posting URL.",
                        "next_action": "wait_for_job",
                        "messages": [{"role": "assistant", "content": "Invalid URL provided"}]
                    }
            
            job_data = retrieve_web.invoke({"web_urls": [url]})
            source = f"URL: {url}"
            
        else:  # provide_job_text
            job_data = retrieve_text.invoke({"info": user_input})
            source = "pasted job description"
            
        # Ask if they want company research
        response = f"""Excellent! I've analyzed the job posting from {source}.

Here's what I found:
{_format_job_summary(job_data)}

Would you like me to research the company as well? This can help with your cover letter.
- Type 'yes' to research the company
- Type 'no' or 'skip' to proceed directly to tailoring your CV"""
        
        return {
            "job_data": job_data,
            "supervisor_response": response,
            "next_action": "ask_company_research",
            "session_stage": "collecting_job",
            "messages": [{"role": "assistant", "content": response}]
        }
        
    except Exception as e:
        return {
            "supervisor_response": f"I had trouble analyzing the job posting: {str(e)}\n\nPlease try providing it in a different format.",
            "next_action": "wait_for_job",
            "messages": [{"role": "assistant", "content": f"Error extracting job: {str(e)}"}]
        }


def handle_company_research_decision(state: SupervisorState) -> dict:
    """
    Node 5: Handle user's decision about company research.
    """
    user_input = state.get("user_input", "").lower()
    
    if any(word in user_input for word in ["yes", "sure", "okay", "research", "company"]):
        # Extract company name from job data
        try:
            job_data_dict = json.loads(state.get("job_data", "{}"))
            # We'll need to ask for company name or extract it
            return {
                "supervisor_response": "Great! What's the company name? I'll research their values, culture, and recent news.",
                "next_action": "wait_for_company_name",
                "messages": [{"role": "assistant", "content": "Requesting company name for research"}]
            }
        except:
            return {
                "supervisor_response": "What's the company name? I'll research their values, culture, and recent news.",
                "next_action": "wait_for_company_name",
                "messages": [{"role": "assistant", "content": "Requesting company name"}]
            }
    else:
        # Skip company research, proceed to writer
        response = """No problem! We have everything we need to get started.

I'm now connecting you with our Writer Agent, who will help you:
1. Analyze how well your CV matches the job requirements
2. Create a tailored version of your CV
3. Generate a compelling cover letter

The Writer Agent will show you plans before making changes and ask for your approval at each step.

Let me hand you over now..."""
        
        return {
            "supervisor_response": response,
            "next_action": "handoff_to_writer",
            "ready_for_writer": True,
            "session_stage": "writer_session",
            "messages": [{"role": "assistant", "content": response}]
        }


def invoke_company_research(state: SupervisorState) -> dict:
    """
    Node 6: Research company information.
    """
    company_name = state.get("user_input", "").strip()
    
    try:
        company_data = collect_company_info.invoke({"company_name": company_name})
        
        response = f"""Perfect! I've researched {company_name}.

Here's what I found:
{_format_company_summary(company_data)}

Now I'm connecting you with our Writer Agent, who will help you:
1. Analyze how well your CV matches the job requirements
2. Create a tailored version of your CV
3. Generate a compelling cover letter (incorporating company insights)

The Writer Agent will show you plans before making changes and ask for your approval at each step.

Let me hand you over now..."""
        
        return {
            "company_data": company_data,
            "supervisor_response": response,
            "next_action": "handoff_to_writer",
            "ready_for_writer": True,
            "session_stage": "writer_session",
            "messages": [{"role": "assistant", "content": response}]
        }
        
    except Exception as e:
        return {
            "supervisor_response": f"I had trouble researching {company_name}: {str(e)}\n\nWould you like to try a different company name, or skip this step?",
            "next_action": "ask_company_research",
            "messages": [{"role": "assistant", "content": f"Error researching company: {str(e)}"}]
        }


# ============================================
# Writer Agent Hand-off
# ============================================

def handoff_to_writer(state: SupervisorState) -> dict:
    """
    Node 7: Hand off conversation control to Writer agent.
    
    This is where the architecture shifts from tool calling to hand-off.
    The Writer agent takes over the conversation for the refinement session.
    """
    cv_data = state.get("cv_data", "")
    job_data = state.get("job_data", "")
    company_data = state.get("company_data", "")
    
    # Convert data to strings for message construction
    # Handle both dict and JSON string formats
    def format_data(data):
        if data is None or data == "":
            return ""
        if isinstance(data, dict):
            try:
                return json.dumps(data, indent=2)
            except (TypeError, ValueError) as e:
                # If serialization fails, return string representation
                return str(data)
        if isinstance(data, str):
            # If it's already a JSON string, try to parse and reformat for consistency
            if not data.strip():
                return ""
            try:
                parsed = json.loads(data)
                return json.dumps(parsed, indent=2)
            except (json.JSONDecodeError, TypeError):
                # If it's not valid JSON, return as-is
                return data
        return str(data)
    
    cv_str = format_data(cv_data)
    job_str = format_data(job_data)
    company_str = format_data(company_data)
    
    # Validate that we have at least CV or job data before proceeding
    if not cv_str and not job_str:
        return {
            "supervisor_response": "I need both CV and job data to proceed with tailoring. Please provide your CV and job posting first.",
            "next_action": "wait_for_input",
            "messages": [{"role": "assistant", "content": "Missing CV or job data for writer handoff"}]
        }
    
    # Prepare system message with FULL CV/job data (not truncated)
    # This ensures the writer agent always has access to the complete context
    company_context = ""
    if company_str:
        company_context = f"\n\nCompany Information:\n{company_str}"
    
    # Build the system context with available data
    data_sections = []
    if cv_str:
        data_sections.append(f"CV Data (ResumeInfo JSON):\n{cv_str}")
    if job_str:
        data_sections.append(f"Job Requirements (JobRequirements JSON):\n{job_str}")
    
    system_context = f"""You have access to the following structured data for this job application:

{chr(10).join(data_sections)}{company_context}

IMPORTANT: This data is available throughout our conversation. When you need to use tools like analyze_cv_job_alignment, generate_tailored_cv_html, or generate_cover_letter_content, use the FULL JSON data provided above, not truncated versions from earlier messages."""
    
    initial_message = """I have CV and job data ready for tailoring. Please analyze the alignment and help me create a tailored CV and cover letter.

The complete CV and job data are available in the system context above."""
    
    # Initialize Writer agent conversation with system message containing full data
    writer_messages = [
        {"role": "system", "content": system_context},
        {"role": "user", "content": initial_message}
    ]
    
    try:
        # Lazy import writer_agent to avoid WeasyPrint issues
        from .writer_agent import agent as writer_agent
        
        # Invoke Writer agent
        result = writer_agent.invoke({"messages": writer_messages})
        writer_response = result["messages"][-1].content
        
        # Store the full writer conversation history for future turns
        # The result["messages"] contains the complete conversation with the Writer agent
        return {
            "current_agent": "writer",
            "supervisor_response": writer_response,
            "next_action": "writer_active",
            "messages": [
                {"role": "system", "content": "Handed off to Writer Agent"},
                {"role": "assistant", "content": writer_response}
            ],
            # Store full writer conversation history for context in future turns
            "writer_messages": result["messages"]
        }
        
    except Exception as e:
        return {
            "supervisor_response": f"I encountered an error connecting to the Writer Agent: {str(e)}\n\nLet me try to help you directly.",
            "next_action": "error_fallback",
            "messages": [{"role": "assistant", "content": f"Error in writer handoff: {str(e)}"}]
        }


def continue_writer_session(state: SupervisorState) -> dict:
    """
    Node 8: Continue conversation with Writer agent (writer has control).
    
    The supervisor just passes messages through to Writer agent.
    """
    user_input = state.get("user_input", "")
    
    # Check for supervisor return triggers
    return_triggers = ["back to supervisor", "start over", "new job", "different cv"]
    if any(trigger in user_input.lower() for trigger in return_triggers):
        response = """I see you'd like to return to the main menu.

Would you like to:
- Start a new application with a different CV or job?
- Get help with something else?

Just let me know what you need!"""
        
        return {
            "current_agent": "supervisor",
            "supervisor_response": response,
            "next_action": "wait_for_input",
            "session_stage": "init",
            "ready_for_writer": False,
            "messages": [
                {"role": "system", "content": "Returned from Writer Agent to Supervisor"},
                {"role": "assistant", "content": response}
            ],
            # Clear writer conversation history when returning to supervisor
            "writer_messages": []
        }
    
    # Continue with Writer agent
    try:
        # Lazy import writer_agent to avoid WeasyPrint issues
        from .writer_agent import agent as writer_agent
        
        # Retrieve existing writer conversation history from state
        # This should contain the full conversation history from previous turns
        # If missing (edge case), start with empty list
        writer_messages = state.get("writer_messages", [])
        
        # Ensure CV/job data is always available in the context
        # Check if system message with data exists, if not, add it
        cv_data = state.get("cv_data", "")
        job_data = state.get("job_data", "")
        company_data = state.get("company_data", "")
        
        # Check if we need to inject the system context with full data
        has_system_context = any(
            msg.get("role") == "system" and "CV Data (ResumeInfo JSON)" in msg.get("content", "")
            for msg in writer_messages
        )
        
        if not has_system_context and (cv_data or job_data):
            # Reconstruct system message with full data
            # Handle both dict and JSON string formats
            def format_data(data):
                if data is None or data == "":
                    return ""
                if isinstance(data, dict):
                    try:
                        return json.dumps(data, indent=2)
                    except (TypeError, ValueError) as e:
                        # If serialization fails, return string representation
                        return str(data)
                if isinstance(data, str):
                    # If it's already a JSON string, try to parse and reformat for consistency
                    if not data.strip():
                        return ""
                    try:
                        parsed = json.loads(data)
                        return json.dumps(parsed, indent=2)
                    except (json.JSONDecodeError, TypeError):
                        # If it's not valid JSON, return as-is
                        return data
                return str(data)
            
            cv_str = format_data(cv_data)
            job_str = format_data(job_data)
            company_str = format_data(company_data)
            
            # Only create system context if we have data
            if cv_str or job_str:
                company_context = ""
                if company_str:
                    company_context = f"\n\nCompany Information:\n{company_str}"
                
                # Build the system context with available data
                data_sections = []
                if cv_str:
                    data_sections.append(f"CV Data (ResumeInfo JSON):\n{cv_str}")
                if job_str:
                    data_sections.append(f"Job Requirements (JobRequirements JSON):\n{job_str}")
                
                system_context = f"""You have access to the following structured data for this job application:

{chr(10).join(data_sections)}{company_context}

IMPORTANT: This data is available throughout our conversation. When you need to use tools like analyze_cv_job_alignment, generate_tailored_cv_html, or generate_cover_letter_content, use the FULL JSON data provided above, not truncated versions from earlier messages."""
                
                # Insert system message at the beginning
                writer_messages = [{"role": "system", "content": system_context}] + writer_messages
            
            # Insert system message at the beginning
            writer_messages = [{"role": "system", "content": system_context}] + writer_messages
        
        # Append the new user input to the conversation history
        writer_messages.append({"role": "user", "content": user_input})
        
        # Invoke Writer agent with full conversation history
        result = writer_agent.invoke({"messages": writer_messages})
        writer_response = result["messages"][-1].content
        
        # Update stored writer conversation history with the complete result
        # This includes all previous messages plus the new exchange
        updated_writer_messages = result["messages"]
        
        # Check if Writer is done (simple check - could be more sophisticated)
        done_keywords = ["pdf generated successfully", "application complete", "all done"]
        if any(keyword in writer_response.lower() for keyword in done_keywords):
            completion_note = "\n\n---\n✅ Great work! Your application materials are ready.\n\nIf you need help with another job application, just let me know!"
            writer_response += completion_note
            
            return {
                "supervisor_response": writer_response,
                "next_action": "writer_active",
                "session_stage": "complete",
                "messages": [{"role": "assistant", "content": writer_response}],
                # Maintain writer conversation history even after completion
                "writer_messages": updated_writer_messages
            }
        
        return {
            "supervisor_response": writer_response,
            "next_action": "writer_active",
            "messages": [{"role": "assistant", "content": writer_response}],
            # Store updated writer conversation history for next turn
            "writer_messages": updated_writer_messages
        }
        
    except Exception as e:
        return {
            "supervisor_response": f"I encountered an error: {str(e)}\n\nLet me reconnect you with the Writer Agent.",
            "next_action": "writer_active",
            "messages": [{"role": "assistant", "content": f"Error in writer session: {str(e)}"}]
        }


# ============================================
# General Response Generation
# ============================================

def generate_supervisor_response(state: SupervisorState) -> dict:
    """
    Node 9: Generate friendly responses for general queries, help, greetings.
    """
    user_input = state.get("user_input", "")
    intent = state.get("intent", "")
    
    if intent == "greeting":
        response = """Hi there! 👋 I'm your Job Application Assistant!

I'm here to help you create tailored CVs and cover letters that perfectly match job opportunities.

Here's how I can help:
1. 📄 Extract and analyze your CV
2. 🔍 Analyze job postings and research companies
3. ✍️ Tailor your CV to highlight relevant experience
4. 💼 Write compelling, personalized cover letters

To get started, just share your CV file with me!"""

    elif intent == "help":
        response = """I'd be happy to help! Here's what you can do:

**Getting Started:**
- Share your CV file path (e.g., "C:/Documents/my_cv.pdf")
- Provide a job posting URL or paste the job description

**What I'll Do:**
1. Extract your CV information (and ask clarifying questions if needed)
2. Analyze the job requirements
3. Optionally research the company
4. Connect you with our Writer Agent to tailor your CV and create a cover letter

**Current Status:**"""
        
        # Add current status
        if state.get("cv_data"):
            response += "\n✅ CV data collected"
        else:
            response += "\n⏳ Waiting for CV"
            
        if state.get("job_data"):
            response += "\n✅ Job data collected"
        else:
            response += "\n⏳ Waiting for job posting"
            
        if state.get("ready_for_writer"):
            response += "\n✅ Ready to start tailoring!"
            
        response += "\n\nWhat would you like to do next?"

    else:  # general_question
        # Check if we already have CV and job data
        has_cv = state.get("cv_data") is not None
        has_job = state.get("job_data") is not None
        
        # If we have both, suggest starting the tailoring process
        if has_cv and has_job:
            return {
                "supervisor_response": """Great! I can see that you've already uploaded your CV and job description. 

We're all set to start tailoring your application materials! 

I can help you:
1. Analyze how well your CV matches the job requirements
2. Create a tailored version of your CV that highlights relevant experience
3. Generate a compelling cover letter

Would you like me to start the analysis and begin tailoring your CV?""",
                "next_action": "wait_for_input",
                "ready_for_writer": True,
                "messages": [{"role": "assistant", "content": "Detected both CV and job data available"}]
            }
        
        # Use LLM for general questions
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a friendly Job Application Assistant supervisor.
            
            Your role is to guide users through the CV tailoring process.
            Be helpful, warm, and professional. If the question is about:
            - How the system works: Explain the 3-step process (CV → Job → Tailoring)
            - What you can do: Mention CV analysis, job matching, tailored CVs, cover letters
            - Technical issues: Be supportive and offer alternatives
            
            Keep responses concise and actionable."""),
            ("user", "{user_input}")
        ])
        
        chain = prompt | llm
        result = chain.invoke({"user_input": user_input})
        response = result.content
    
    return {
        "supervisor_response": response,
        "next_action": "wait_for_input",
        "messages": [{"role": "assistant", "content": response}]
    }


# ============================================
# Conditional Routing Logic
# ============================================

def route_after_intent(state: SupervisorState) -> str:
    """
    Conditional edge: Determine next node based on intent.
    """
    intent = state.get("intent", "")
    current_agent = state.get("current_agent", "supervisor")
    pending_questions = state.get("pending_questions")
    
    # If Writer is active, continue with Writer
    if current_agent == "writer":
        return "continue_writer"
    
    # If answering clarification questions
    if intent == "answer_clarification" and pending_questions:
        return "handle_clarification"
    
    # Special handling for start_tailoring: check readiness first
    if intent == "start_tailoring":
        has_cv = state.get("cv_data") is not None
        has_job = state.get("job_data") is not None
        
        if has_cv and has_job:
            return "handoff_writer"
        elif not has_cv:
            return "handle_missing_data"
        else:  # not has_job
            return "handle_missing_data"
    
    # Route based on intent
    intent_routing = {
        "upload_cv": "invoke_cv",
        "provide_job_url": "invoke_job",
        "provide_job_text": "invoke_job",
        "research_company": "invoke_company_research",
        "greeting": "generate_response",
        "help": "generate_response",
        "general_question": "generate_response"
    }
    
    return intent_routing.get(intent, "generate_response")


def route_after_action(state: SupervisorState) -> str:
    """
    Conditional edge: Determine next step based on next_action.
    """
    next_action = state.get("next_action", "")
    
    routing = {
        "wait_for_input": END,
        "wait_for_clarification": END,
        "wait_for_job": END,
        "ask_company_research": END,
        "wait_for_company_name": END,
        "handoff_to_writer": "handoff_writer",
        "writer_active": END,
        "error_fallback": END
    }
    
    return routing.get(next_action, END)




# ============================================
# Helper Functions
# ============================================

def _format_cv_summary(cv_json: str) -> str:
    """Format CV data for display."""
    try:
        cv = json.loads(cv_json)
        return f"""
- Name: {cv.get('name', 'N/A')}
- Email: {cv.get('email', 'N/A')}
- Phone: {cv.get('phone', 'N/A')}
- Skills: {len(cv.get('skills', []))} skills listed
- Experience: {len(cv.get('experience', []))} positions
- Education: {len(cv.get('education', []))} entries
"""
    except:
        return "(Summary not available)"


def _format_job_summary(job_json: str) -> str:
    """Format job data for display."""
    try:
        job = json.loads(job_json)
        return f"""
- Position: {job.get('job_title', 'N/A')}
- Level: {job.get('job_level', 'N/A')}
- Type: {job.get('employment_type', 'N/A')}
- Location: {job.get('location', 'N/A')}
- Required Skills: {', '.join(job.get('required_skills', [])[:5])}{'...' if len(job.get('required_skills', [])) > 5 else ''}
- Key Responsibilities: {len(job.get('responsibilities', []))} listed
"""
    except:
        return "(Summary not available)"


def _format_company_summary(company_json: str) -> str:
    """Format company data for display."""
    try:
        company = json.loads(company_json)
        return f"""
- Company: {company.get('company_name', 'N/A')}
- Industry: {company.get('industry', 'N/A')}
- Size: {company.get('company_size', 'N/A')}
- Core Values: {', '.join(company.get('core_values', [])[:3])}{'...' if len(company.get('core_values', [])) > 3 else ''}
- Culture: {company.get('company_culture', 'N/A')[:100]}...
"""
    except:
        return "(Summary not available)"


def handle_missing_data(state: SupervisorState) -> dict:
    """Node: Handle cases where CV or Job data is missing."""
    has_cv = state.get("cv_data") is not None
    has_job = state.get("job_data") is not None
    
    if not has_cv and not has_job:
        response = """To tailor your application materials, I need both your CV and the job posting.

Let's start with your CV. Please provide the file path to your CV (e.g., "C:/Documents/my_cv.pdf")"""
    elif not has_cv:
        response = """I have the job posting, but I still need your CV to create tailored materials.

Please provide the file path to your CV (e.g., "C:/Documents/my_cv.pdf")"""
    else:  # not has_job
        response = """I have your CV, but I still need the job posting to tailor your materials.

Please provide either:
- A URL to the job posting
- The job description text (you can paste it directly)"""
    
    return {
        "supervisor_response": response,
        "next_action": "wait_for_input",
        "messages": [{"role": "assistant", "content": response}]
    }


# ============================================
# Graph Construction
# ============================================

def create_supervisor_graph():
    """
    Build the supervisor orchestration graph.
    
    Graph Flow:
    START → analyze_intent → [conditional routing] → various nodes → END
    
    The graph uses conditional edges to route based on:
    - User intent
    - Current session stage
    - Data availability
    - Active agent (supervisor vs writer)
    """
    workflow = StateGraph(SupervisorState)
    
    # Add all nodes
    workflow.add_node("analyze_intent", analyze_user_intent)
    workflow.add_node("invoke_cv", invoke_cv_agent)
    workflow.add_node("handle_clarification", handle_cv_clarification)
    workflow.add_node("invoke_job", invoke_job_agent)
    workflow.add_node("handle_company_decision", handle_company_research_decision)
    workflow.add_node("invoke_company_research", invoke_company_research)
    workflow.add_node("handoff_writer", handoff_to_writer)
    workflow.add_node("continue_writer", continue_writer_session)
    workflow.add_node("generate_response", generate_supervisor_response)
    workflow.add_node("handle_missing_data", handle_missing_data)
    
    # Set entry point
    workflow.set_entry_point("analyze_intent")
    
    # Add conditional edges from analyze_intent
    workflow.add_conditional_edges(
        "analyze_intent",
        route_after_intent,
        {
            "invoke_cv": "invoke_cv",
            "handle_clarification": "handle_clarification",
            "invoke_job": "invoke_job",
            "invoke_company_research": "invoke_company_research",
            "handoff_writer": "handoff_writer",
            "handle_missing_data": "handle_missing_data",
            "continue_writer": "continue_writer",
            "generate_response": "generate_response"
        }
    )
    
    # Add edges from other nodes
    workflow.add_edge("invoke_cv", END)
    workflow.add_edge("handle_clarification", END)
    workflow.add_conditional_edges(
        "invoke_job",
        lambda state: "ask_company" if state.get("next_action") == "ask_company_research" else END,
        {
            "ask_company": "handle_company_decision",
            END: END
        }
    )
    workflow.add_conditional_edges(
        "handle_company_decision",
        lambda state: state.get("next_action"),
        {
            "wait_for_company_name": END,
            "handoff_to_writer": "handoff_writer"
        }
    )
    workflow.add_edge("invoke_company_research", "handoff_writer")
    workflow.add_edge("handoff_writer", END)
    workflow.add_edge("continue_writer", END)
    workflow.add_edge("generate_response", END)
    workflow.add_edge("handle_missing_data", END)
    
    # Compile with memory (checkpointing)
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)


# ============================================
# Public Interface
# ============================================

def run_supervisor(initial_message: str = None):
    """
    Interactive supervisor session with conversation memory.
    
    This function provides a CLI interface for testing the supervisor agent.
    It maintains state across conversation turns using checkpointing.
    
    Args:
        initial_message: Optional first message to start conversation
        
    Returns:
        Final conversation state
    """
    print("=" * 70)
    print("JOB APPLICATION ASSISTANT - Supervisor Agent")
    print("=" * 70)
    print("\nWelcome! I'm here to help you create tailored job application materials.")
    print("\nType 'quit' to exit at any time.\n")
    
    # Create graph with memory
    app = create_supervisor_graph()
    
    # Initialize state
    config = {"configurable": {"thread_id": "supervisor_session_1"}}
    
    # Initialize conversation
    state = {
        "messages": [],
        "user_input": "",
        "supervisor_response": "",
        "current_agent": "supervisor",
        "next_action": "wait_for_input",
        "intent": "",
        "cv_data": None,
        "cv_file_path": None,
        "job_data": None,
        "company_data": None,
        "pending_questions": None,
        "clarifications": None,
        "needs_clarification": False,
        "session_stage": "init",
        "conversation_count": 0,
        "ready_for_writer": False
    }
    
    # If initial message provided, process it first
    if initial_message:
        print(f"Starting with: {initial_message}\n")
        state["user_input"] = initial_message
        result = app.invoke(state, config)
        state = result
        print(f"Assistant:\n{state.get('supervisor_response', '')}\n")
        print(f"{'-'*70}\n")
    else:
        # Send welcome message
        welcome = """Hi there! 👋 I'm your Job Application Assistant!

I'm here to help you create tailored CVs and cover letters that perfectly match job opportunities.

To get started, please share your CV file path (e.g., "C:/Documents/my_cv.pdf")"""
        print(f"Assistant:\n{welcome}\n")
        print(f"{'-'*70}\n")
    
    # Conversation loop
    max_turns = 50
    turn = 0
    
    while turn < max_turns:
        turn += 1
        
        # Get user input
        user_input = input("You: ").strip()
        
        # Check for exit
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("\n👋 Thank you for using the Job Application Assistant. Good luck with your applications!")
            break
        
        if not user_input:
            continue
        
        # Update state with user input
        state["user_input"] = user_input
        state["conversation_count"] = turn
        
        # Process through graph
        print("\n🤖 Processing...\n")
        try:
            result = app.invoke(state, config)
            state = result
            
            # Display response
            response = state.get("supervisor_response", "I'm not sure how to respond to that.")
            print(f"Assistant:\n{response}\n")
            print(f"{'-'*70}\n")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            print("\nLet's try again. What would you like to do?\n")
    
    if turn >= max_turns:
        print(f"\n⚠️ Reached maximum turns ({max_turns}). Ending session.")
    
    return state


# ============================================
# CLI Entry Point
# ============================================

if __name__ == "__main__":
    import sys
    
    print("\n" + "="*70)
    print("SUPERVISOR AGENT - Interactive Mode")
    print("="*70 + "\n")
    
    # Get initial message from command line if provided
    initial_message = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else None
    
    # Run supervisor
    try:
        run_supervisor(initial_message)
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()