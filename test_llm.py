# test_llm.py - Test script to verify LLM is working
import asyncio
from core.llm import LLMClient

async def test_llm():
    client = LLMClient()
    
    test_prompt = """
    Classify this message: "Can you help me write a business proposal?"
    
    Return JSON with:
    - is_work: boolean
    - topic: string
    - confidence: string
    """
    
    response = await client.complete(
        system_prompt="You are a classifier. Return only valid JSON.",
        user_message=test_prompt,
        temperature=0.1,
        max_tokens=200,
    )
    
    print("LLM Response:")
    print(response)
    
    # Try to parse it
    import json
    try:
        data = json.loads(response)
        print("\nParsed successfully!")
        print(json.dumps(data, indent=2))
    except Exception as e:
        print(f"\nFailed to parse: {e}")

asyncio.run(test_llm())
