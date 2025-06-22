from openai import AsyncOpenAI
import logging

class DrSnowPawsGuardrails:
    def __init__(self, client: AsyncOpenAI):
        self.client = client
        self.logger = logging.getLogger(__name__)
        
    async def check_input(self, text: str) -> tuple[bool, str]:
        """Check if input is safe and appropriate for children."""
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": """You are a content safety filter for a children's medical chatbot.
                    Analyze the input for:
                    1. Inappropriate content
                    2. Adult themes
                    3. Harmful instructions
                    4. Personal information
                    
                    If the content is safe, return "SAFE: " followed by the original text.
                    If unsafe, return "UNSAFE: " with a child-friendly explanation of why it can't be answered."""},
                    {"role": "user", "content": text}
                ],
                temperature=0,
                max_tokens=100
            )
            
            result = response.choices[0].message.content.strip()
            
            if result.startswith("SAFE:"):
                return True, text
            else:
                return False, "*adjusts glasses* I'm sorry, but I can't answer that kind of question. Let's talk about something else! 🐾"
                
        except Exception as e:
            self.logger.error(f"Error in input check: {e}")
            return True, text  # Default to allowing if check fails
            
    async def check_output(self, response: str, original_input: str) -> str:
        """Ensure the output is appropriate and child-friendly."""
        try:
            check = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": """You are a content safety filter for a children's medical chatbot.
                    Analyze the output for:
                    1. Age-appropriate language and concepts
                    2. Comforting and reassuring tone
                    3. No medical advice beyond basic wellness
                    4. No personal information
                    
                    If safe, return "SAFE: " followed by the original text.
                    If unsafe, return a rewritten child-friendly version."""},
                    {"role": "user", "content": f"Input: {original_input}\nOutput: {response}"}
                ],
                temperature=0,
                max_tokens=200
            )
            
            result = check.choices[0].message.content.strip()
            
            if result.startswith("SAFE:"):
                return response
            else:
                return result
                
        except Exception as e:
            self.logger.error(f"Error in output check: {e}")
            return response  # Return original if check fails

    def handle_emergency(self, user_input: str) -> str:
        """
        Special handler for potential emergency situations.
        
        Args:
            user_input: The concerning user input
            
        Returns:
            An appropriate emergency response
        """
        return (
            "*looks very concerned* Oh my! This sounds like something we need grown-up help with "
            "right away. Please tell a parent, teacher, or another trusted adult immediately. "
            "If you're feeling very unwell or unsafe, remember these important numbers:\n"
            "• Emergency: Call 911\n"
            "• Child Help Hotline: 1-800-422-4453\n"
            "*gentle pat with paw* Your safety is very important to me! 🐾❤️"
        )