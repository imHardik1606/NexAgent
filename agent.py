import json
from groq import Groq
from config import GROQ_API_KEY, MODEL_NAME, TEMPERATURE
from tools import TOOL_DEFINITIONS, AVAILABLE_FUNCTIONS
from logger import logger

class Agent:
    def __init__(self):
        """
        Initializes the Groq client and the conversation history with a system message.
        """
        self.client = Groq(api_key=GROQ_API_KEY)
        self.history = [
            {
                "role": "system",
                "content": "You are NexAgent, a helpful AI assistant with tools to interact with the filesystem and internet. When asked to do something requiring a tool, use it. Be concise. Always confirm what action you took."
            }
        ]
        self.interaction_count = 0
        logger.info("Agent initialized")

    def run(self, user_input: str) -> str:
        """
        Handles one full interaction cycle with the user, including tool execution if needed.
        """
        try:
            # Step 1: Append user message to history
            self.history.append({"role": "user", "content": user_input})
            
            # Step 2: Log user input
            logger.info(f"User Input: {user_input}")

            # Step 3: First LLM call with tools
            response = self.client.chat.completions.create(
                model=MODEL_NAME,
                messages=self.history,
                tools=TOOL_DEFINITIONS,
                tool_choice="auto",
                temperature=TEMPERATURE
            )

            # Step 4: Get message from response
            message = response.choices[0].message
            
            # Step 5: Check if tool_calls exist
            if message.tool_calls:
                # Append the assistant's tool-call message to history
                self.history.append(message)
                
                # Loop through each tool call
                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    
                    # Parse arguments
                    try:
                        arguments = json.loads(tool_call.function.arguments)
                    except Exception:
                        arguments = {}
                    
                    # Log tool call
                    logger.info(f"Tool called: {function_name} | args: {arguments}")
                    
                    # Look up function in AVAILABLE_FUNCTIONS
                    function_to_call = AVAILABLE_FUNCTIONS.get(function_name)
                    if function_to_call:
                        result = function_to_call(**arguments)
                    else:
                        result = "Error: Tool not found"
                    
                    # Log the result (first 150 chars only)
                    logger.info(f"Tool Result: {str(result)[:150]}...")
                    
                    # Append tool result to history
                    self.history.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": str(result)
                    })
                
                # Make second LLM call with updated history (no tools parameter)
                second_response = self.client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=self.history,
                    temperature=TEMPERATURE
                )
                
                final_content = second_response.choices[0].message.content
                
                # Append assistant message to history and log it
                self.history.append({"role": "assistant", "content": final_content})
                logger.info(f"Final Response: {final_content}")
                
                self.interaction_count += 1
                return final_content
            
            else:
                # No tool calls: Get content, append to history, log and return
                content = message.content
                self.history.append({"role": "assistant", "content": content})
                logger.info(f"Assistant Response: {content}")
                self.interaction_count += 1
                return content

        except Exception as e:
            logger.error(f"Error in Agent.run: {str(e)}")
            return "Sorry, I encountered an error. Please try again."

    def get_interaction_count(self) -> int:
        """Returns the total number of successful interactions."""
        return self.interaction_count

    def clear_history(self):
        """
        Resets history keeping only the first system message.
        """
        if self.history:
            self.history = [self.history[0]]
        logger.info("History cleared")

if __name__ == "__main__":
    agent = Agent()
    
    # Test 1: Tool usage test
    print("\n--- Test 1: File Listing (Should use tool) ---")
    resp1 = agent.run("list the files in current directory")
    print(f"Agent: {resp1}")
    
    # Test 2: Simple chat test
    print("\n--- Test 2: Basic Chat (No tool) ---")
    resp2 = agent.run("what is 2 + 2")
    print(f"Agent: {resp2}")
