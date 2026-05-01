from groq import Groq
import config

def test_groq_connection():
    print(f"Testing connection with model: {config.MODEL_NAME}...")
    
    try:
        # Initialize Groq client
        client = Groq(api_key=config.GROQ_API_KEY)
        
        # Send a simple message
        completion = client.chat.completions.create(
            model=config.MODEL_NAME,
            messages=[
                {
                    "role": "user",
                    "content": "Respond with exactly: CONNECTION SUCCESSFUL"
                }
            ],
            temperature=config.TEMPERATURE,
        )
        
        # Print the response
        response_text = completion.choices[0].message.content
        print(f"\nAPI Response: {response_text}")
        
        if "CONNECTION SUCCESSFUL" in response_text.upper():
            print("\n✅ Groq API connection verified successfully!")
        else:
            print("\n⚠️ Received unexpected response format.")
            
    except Exception as e:
        print(f"\n❌ Error connecting to Groq API:")
        print(f"Details: {str(e)}")
        print("\nPlease check your GROQ_API_KEY in the .env file and ensure you have an active internet connection.")

if __name__ == "__main__":
    test_groq_connection()
