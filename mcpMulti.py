import asyncio
import os
import shutil

from agents import Agent, Runner, gen_trace_id, trace
from agents.mcp import MCPServer, MCPServerStdio

async def run(filesystem_server: MCPServer, fetch_server: MCPServer, cli_server: MCPServer, volatility_server: MCPServer):
    # Create an agent with multiple MCP servers
    print("Entered RUN")
    agent = Agent(
        name="Assistant",
        instructions="Use the tools to read the filesystem and fetch information to answer questions.",
        mcp_servers=[filesystem_server, fetch_server, cli_server, volatility_server],  # Pass a list of multiple servers
    )
    print("Interactive Agent Ready. Type 'exit' to quit.")
    
    # Interactive loop
    while True:
        # Get user input
        user_message = input("\nEnter your question: ")
        
        # Check for exit command
        if user_message.lower() in ['exit', 'quit', 'bye']:
            print("Exiting interactive mode.")
            break
        
        # Skip empty inputs
        if not user_message.strip():
            continue
            
        print(f"Running: {user_message}")
        
        # Run the agent with the user's input
        result = await Runner.run(starting_agent=agent, input=user_message)
        
        # Print the result
        print("\nResult:")
        print(result.final_output)


async def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    samples_dir = os.path.join(current_dir, "sample_files")
    
    async with (  # Fixed: Parentheses instead of braces
        MCPServerStdio(  # Fixed: Parentheses instead of brace
            name="Filesystem Server",  # Filesystem server
            params={
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem", samples_dir],
            },
        ) as filesystem_server, 
        MCPServerStdio(
            name="Fetch Server",  # Fetch server
            params={
                "command": "python",
                "args": ["-m", "mcp_server_fetch"],
            },
        ) as fetch_server, 
        MCPServerStdio(
            name="Cli MCP Server",  # Command Line
            params={
                "command": "uvx",
                "args": ["cli-mcp-server", "run", "cli-mcp-server"],
                "env": {
                    "ALLOWED_DIR": "/tmp",
                    "ALLOWED_COMMANDS": "all",
                    "ALLOWED_FLAGS": "-l,-a,--help,--version",
                    "MAX_COMMAND_LENGTH": "1024",
                    "COMMAND_TIMEOUT": "600",
                },
            },
        ) as cli_mcp_server, 
        MCPServerStdio(  # Fixed: Parentheses instead of brace
            name="Volatility MCP Server",  # Volatility server
            params={
                "command": "python",
                "args": ["/home/kali/MCP/Volatility-MCP-Server/volatility_mcp_server.py"],
                "env": {
                    "PYTHONPATH": "/home/kali/MCP/Volatility-MCP-Server/volatility3/volatility3-2.11.0",
                },
            },
        ) as volatility_mcp_server  # Removed trailing comma here
    ):  # Added colon
        trace_id = gen_trace_id()
        with trace(workflow_name="MCP Multiple Servers Example", trace_id=trace_id):
            print(f"View trace: https://platform.openai.com/traces/{trace_id}\n")
            
            await run(filesystem_server, fetch_server, cli_mcp_server, volatility_mcp_server)  # Fixed indentation


if __name__ == "__main__":
    if not shutil.which("npx"):
        raise RuntimeError("npx is not installed. Please install it with `npm install -g npx`.")
    asyncio.run(main())






