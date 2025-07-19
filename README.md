# Blog Topic Generator from Liked Tweets

A workflow that reads your liked tweets from X (Twitter) and generates blog post ideas based on your interests.

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Get X API credentials:**
   - Go to [X Developer Portal](https://developer.x.com/en/portal/dashboard)
   - Create a new app with "Read" permissions
   - Enable "OAuth 1.0a" authentication
   - Get your API Key, API Secret, Access Token, and Access Token Secret
   - Note: You need at least Basic tier ($200/month) for meaningful tweet access

3. **Get Anthropic API key:**
   - Go to [Anthropic Console](https://console.anthropic.com/)
   - Create an API key

4. **Create environment file:**
   ```bash
   cp .env.example .env
   ```
   Then edit `.env` with your credentials.

## Usage

### Full Workflow
Run the complete workflow to fetch tweets and generate topics:
```bash
python workflow.py
```

### Individual Components

**Fetch liked tweets only:**
```bash
python twitter_client.py
```

**Generate topics from existing tweet data:**
```bash
python blog_topic_generator.py
```

## Output

The workflow creates two files:
- `liked_tweets.json` - Raw tweet data
- `blog_topics.json` - Generated blog post ideas

## Configuration

Set these environment variables in your `.env` file:
- `MAX_TWEETS` - Number of tweets to analyze (default: 50)
- Other variables as shown in `.env.example`

## API Costs

- **X API:** Basic tier $200/month for 10,000 tweet reads
- **Anthropic:** ~$0.01-0.05 per workflow run (depending on tweet content)

## Notes

- The topic generator uses Claude to provide open-ended, creative suggestions
- Topics reflect your interests based on content you've engaged with
- No rigid categorization - designed for variety in writing topics