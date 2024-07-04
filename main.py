import os
import re
from dotenv import load_dotenv
import tweepy
import tldextract
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import logging
from linkedin_api import Linkedin
import instaloader
from facebook_scraper import get_profile
from urllib.parse import urlparse
from tweepy.errors import TweepyException

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="Lead Qualification Machine")

# Configure logging
logging.basicConfig(filename='lead_qualification.log', level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')

class LeadInput(BaseModel):
    id: int
    name: str
    age: int
    email: str
    city: str
    state: str
    income: str
    linkedin_url: Optional[str] = None
    instagram_username: Optional[str] = None
    facebook_url: Optional[str] = None
    twitter_username: Optional[str] = None

class QualifiedLead(BaseModel):
    id: int
    name: str
    age: int
    email: str
    city: str
    state: str
    income: str
    score: float
    employment: Optional[str] = None
    linkedin_summary: Optional[dict] = None
    instagram_summary: Optional[dict] = None
    facebook_summary: Optional[dict] = None
    twitter_summary: Optional[dict] = None
    qualification_summary: str

class LeadQualificationMachine:
    def __init__(self):
        self.insta_loader = instaloader.Instaloader()
        
    # Twitter authentication
    twitter_api_key = os.getenv('TWITTER_API_KEY')
    twitter_api_secret = os.getenv('TWITTER_API_SECRET')
    twitter_access_token = os.getenv('TWITTER_ACCESS_TOKEN')
    twitter_access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
    twitter_bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
    
    if all([twitter_api_key, twitter_api_secret, twitter_access_token, twitter_access_token_secret, twitter_bearer_token]):
        self.twitter_client = tweepy.Client(
            consumer_key=twitter_api_key, 
            consumer_secret=twitter_api_secret,
            access_token=twitter_access_token, 
            access_token_secret=twitter_access_token_secret,
            bearer_token=twitter_bearer_token
        )
    else:
        logging.warning("Twitter credentials not fully provided. Twitter scraping will be limited.")
        self.twitter_client = None

        # LinkedIn initialization
        linkedin_email = os.getenv('LINKEDIN_EMAIL')
        linkedin_password = os.getenv('LINKEDIN_PASSWORD')
        if linkedin_email and linkedin_password:
            try:
                self.linkedin = Linkedin(linkedin_email, linkedin_password)
            except Exception as e:
                logging.error(f"Failed to initialize LinkedIn: {str(e)}")
                self.linkedin = None
        else:
            logging.info("LinkedIn credentials not provided. LinkedIn scraping will be skipped.")
            self.linkedin = None
        
        self.personal_email_domains = set(['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'aol.com'])

    def analyze_email_domain(self, email):
        extracted = tldextract.extract(email.split('@')[1])
        domain = extracted.domain + '.' + extracted.suffix
        if domain not in self.personal_email_domains:
            return domain
        return None

    def linkedin_scrape(self, profile_url):
        if self.linkedin is None:
            return {"error": "LinkedIn scraping is not configured", "employment": self.extract_company_from_url(profile_url)}
        try:
            profile = self.linkedin.get_profile(profile_url)
            employment = profile.get('experiences', [{}])[0].get('companyName', 'Unknown') if profile.get('experiences') else 'Unknown'
            return {
                'employment': employment,
                'industry': profile.get('industryName', 'Unknown'),
                'positions': profile.get('positions', []),
                'education': profile.get('education', []),
                'skills': profile.get('skills', [])
            }
        except Exception as e:
            logging.error(f"Error scraping LinkedIn profile {profile_url}: {e}")
            return {"error": str(e), "employment": self.extract_company_from_url(profile_url)}

    def extract_company_from_url(self, url):
        parsed_url = urlparse(url)
        path_parts = parsed_url.path.split('/')
        if len(path_parts) > 2:
            return path_parts[2].replace('-', ' ').title()
        return "Unknown"

    def instagram_scrape(self, username):
        try:
            profile = instaloader.Profile.from_username(self.insta_loader.context, username)
            return {
                'followers': profile.followers,
                'following': profile.followees,
                'posts_count': profile.mediacount,
                'bio': profile.biography
            }
        except Exception as e:
            logging.error(f"Error scraping Instagram profile {username}: {e}")
            return {"error": str(e)}

    def facebook_scrape(self, profile_url):
        try:
            # Normalize the Facebook URL
            if 'm.facebook.com' in profile_url:
                profile_url = profile_url.replace('m.facebook.com', 'www.facebook.com')
            elif 'facebook.com' not in profile_url:
                profile_url = f'https://www.facebook.com/{profile_url}'

            profile = get_profile(profile_url)
            return {
                'friends': str(profile.get('Friends', 'Unknown')),
                'about': profile.get('About', 'No information available'),
                'posts_count': len(profile.get('Posts', []))
            }
        except Exception as e:
            logging.error(f"Error scraping Facebook profile {profile_url}: {e}")
            return {"error": f"Facebook scraping failed: {str(e)}"}

    def twitter_scrape(self, username):
        if self.twitter_client is None:
            return {"error": "Twitter API is not configured"}
        try:
            # Lookup user by username
            user = self.twitter_client.get_user(username=username, 
                                                user_fields=['public_metrics', 'description', 'created_at'])
            
            if user.data:
                user_data = user.data
                
                # Get recent tweets
                tweets = self.twitter_client.get_users_tweets(user_data.id, max_results=10, 
                                                              tweet_fields=['created_at', 'public_metrics'])
                recent_tweets = [tweet.text for tweet in tweets.data] if tweets.data else []

                return {
                    'id': user_data.id,
                    'name': user_data.name,
                    'username': user_data.username,
                    'followers': user_data.public_metrics['followers_count'],
                    'following': user_data.public_metrics['following_count'],
                    'tweets_count': user_data.public_metrics['tweet_count'],
                    'description': user_data.description,
                    'created_at': user_data.created_at,
                    'recent_tweets': recent_tweets
                }
            else:
                return {"error": "User not found"}
        except TweepyException as e:
            logging.error(f"Error scraping Twitter profile {username}: {e}")
            return {"error": f"Twitter scraping failed: {str(e)}"}
    def calculate_score(self, lead, linkedin_data, instagram_data, facebook_data, twitter_data, work_email_domain):
        score = 0
        reasons = []

        # Income scoring
        income_str = lead.income.replace('$', '').replace('K', '000').replace('M', '000000')
        income_value = float(income_str.split(' - ')[0]) if ' - ' in income_str else float(income_str)
        income_score = min(income_value / 5000, 30)  # Increased max points for income
        score += income_score
        reasons.append(f"Income: +{income_score:.1f} points")

        # Work email scoring
        if work_email_domain:
            work_email_score = 15
            score += work_email_score
            reasons.append(f"Work email domain ({work_email_domain}): +{work_email_score} points")

        # LinkedIn scoring
        if isinstance(linkedin_data, dict) and 'error' not in linkedin_data:
            linkedin_score = min(len(linkedin_data.get('skills', [])) * 0.5 + len(linkedin_data.get('positions', [])) * 2, 25)
            score += linkedin_score
            reasons.append(f"LinkedIn profile: +{linkedin_score:.1f} points")
        elif 'employment' in linkedin_data:
            fallback_score = 5
            score += fallback_score
            reasons.append(f"LinkedIn fallback (derived from URL): +{fallback_score} points")

        # Social media influence scoring
        if isinstance(instagram_data, dict) and 'followers' in instagram_data:
            insta_score = min(instagram_data['followers'] / 500, 10)  # Adjusted for more points
            score += insta_score
            reasons.append(f"Instagram followers: +{insta_score:.1f} points")
        
        if isinstance(facebook_data, dict) and 'friends' in facebook_data:
            try:
                friends = int(facebook_data['friends']) if facebook_data['friends'] != 'Unknown' else 0
                fb_score = min(friends / 50, 10)  # Adjusted for more points
                score += fb_score
                reasons.append(f"Facebook friends: +{fb_score:.1f} points")
            except ValueError:
                logging.warning(f"Invalid Facebook friends value: {facebook_data['friends']}")
        
        if isinstance(twitter_data, dict) and 'followers' in twitter_data:
            twitter_score = min(twitter_data['followers'] / 500, 10)  # Adjusted for more points
            score += twitter_score
            reasons.append(f"Twitter followers: +{twitter_score:.1f} points")

        return min(score, 100), reasons

    def generate_summary(self, lead, score, reasons, employment, linkedin_data, instagram_data, facebook_data, twitter_data):
        summary = f"Lead Qualification Summary for {lead.name}:\n\n"
        summary += f"Overall Score: {score:.1f}/100\n"
        summary += f"Likely Employment: {employment}\n\n"
        summary += "Scoring Breakdown:\n"
        for reason in reasons:
            summary += f"- {reason}\n"
        summary += "\nProfile Highlights:\n"
        
        if isinstance(linkedin_data, dict):
            if 'error' not in linkedin_data:
                summary += f"- LinkedIn: {len(linkedin_data.get('positions', []))} positions, {len(linkedin_data.get('skills', []))} skills\n"
            else:
                summary += f"- LinkedIn: {linkedin_data.get('error', 'Unknown error')}"
                if 'employment' in linkedin_data:
                    summary += f" (Derived employment: {linkedin_data['employment']})\n"
        
        if isinstance(instagram_data, dict):
            if 'error' not in instagram_data:
                summary += f"- Instagram: {instagram_data.get('followers', 0)} followers, {instagram_data.get('posts_count', 0)} posts\n"
            else:
                summary += f"- Instagram: {instagram_data.get('error', 'Unknown error')}\n"
        
        if isinstance(facebook_data, dict):
            if 'error' not in facebook_data:
                summary += f"- Facebook: {facebook_data.get('friends', 'Unknown')} friends, {facebook_data.get('posts_count', 0)} posts\n"
            else:
                summary += f"- Facebook: {facebook_data.get('error', 'Unknown error')}\n"
        
        if isinstance(twitter_data, dict):
            if 'error' not in twitter_data:
                summary += f"- Twitter: {twitter_data.get('followers', 0)} followers, {twitter_data.get('tweets_count', 0)} tweets\n"
                if twitter_data.get('recent_tweets'):
                    summary += f"  Recent tweet sample: '{twitter_data['recent_tweets'][0]}'\n"
            else:
                summary += f"- Twitter: {twitter_data.get('error', 'Unknown error')}\n"

        return summary

    def qualify_lead(self, lead: LeadInput) -> QualifiedLead:
        linkedin_data = self.linkedin_scrape(lead.linkedin_url) if lead.linkedin_url else {"error": "No LinkedIn URL provided"}
        instagram_data = self.instagram_scrape(lead.instagram_username) if lead.instagram_username else {"error": "No Instagram username provided"}
        facebook_data = self.facebook_scrape(lead.facebook_url) if lead.facebook_url else {"error": "No Facebook URL provided"}
        twitter_data = self.twitter_scrape(lead.twitter_username) if lead.twitter_username else {"error": "No Twitter username provided"}

        work_email_domain = self.analyze_email_domain(lead.email)
        score, reasons = self.calculate_score(lead, linkedin_data, instagram_data, facebook_data, twitter_data, work_email_domain)

        employment = linkedin_data.get('employment', 'Unknown') if isinstance(linkedin_data, dict) and 'error' not in linkedin_data else work_email_domain or "Unknown"

        summary = self.generate_summary(lead, score, reasons, employment, linkedin_data, instagram_data, facebook_data, twitter_data)

        return QualifiedLead(
            id=lead.id,
            name=lead.name,
            age=lead.age,
            email=lead.email,
            city=lead.city,
            state=lead.state,
            income=lead.income,
            score=score,
            employment=employment,
            linkedin_summary=linkedin_data,
            instagram_summary=instagram_data,
            facebook_summary=facebook_data,
            twitter_summary=twitter_data,
            qualification_summary=summary
        )

machine = LeadQualificationMachine()

@app.post("/qualify", response_model=List[QualifiedLead])
async def qualify_leads(leads: List[LeadInput]):
    try:
        qualified_leads = [machine.qualify_lead(lead) for lead in leads]
        return qualified_leads
    except Exception as e:
        logging.error(f"Error qualifying leads: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9990)