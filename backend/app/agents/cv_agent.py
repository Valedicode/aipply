from pydantic import BaseModel, Field
from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pathlib import Path
import fitz
import dotenv

dotenv.load_dotenv()

# Default test CV path
DEFAULT_TEST_CV = Path(__file__).parent.parent.parent / "data" / "CV.pdf"

class ResumeInfo(BaseModel):
    name: str
    email: str
    phone: str
    skills: str
    education: list[str]
    experience: list[str]

@tool
def extract_resume_info(pdf_path: str) -> str:
    """Extract structured information from a PDF resume file.
        
        This tool:
        1. Reads the PDF file
        2. Extracts text content
        3. Analyzes and structures the information
        
        Args:
            pdf_path: Path to the PDF resume file (e.g., "resume.pdf")
            
        Returns:
            JSON string with extracted resume information including name, 
            skills, education, experience, contact info, etc.
    """
    # Extract text from PDF
    text = ""
    doc = fitz.open(str(pdf_path))
    for page in doc:
        text += page.get_text("text") + "\n"
    
    # Use LLM to extract structured data
    llm = ChatOpenAI(model="gpt-5-nano", temperature=0)
    structured_llm = llm.with_structured_output(ResumeInfo)

    prompt = ChatPromptTemplate.from_messages([
        ("system", "Extract all information from the resume text. Be thorough and capture all details."),
        ("user", f"{text}")
    ])

    chain = prompt | structured_llm
    result = chain.invoke({"text": text})

    # Return json format as string
    return result.model_dump_json(indent=2)

@tool
def identify_ambiguities(resume_json: str) -> str:
    """Analyze extracted resume data and identify any ambiguities or missing information.
    
    Args:
        resume_json: JSON string of extracted resume data
        
    Returns:
        List of clarifying questions to ask the user, or "No questions" if data is clear
    """
    llm = ChatOpenAI(model="gpt-5-nano", temperature=0)
    prompt = ChatPromptTemplate.from_messages([
        ("system", """Analyze the resume data for:
        - Missing important information
        - Ambiguous entries
        - Unclear dates or descriptions
        - Information that needs verification
        
        Return a numbered list of specific questions to ask the user, or "No questions needed" if everything is clear."""),
        ("user", "Resume data:\n{data}")
    ])

    chain = prompt | llm
    result = chain.invoke({"data": resume_json})
    return result.content

@tool  
def update_resume_with_clarifications(resume_json: str, clarifications: str) -> str:
    """Update resume data based on user's clarifying answers.
    
    Args:
        resume_json: Original extracted resume JSON
        clarifications: User's answers to clarifying questions
        
    Returns:
        Updated resume JSON with clarifications incorporated
    """
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Update the resume data by incorporating the user's clarifying answers. Return the complete updated JSON."),
        ("user", "Original resume:\n{resume}\n\nClarifications:\n{clarifications}")
    ])
    
    chain = prompt | llm
    result = chain.invoke({"resume": resume_json, "clarifications": clarifications})
    return result.content

# Create agent
llm = ChatOpenAI(model="gpt-5-nano")
system_prompt = """You are a resume extraction assistant. Your workflow:

1. When given a PDF path, use extract_resume_info to extract information
2. Use identify_ambiguities to check for unclear or missing information
3. If there are questions, present them to the user and wait for answers
4. Use update_resume_with_clarifications to incorporate user's answers
5. Return the final structured resume data

Be thorough and ensure all information is accurately captured."""

agent = create_agent(
    model = llm,
    tools=[
        extract_resume_info, 
        identify_ambiguities,
        update_resume_with_clarifications
    ],
    system_prompt=system_prompt
)


def run_interactive_cv_extraction(pdf_path: str):
    """
    Run CV extraction with continuous user interaction via terminal.
    
    The agent will:
    1. Extract resume from PDF
    2. Ask clarifying questions
    3. Wait for user answers
    4. Continue until everything is clear
    5. Return final structured data
    """
    print("=" * 70)
    print("CV EXTRACTION WITH INTERACTIVE Q&A")
    print("=" * 70)
    print(f"\nProcessing: {pdf_path}")
    print("\nType 'quit' to exit at any time.\n")
    
    # Initialize conversation history
    messages = [
        {"role": "user", "content": f"Extract all information from {pdf_path}. Ask me questions if anything is unclear or missing."}
    ]
    
    # Conversation loop
    max_turns = 10  # Prevent infinite loops
    turn = 0
    
    while turn < max_turns:
        turn += 1
        print(f"\n{'='*70}")
        print(f"Turn {turn}")
        print(f"{'='*70}")
        
        # Agent's turn
        print("\n🤖 Agent is processing...\n")
        result = agent.invoke({"messages": messages})
        agent_response = result["messages"][-1].content
        
        # Add agent's response to history
        messages.append({"role": "assistant", "content": agent_response})
        
        # Display agent's response
        print(f"Agent:\n{agent_response}\n")
        
        # Check if agent is done (no more questions)
        done_keywords = [
            "here is the final",
            "extraction complete",
            "no further questions",
            "all information captured",
            "final structured data"
        ]
        
        if any(keyword in agent_response.lower() for keyword in done_keywords):
            print("\n✅ Extraction complete!")
            print(f"{'='*70}\n")
            break
        
        # Check if agent is asking questions
        question_keywords = ["question", "clarify", "unclear", "missing", "?"]
        is_asking = any(keyword in agent_response.lower() for keyword in question_keywords)
        
        if not is_asking:
            # Agent might be done but didn't use our keywords
            print("\n✅ Agent seems to be done. Review the data above.")
            confirm = input("\nContinue conversation? (y/n): ").strip().lower()
            if confirm != 'y':
                break
        
        # User's turn
        print(f"{'-'*70}")
        user_input = input("You: ").strip()
        
        # Allow user to quit
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("\n👋 Exiting conversation.")
            break
        
        # Add user's response to history
        messages.append({"role": "user", "content": user_input})
    
    if turn >= max_turns:
        print(f"\n⚠️  Reached maximum turns ({max_turns}). Ending conversation.")
    
    # Return final conversation
    return {
        "messages": messages,
        "turns": turn,
        "final_response": messages[-1]["content"] if len(messages) > 1 else None
    }


# Simple CLI for testing
if __name__ == "__main__":
    import sys
    
    print("\n" + "="*70)
    print("CV AGENT - Interactive Terminal Mode")
    print("="*70 + "\n")
    
    # Get PDF path from user or command line, or use default test CV
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    elif DEFAULT_TEST_CV.exists():
        # Use default test CV if available
        pdf_path = str(DEFAULT_TEST_CV)
        print(f"Using default test CV: {pdf_path}")
        print("(To use a different file, pass it as an argument: python cv_agent.py /path/to/resume.pdf)\n")
    else:
        pdf_path = input("Enter path to PDF resume: ").strip()
    
    # Check if file exists
    if not Path(pdf_path).exists():
        print(f"\n❌ Error: File not found: {pdf_path}")
        if DEFAULT_TEST_CV.exists():
            print(f"💡 Tip: Default test CV should be at: {DEFAULT_TEST_CV}")
        sys.exit(1)
    
    # Run interactive extraction
    try:
        result = run_interactive_cv_extraction(pdf_path)
        
        print("\n" + "="*70)
        print("CONVERSATION SUMMARY")
        print("="*70)
        print(f"Total turns: {result['turns']}")
        print(f"Total messages: {len(result['messages'])}")
        
        # Optionally save conversation
        save = input("\nSave conversation to file? (y/n): ").strip().lower()
        if save == 'y':
            import json
            output_file = "cv_extraction_conversation.json"
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"✅ Saved to {output_file}")
        
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user. Exiting.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
