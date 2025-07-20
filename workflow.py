#!/usr/bin/env python3
"""
Blog Topic Generation Workflow

This script combines fetching liked tweets and generating blog topics.
"""

import os
import sys
from twitter_client_oauth import TwitterClientOAuth
from blog_topic_generator import BlogTopicGenerator


def main():
    """Main workflow to fetch tweets and generate blog topics"""
    print("Blog Topic Generation Workflow")
    print("=" * 50)
    
    # Check environment variables
    required_vars = ['X_API_BEARER_TOKEN', 'X_API_KEY', 'X_API_SECRET', 'X_ACCESS_TOKEN', 'X_ACCESS_TOKEN_SECRET', 'X_USERNAME']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set them in your .env file")
        return 1
    
    # Initialize clients
    try:
        twitter_client = TwitterClientOAuth()
        topic_generator = BlogTopicGenerator()
    except Exception as e:
        print(f"❌ Error initializing clients: {e}")
        return 1
    
    # Get user configuration
    username = os.getenv('X_USERNAME')
    max_tweets = int(os.getenv('MAX_TWEETS', '25'))
    days_back = int(os.getenv('DAYS_BACK', '7'))
    
    print(f"\n📋 Configuration:")
    print(f"- Username: @{username}")
    print(f"- Max tweets to fetch: {max_tweets}")
    print(f"- Days back: {days_back}")
    
    # Step 1: Fetch liked tweets
    print(f"\n🔍 Step 1: Fetching liked tweets for @{username}...")
    
    user_id = twitter_client.get_user_id(username)
    if not user_id:
        print(f"❌ Could not get user ID for @{username}")
        return 1
    
    tweets = twitter_client.get_liked_tweets(user_id, max_results=max_tweets, days_back=days_back)
    if not tweets:
        print("❌ No liked tweets found")
        return 1
    
    print(f"✅ Found {len(tweets)} liked tweets")
    
    # Save tweets
    tweets_file = "liked_tweets.json"
    twitter_client.save_tweets_to_file(tweets, tweets_file)
    
    # Step 2: Generate blog topics
    print(f"\n💡 Step 2: Generating blog topic ideas...")
    results = topic_generator.generate_blog_topics(tweets_file)
    if not results:
        print("❌ Failed to generate blog topics")
        return 1
    
    # Display results
    topic_generator.print_summary(results)
    topic_generator.save_results(results)
    
    print(f"\n✅ Workflow completed successfully!")
    print(f"📁 Files created:")
    print(f"   - {tweets_file} (liked tweets data)")
    print(f"   - blog_topics.json (generated topics)")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())