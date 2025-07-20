import os
import json
import requests
import hmac
import hashlib
import base64
import urllib.parse
import time
import secrets
import string
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

class TwitterClientOAuth:
    def __init__(self):
        # Bearer Token for user lookup (app-only)
        self.bearer_token = os.getenv('X_API_BEARER_TOKEN')
        
        # OAuth 1.0a credentials for liked tweets (user context)
        self.api_key = os.getenv('X_API_KEY')
        self.api_secret = os.getenv('X_API_SECRET')
        self.access_token = os.getenv('X_ACCESS_TOKEN')
        self.access_token_secret = os.getenv('X_ACCESS_TOKEN_SECRET')
        
        self.base_url = "https://api.x.com/2"
        
        # Validate credentials
        if not self.bearer_token:
            print("Warning: No Bearer Token found. User lookup may not work.")
        
        oauth_tokens = [self.api_key, self.api_secret, self.access_token, self.access_token_secret]
        if not all(oauth_tokens):
            raise ValueError("OAuth 1.0a credentials required: X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET")
    
    def create_oauth_signature(self, method: str, url: str, params: Dict = None) -> str:
        """Create OAuth 1.0a signature"""
        # OAuth parameters
        oauth_params = {
            'oauth_consumer_key': self.api_key,
            'oauth_token': self.access_token,
            'oauth_signature_method': 'HMAC-SHA1',
            'oauth_timestamp': str(int(time.time())),
            'oauth_nonce': ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32)),
            'oauth_version': '1.0'
        }
        
        # Combine OAuth params with request params
        all_params = oauth_params.copy()
        if params:
            # Convert all params to strings and URL encode them
            for key, value in params.items():
                all_params[key] = str(value)
        
        # Create parameter string
        sorted_params = sorted(all_params.items())
        param_string = '&'.join([f"{urllib.parse.quote_plus(str(k))}={urllib.parse.quote_plus(str(v))}" for k, v in sorted_params])
        
        # Create signature base string
        base_string = f"{method.upper()}&{urllib.parse.quote_plus(url)}&{urllib.parse.quote_plus(param_string)}"
        
        # Create signing key
        signing_key = f"{urllib.parse.quote_plus(self.api_secret)}&{urllib.parse.quote_plus(self.access_token_secret)}"
        
        # Generate signature
        signature = base64.b64encode(
            hmac.new(signing_key.encode(), base_string.encode(), hashlib.sha1).digest()
        ).decode()
        
        oauth_params['oauth_signature'] = signature
        return oauth_params
    
    def get_oauth_headers(self, method: str, url: str, params: Dict = None) -> Dict[str, str]:
        """Generate OAuth 1.0a headers"""
        oauth_params = self.create_oauth_signature(method, url, params)
        
        # Create authorization header
        auth_header = 'OAuth ' + ', '.join([f'{k}="{urllib.parse.quote_plus(str(v))}"' for k, v in sorted(oauth_params.items())])
        
        return {
            "Authorization": auth_header,
            "Content-Type": "application/json"
        }
    
    def get_user_id(self, username: str) -> Optional[str]:
        """Get user ID from username using Bearer Token"""
        if not self.bearer_token:
            print("Error: Bearer token required for user lookup")
            return None
            
        url = f"{self.base_url}/users/by/username/{username}"
        headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('data', {}).get('id')
            else:
                print(f"Error getting user ID: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Error getting user ID: {e}")
            return None
    
    def get_liked_tweets(self, user_id: str, max_results: int = 25, days_back: int = 7) -> List[Dict]:
        """
        Get liked tweets for a user using OAuth 1.0a
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            print(f"Filtering tweets from the last {days_back} days (since {cutoff_date.strftime('%Y-%m-%d')})")
            
            url = f"{self.base_url}/users/{user_id}/liked_tweets"
            
            params = {
                "max_results": min(max_results, 100),
                "tweet.fields": "created_at,public_metrics,context_annotations,entities",
                "expansions": "author_id",
                "user.fields": "username,name,verified"
            }
            
            all_tweets = []
            next_token = None
            
            while len(all_tweets) < max_results:
                # Add pagination token if we have one
                current_params = params.copy()
                if next_token:
                    current_params["pagination_token"] = next_token
                
                # Create OAuth headers
                headers = self.get_oauth_headers("GET", url, current_params)
                
                # Make the request
                response = requests.get(url, headers=headers, params=current_params)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if 'data' in data:
                        tweets = data['data']
                        users = {user['id']: user for user in data.get('includes', {}).get('users', [])}
                        
                        # Filter tweets by date and enrich with author info
                        recent_tweets = []
                        for tweet in tweets:
                            # Check if tweet is within date range
                            if 'created_at' in tweet:
                                try:
                                    tweet_date = datetime.strptime(tweet['created_at'], '%Y-%m-%dT%H:%M:%S.%fZ')
                                    if tweet_date < cutoff_date:
                                        continue
                                except ValueError:
                                    pass
                            
                            # Add author info
                            author_id = tweet.get('author_id')
                            if author_id in users:
                                tweet['author'] = users[author_id]
                            
                            recent_tweets.append(tweet)
                        
                        all_tweets.extend(recent_tweets)
                        
                        # Check for pagination
                        meta = data.get('meta', {})
                        next_token = meta.get('next_token')
                        
                        if not next_token or len(all_tweets) >= max_results:
                            break
                            
                        # Stop if we didn't find any recent tweets
                        if len(recent_tweets) == 0:
                            print(f"No more tweets found within {days_back} days")
                            break
                    else:
                        break
                        
                elif response.status_code == 401:
                    print(f"❌ Unauthorized (401): Check your OAuth credentials")
                    print(f"Response: {response.text}")
                    break
                elif response.status_code == 403:
                    print(f"❌ Forbidden (403): Your app may not have permission to access liked tweets")
                    print(f"Response: {response.text}")
                    break
                else:
                    print(f"Error fetching liked tweets: {response.status_code} - {response.text}")
                    break
            
            filtered_tweets = all_tweets[:max_results]
            print(f"Found {len(filtered_tweets)} tweets from the last {days_back} days")
            return filtered_tweets
            
        except Exception as e:
            print(f"Error fetching liked tweets: {e}")
            return []
    
    
    def save_tweets_to_file(self, tweets: List[Dict], filename: str = "liked_tweets.json"):
        """Save tweets to a JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(tweets, f, indent=2, ensure_ascii=False, default=str)
        print(f"Saved {len(tweets)} tweets to {filename}")


def main():
    """Test the OAuth Twitter client"""
    try:
        client = TwitterClientOAuth()
        
        username = os.getenv('X_USERNAME')
        if not username:
            print("Please set X_USERNAME in your .env file")
            return
        
        print(f"Getting user ID for @{username}...")
        user_id = client.get_user_id(username)
        
        if user_id:
            print(f"✅ User ID: {user_id}")
            print("Fetching liked tweets with OAuth 1.0a...")
            
            tweets = client.get_liked_tweets(user_id, max_results=10, days_back=7)
            
            if tweets:
                print(f"✅ Successfully fetched {len(tweets)} liked tweets!")
                client.save_tweets_to_file(tweets)
                
                # Show preview
                print("\nPreview:")
                for i, tweet in enumerate(tweets[:2]):
                    author = tweet.get('author', {})
                    print(f"{i+1}. @{author.get('username', 'unknown')}: {tweet['text'][:80]}...")
            else:
                print("❌ No tweets found")
        else:
            print("❌ Could not get user ID")
            
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()