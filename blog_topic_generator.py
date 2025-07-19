import json
import os
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False


class BlogTopicGenerator:
    def __init__(self):
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
        if HAS_ANTHROPIC and self.anthropic_api_key:
            self.client = anthropic.Anthropic(api_key=self.anthropic_api_key)
    
    def prepare_tweet_content(self, tweets: List[Dict], max_tweets: int = 20) -> str:
        """Prepare tweet content for analysis"""
        tweet_texts = []
        
        for tweet in tweets[:max_tweets]:
            author = tweet.get('author', {}).get('username', 'unknown')
            text = tweet.get('text', '').strip()
            
            # Clean up text (remove excessive whitespace, URLs for readability)
            import re
            text = re.sub(r'https?://\S+', '[URL]', text)
            text = re.sub(r'\s+', ' ', text)
            
            tweet_texts.append(f"@{author}: {text}")
        
        return '\n\n'.join(tweet_texts)
    
    def generate_topics_with_ai(self, tweets: List[Dict]) -> List[str]:
        """Generate blog topics using Anthropic Claude in an open-ended way"""
        if not HAS_ANTHROPIC or not self.anthropic_api_key:
            print("Anthropic API not available. Please install anthropic and set ANTHROPIC_API_KEY.")
            return []
        
        try:
            tweet_content = self.prepare_tweet_content(tweets)
            
            # Load prompt template from file
            try:
                with open('blog_prompt.txt', 'r', encoding='utf-8') as f:
                    prompt_template = f.read()
                prompt = prompt_template.format(tweet_content=tweet_content)
            except FileNotFoundError:
                print("Warning: blog_prompt.txt not found. Using default prompt.")
                prompt = f"Based on these tweets, suggest 3-5 blog post ideas:\n\n{tweet_content}"

            message = self.client.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=800,
                temperature=0.8,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = message.content[0].text.strip()
            
            # Extract topics from numbered list
            import re
            topics = re.findall(r'^\d+\.?\s*(.+)$', response_text, re.MULTILINE)
            
            if not topics:
                # Fallback: split by lines and clean
                topics = [line.strip() for line in response_text.split('\n') if line.strip()]
            
            return [topic.strip() for topic in topics if topic.strip()]
            
        except Exception as e:
            print(f"Error generating AI topics: {e}")
            return []
    
    def generate_simple_summary(self, tweets: List[Dict]) -> Dict:
        """Generate a simple summary without complex analysis"""
        total_tweets = len(tweets)
        authors = set()
        
        for tweet in tweets:
            author = tweet.get('author', {}).get('username')
            if author:
                authors.add(author)
        
        return {
            'total_tweets': total_tweets,
            'unique_authors': len(authors),
            'sample_authors': list(authors)[:10]
        }
    
    def generate_blog_topics(self, tweets_file: str = "liked_tweets.json") -> Dict:
        """Main function to generate blog topics from liked tweets"""
        
        # Load tweets
        try:
            with open(tweets_file, 'r', encoding='utf-8') as f:
                tweets = json.load(f)
        except FileNotFoundError:
            print(f"Tweets file {tweets_file} not found. Please run twitter_client.py first.")
            return {}
        
        if not tweets:
            print("No tweets found in file.")
            return {}
        
        print(f"Analyzing {len(tweets)} liked tweets for blog topic inspiration...")
        
        # Generate simple summary
        summary = self.generate_simple_summary(tweets)
        
        # Generate topics using AI
        ai_topics = self.generate_topics_with_ai(tweets)
        
        results = {
            'summary': summary,
            'blog_topics': ai_topics,
            'total_topics': len(ai_topics)
        }
        
        return results
    
    def save_results(self, results: Dict, filename: str = "blog_topics.json"):
        """Save results to file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"Results saved to {filename}")
    
    def print_summary(self, results: Dict):
        """Print a summary of generated topics"""
        if not results:
            return
        
        print("\n" + "="*60)
        print("BLOG TOPIC INSPIRATION FROM YOUR LIKED TWEETS")
        print("="*60)
        
        summary = results.get('summary', {})
        
        print(f"\nContent Summary:")
        print(f"- Analyzed {summary.get('total_tweets', 0)} liked tweets")
        print(f"- From {summary.get('unique_authors', 0)} different authors")
        
        sample_authors = summary.get('sample_authors', [])
        if sample_authors:
            print(f"- Including content from: {', '.join(sample_authors[:5])}" + 
                  (f" and {len(sample_authors)-5} others" if len(sample_authors) > 5 else ""))
        
        topics = results.get('blog_topics', [])
        if topics:
            print(f"\n💡 Blog Post Ideas ({len(topics)}):")
            for i, topic in enumerate(topics, 1):
                print(f"{i:2d}. {topic}")
        else:
            print("\nNo topics generated. Check your API configuration.")


def main():
    """Generate blog topics from liked tweets"""
    generator = BlogTopicGenerator()
    results = generator.generate_blog_topics()
    
    if results:
        generator.print_summary(results)
        generator.save_results(results)
    else:
        print("No results generated. Make sure you have liked tweets data.")


if __name__ == "__main__":
    main()