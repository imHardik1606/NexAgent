import json
from groq import Groq
from config import GROQ_API_KEY, MODEL_NAME, TEMPERATURE, BASE_PATH
from tools import TOOL_DEFINITIONS, AVAILABLE_FUNCTIONS, load_memory
from logger import logger
from traceroot import observe, update_current_span

class Agent:
    def __init__(self):
        """
        Initializes the Groq client and the conversation history with a system message.
        """
        self.client = Groq(api_key=GROQ_API_KEY)
        
        # Load long-term memory
        self.memory = load_memory()
        memory_context = f"\nLONG-TERM MEMORY: {json.dumps(self.memory)}" if self.memory else ""

        self.history = [
            {
                "role": "system",
                "content": (
                    "You are NexAgent, a professional and high-end AI assistant. "
                    f"Your base user directory is {BASE_PATH}. "
                    "You have access to tools for filesystem operations and web searching. "
                    f"{memory_context}\n"
                    "GUIDELINES:\n"
                    "1. Always identify yourself clearly as NexAgent.\n"
                    "2. Use tools whenever needed to provide accurate info.\n"
                    "3. If a tool result is empty or technical (like raw shell output), summarize it in clean English. If info is missing, try a different search query or tool.\n"
                    "4. If 'wttr.in' is down, try searching the web for 'current weather in [location]'.\n"
                    "5. Avoid technical shorthand like 'km/h' if it looks messy; use 'km per hour' or 'mph'.\n"
                    "6. DO NOT hallucinate tool calls or use XML-like tags.\n"
                    "7. Be concise and confirm your actions professionally."
                )
            }
        ]
        self.interaction_count = 0
        logger.debug("Agent initialized")


    @observe(name="NexAgent Interaction", type="agent")
    def run(self, user_input: str) -> str:

        """
        Handles the interaction cycle, supporting multiple tool calls in sequence.
        """
        try:
            self.history.append({"role": "user", "content": user_input})
            logger.debug(f"User Input: {user_input}")

            # Support up to 5 turns of tool usage per interaction
            for turn in range(5):
                response = self.client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=self.history,
                    tools=TOOL_DEFINITIONS,
                    tool_choice="auto",
                    temperature=TEMPERATURE
                )

                # Record the LLM interaction details in the trace
                update_current_span(
                    model=MODEL_NAME,
                    model_parameters={"temperature": TEMPERATURE},
                    usage={
                        "input_tokens": response.usage.prompt_tokens,
                        "output_tokens": response.usage.completion_tokens
                    },
                    prompt=self.history
                )

                message = response.choices[0].message
                
                # If no tool calls, this is the final answer
                if not message.tool_calls:
                    self.history.append({"role": "assistant", "content": message.content})
                    self.interaction_count += 1
                    return message.content

                # Process tool calls
                self.history.append(message)
                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    try:
                        arguments = json.loads(tool_call.function.arguments)
                    except Exception:
                        arguments = {}
                    
                    logger.debug(f"Tool called: {function_name} | args: {arguments}")
                    
                    function_to_call = AVAILABLE_FUNCTIONS.get(function_name)
                    if function_to_call:
                        result = function_to_call(**arguments)
                    else:
                        result = "Error: Tool not found"
                    
                    logger.debug(f"Tool Result: {str(result)[:150]}...")
                    
                    self.history.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": str(result)
                    })
                
                # Loop continues to give the model a chance to react to the tool results

            return "Error: Maximum tool interaction turns exceeded."

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
