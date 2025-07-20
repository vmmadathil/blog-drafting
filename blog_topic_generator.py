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
        """Prepare simplified tweet content for analysis - text only"""
        tweet_texts = []
        
        for tweet in tweets[:max_tweets]:
            text = tweet.get('text', '').strip()
            if not text:
                continue
                
            # Clean up text (remove URLs, excessive whitespace)
            import re
            text = re.sub(r'https?://\S+', '', text)  # Remove URLs entirely
            text = re.sub(r'\s+', ' ', text)          # Normalize whitespace
            text = text.strip()
            
            if text:  # Only add non-empty tweets
                tweet_texts.append(text)
        
        return '\n\n'.join(tweet_texts)
    
    def generate_topics_with_ai(self, tweets: List[Dict]) -> List[str]:
        """Generate blog topics using Anthropic Claude in an open-ended way"""
        if not HAS_ANTHROPIC or not self.anthropic_api_key:
            print("Anthropic API not available. Please install anthropic and set ANTHROPIC_API_KEY.")
            return []
        
        try:
            tweet_content = self.prepare_tweet_content(tweets)
            print(f"Prepared {len(tweet_content)} characters of tweet content")
            
            # Load prompt template from file
            try:
                with open('blog_prompt.txt', 'r', encoding='utf-8') as f:
                    prompt_template = f.read()
                prompt = prompt_template.format(tweet_content=tweet_content)
                print("✅ Prompt template loaded and formatted successfully")
            except FileNotFoundError:
                print("Warning: blog_prompt.txt not found. Using default prompt.")
                prompt = f"Based on these tweets, suggest 3-5 blog post ideas:\n\n{tweet_content}"
            except Exception as e:
                print(f"Error formatting prompt: {e}")
                return []

            print("🤖 Calling Anthropic API...")
            message = self.client.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=1500,
                temperature=0.8,
                messages=[{"role": "user", "content": prompt}]
            )
            print("✅ API call successful")
            
            response_text = message.content[0].text.strip()
            
            # Save response to text file
            with open('blog_topics.txt', 'w', encoding='utf-8') as f:
                f.write("BLOG TOPIC SUGGESTIONS\n")
                f.write("=" * 50 + "\n\n")
                f.write(response_text)
            
            print("✅ Blog topics saved to blog_topics.txt")
            
            # Return empty list since we're not parsing JSON anymore
            return []
            
        except Exception as e:
            print(f"Error generating AI topics: {e}")
            import traceback
            traceback.print_exc()
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
            print(f"Tweets file {tweets_file} not found. Please run twitter_client_oauth.py first.")
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
    
    def save_results(self, results: Dict, filename: str = "blog_topics_summary.json"):
        """Save summary to file (topics are now in txt file)"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"Summary saved to {filename}")
    
    def print_summary(self, results: Dict):
        """Print a summary of the analysis"""
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
        
        print(f"\n💡 Blog topics saved to blog_topics.txt")
        print("📁 Open blog_topics.txt to see the detailed suggestions with titles, descriptions, and outlines.")
        
        # Also display the topics content here
        try:
            with open('blog_topics.txt', 'r', encoding='utf-8') as f:
                content = f.read()
                # Skip the header and show the actual topics
                if "=" * 50 in content:
                    topics_content = content.split("=" * 50 + "\n\n", 1)[1]
                else:
                    topics_content = content
                
                print("\n" + "="*60)
                print("BLOG TOPIC SUGGESTIONS")
                print("="*60)
                print(topics_content)
        except Exception as e:
            print(f"Could not display topics: {e}")


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