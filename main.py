import click
import sys
from agent import Agent
from logger import logger, log_session_start, log_session_end

@click.command()
def main():
    """
    Main entry point for NexAgent. Provides a CLI loop for user interaction.
    """
    # 1. Print welcome banner
    click.echo("================================================")
    click.echo("      NexAgent - AI-Powered OS Assistant      ")
    click.echo("================================================")
    click.echo("Commands: type anything in plain English")
    click.echo("Special:  'clear' resets conversation")
    click.echo("          'history' shows message count  ")
    click.echo("          'exit' quits")
    click.echo("================================================")

    # 2. Create the agent instance
    try:
        agent = Agent()
    except Exception as e:
        logger.error(f"Critical initialization error: {str(e)}")
        click.echo(f"Error initializing Agent. Please check your .env and config. ({e})")
        return

    # 3. Start session logging
    log_session_start()

    # 4. Interactive loop
    while True:
        try:
            # a/b. Get user input and strip whitespace
            user_input = input("You: ").strip()
            
            # c. Skip if empty
            if not user_input:
                continue
            
            # d. Handle 'exit'
            if user_input.lower() == 'exit':
                click.echo("Goodbye!")
                log_session_end(agent.get_interaction_count())
                sys.exit(0)
            
            # e. Handle 'clear'
            if user_input.lower() == 'clear':
                agent.clear_history()
                click.echo("Conversation cleared.\n")
                continue
            
            # f. Handle 'history'
            if user_input.lower() == 'history':
                click.echo(f"Messages in history: {len(agent.history)}\n")
                continue
            
            # g. General query
            click.echo("\nThinking...\n")
            response = agent.run(user_input)
            click.echo(f"NexAgent: {response}\n")

        except KeyboardInterrupt:
            # h. Wrap in try/except KeyboardInterrupt
            click.echo("\nGoodbye!")
            log_session_end(agent.get_interaction_count())
            sys.exit(0)
        
        except Exception as e:
            # i. Catch all other errors
            logger.error(f"Error in main loop: {str(e)}")
            click.echo(f"Error: {e}\n")
            continue

if __name__ == "__main__":
    main()
