#!/usr/bin/env python
import os
import subprocess
import sys
import argparse

def main():
    # LangSmith project name for report quality testing
    langsmith_project = "Open Deep Research: Report Quality Testing"

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run report quality tests for different agents")
    parser.add_argument("--rich-output", action="store_true", help="Show rich output in terminal")
    parser.add_argument("--experiment-name", help="Name for the LangSmith experiment")
    parser.add_argument("--agent", choices=["multi_agent", "graph"], help="Run tests for a specific agent")
    parser.add_argument("--all", action="store_true", help="Run tests for all agents")
    args = parser.parse_args()
    
    # Base pytest options
    base_pytest_options = ["-v", "--disable-warnings", "--langsmith-output"]
    if args.rich_output:
        base_pytest_options.append("--rich-output")
    
    # Define available agents
    agents = ["multi_agent", "graph"]
    
    # Determine which agents to test
    if args.agent:
        if args.agent in agents:
            agents_to_test = [args.agent]
        else:
            print(f"Error: Unknown agent '{args.agent}'")
            print(f"Available agents: {', '.join(agents)}")
            return 1
    elif args.all:
        agents_to_test = agents
    else:
        # Default to testing all agents
        agents_to_test = agents
    
    # Run tests for each agent
    for agent in agents_to_test:
        print(f"\nRunning tests for {agent}...")
        
        # Set up LangSmith environment for this agent
        os.environ["LANGSMITH_PROJECT"] = langsmith_project
        os.environ["LANGSMITH_TEST_SUITE"] = langsmith_project
        
        # Ensure tracing is enabled
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        
        # Create a fresh copy of the pytest options for this run
        pytest_options = base_pytest_options.copy()
        
        # Use environment variable to pass the agent name instead
        os.environ["RESEARCH_AGENT"] = agent
        
        # Test file path
        test_file = "tests/test_report_quality.py"
                    
        # Set up experiment name
        experiment_name = args.experiment_name if args.experiment_name else f"Report Quality Test | Agent: {agent}"
        print(f"   Project: {langsmith_project}")
        print(f"   Experiment: {experiment_name}")
        
        os.environ["LANGSMITH_EXPERIMENT"] = experiment_name
        
        print(f"\nℹ️ Test results for {agent} are being logged to LangSmith")
        
        # Run the test
        cmd = ["python", "-m", "pytest", test_file] + pytest_options
        print(f"Running command: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Print test output with highlighting for section relevance analysis
        stdout = result.stdout
        
        # Highlight section relevance information with colors if supported
        if "POTENTIAL IRRELEVANT SECTIONS DETECTED" in stdout:
            # Extract and highlight the section relevance analysis
            import re
            section_analysis = re.search(r'⚠️ POTENTIAL IRRELEVANT SECTIONS DETECTED:.*?(?=\n\n|\Z)', 
                                         stdout, re.DOTALL)
            if section_analysis:
                analysis_text = section_analysis.group(0)
                # Use ANSI color codes for highlighting (red for irrelevant sections)
                highlighted_analysis = f"\033[1;31m{analysis_text}\033[0m"
                stdout = stdout.replace(analysis_text, highlighted_analysis)
        
        print(stdout)
        
        if result.stderr:
            print("Errors/warnings:")
            print(result.stderr)
            
        # Print a summary of section relevance issues
        if "POTENTIAL IRRELEVANT SECTIONS DETECTED" in result.stdout:
            print("\n\033[1;33m==== SECTION RELEVANCE ISSUES DETECTED ====\033[0m")
            print("Some sections may not be relevant to the main topic.")
            print("Review the detailed analysis in the test output above.")
            print("Consider updating the prompts to improve section relevance.")
                
if __name__ == "__main__":
    sys.exit(main() or 0)