import ollama
import json

class TheoryMiner:
    """
    Uses LLM to digest Ancient Texts (theory) and extract algorithmic rules.
    """
    def __init__(self, host="http://localhost:11434"):
        self.client = ollama.Client(host=host)

    def extract_rules(self, text_snippet, model="qwen2.5"):
        """
        Feeds text to LLM and asks for a JSON representation of the Bazi rule.
        """
        prompt = f"""
        你是一个精通Python和八字算法的工程师。
        请阅读以下《三命通会》或古籍片段，提取其中的核心逻辑，并将其转化为 JSON 格式的规则建议。
        
        【古籍片段】:
        {text_snippet}
        
        【任务】:
        如果这段文字描述了一个特定的格局（Pattern）或反应（Reaction），请提取：
        1. Pattern Name (e.g., "San He Bureau")
        2. Conditions (e.g., "Branches contain Si, You, Chou")
        3. Effect (e.g., "Metal Element +100")
        
        请只返回 JSON 格式，不要废话。格式示例：
        {{
            "rule_name": "...",
            "trigger_conditions": ["..."],
            "energy_adjustment": {{ "Element": "+Value" }},
            "description": "..."
        }}
        """
        
        try:
            response = self.client.chat(
                model=model,
                messages=[{'role': 'user', 'content': prompt}]
            )
            return response['message']['content']
        except Exception as e:
            return f"Error connecting to LLM: {e}"

    def process_book(self, long_text, model="qwen2.5", chunk_size=1000):
        """
        Generator that yields rules from a long text (book) chunk by chunk.
        """
        # Split text into chunks
        chunks = [long_text[i:i+chunk_size] for i in range(0, len(long_text), chunk_size)]
        
        for i, chunk in enumerate(chunks):
            yield {
                "chunk_index": i+1,
                "total_chunks": len(chunks),
                "rule": self.extract_rules(chunk, model=model)
            }

# Example Usage for Testing
if __name__ == "__main__":
    # Simulate a snippet found from web search
    snippet = "三命通会云：巳酉丑合金局，为金之正库，见者主文章冠世，武职威权..."
    miner = TheoryMiner(host="http://115.93.10.51:11434") # Use the user's remote host
    print(miner.extract_rules(snippet, model="qwen2.5:latest")) # Assumption on model name
