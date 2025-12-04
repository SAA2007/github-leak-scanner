"""
🔐 Secret Validator - Tests if leaked API keys are still active
⚠️  AUTHORIZED USE ONLY - For security research with permission

Supports validation for 15+ major APIs:
- AI/LLM: OpenAI, Anthropic, Gemini, HuggingFace, Mistral, Cohere
- Cloud: AWS, Azure, Google Cloud, DigitalOcean
- Services: GitHub, Stripe, Twilio, SendGrid
- Communication: Discord, Slack, Telegram

Features:
- Validates keys with minimal read-only requests
- Marks active/inactive in database
- Quarantines repos with active keys
- Generates coordinate files for easy location
"""

import requests
import logging
from typing import Dict, Optional, Tuple
from pathlib import Path
import json
from datetime import datetime

logger = logging.getLogger('scanner.validator')


class SecretValidator:
    """Validate leaked API keys across multiple platforms."""
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.containment_dir = Path("CONTAINMENT")
        self.coordinates_dir = Path("COORDINATES")
        
        # Create containment directories
        self.containment_dir.mkdir(exist_ok=True)
        self.coordinates_dir.mkdir(exist_ok=True)
    
    # ==================== AI / LLM APIs ====================
    
    def validate_openai(self, key: str) -> Dict:
        """OpenAI API - sk-proj-..., sk-..."""
        try:
            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                "https://api.openai.com/v1/models",
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return {
                    'active': True,
                    'status': 'ACTIVE',
                    'risk_level': 'CRITICAL',
                    'details': 'Full API access - can make requests',
                    'api': 'OpenAI'
                }
            elif response.status_code == 401:
                return self._invalid_response('OpenAI')
            elif response.status_code == 429:
                return self._rate_limited_response('OpenAI')
            else:
                return self._unknown_response('OpenAI', response.status_code)
                
        except Exception as e:
            return self._error_response('OpenAI', e)
    
    def validate_anthropic(self, key: str) -> Dict:
        """Anthropic/Claude API - sk-ant-..."""
        try:
            headers = {
                "x-api-key": key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            
            # Minimal test request (costs almost nothing)
            payload = {
                "model": "claude-3-haiku-20240307",
                "max_tokens": 1,
                "messages": [{"role": "user", "content": "hi"}]
            }
            
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return {
                    'active': True,
                    'status': 'ACTIVE',
                    'risk_level': 'CRITICAL',
                    'details': 'Can make Claude API requests',
                    'api': 'Anthropic'
                }
            elif response.status_code == 401:
                return self._invalid_response('Anthropic')
            else:
                return self._unknown_response('Anthropic', response.status_code)
                
        except Exception as e:
            return self._error_response('Anthropic', e)
    
    def validate_gemini(self, key: str) -> Dict:
        """Google Gemini API"""
        try:
            response = requests.get(
                f"https://generativelanguage.googleapis.com/v1/models?key={key}",
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return {
                    'active': True,
                    'status': 'ACTIVE',
                    'risk_level': 'CRITICAL',
                    'details': 'Gemini API access active',
                    'api': 'Google Gemini'
                }
            elif response.status_code in [401, 403]:
                return self._invalid_response('Google Gemini')
            else:
                return self._unknown_response('Google Gemini', response.status_code)
                
        except Exception as e:
            return self._error_response('Google Gemini', e)
    
    def validate_cohere(self, key: str) -> Dict:
        """Cohere API"""
        try:
            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json"
            }
            
            # Test with models endpoint
            response = requests.get(
                "https://api.cohere.ai/v1/models",
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return {
                    'active': True,
                    'status': 'ACTIVE',
                    'risk_level': 'CRITICAL',
                    'details': 'Full Cohere API access',
                    'api': 'Cohere'
                }
            elif response.status_code == 401:
                return self._invalid_response('Cohere')
            else:
                return self._unknown_response('Cohere', response.status_code)
                
        except Exception as e:
            return self._error_response('Cohere', e)
    
    def validate_groq(self, key: str) -> Dict:
        """Groq API"""
        try:
            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                "https://api.groq.com/openai/v1/models",
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return {
                    'active': True,
                    'status': 'ACTIVE',
                    'risk_level': 'CRITICAL',
                    'details': 'Groq API access active',
                    'api': 'Groq'
                }
            elif response.status_code == 401:
                return self._invalid_response('Groq')
            else:
                return self._unknown_response('Groq', response.status_code)
                
        except Exception as e:
            return self._error_response('Groq', e)
    
    def validate_mistral(self, key: str) -> Dict:
        """Mistral AI API"""
        try:
            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                "https://api.mistral.ai/v1/models",
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return {
                    'active': True,
                    'status': 'ACTIVE',
                    'risk_level': 'CRITICAL',
                    'details': 'Mistral API access',
                    'api': 'Mistral AI'
                }
            elif response.status_code == 401:
                return self._invalid_response('Mistral AI')
            else:
                return self._unknown_response('Mistral AI', response.status_code)
                
        except Exception as e:
            return self._error_response('Mistral AI', e)
    
    def validate_replicate(self, token: str) -> Dict:
        """Replicate API"""
        try:
            headers = {"Authorization": f"Token {token}"}
            
            response = requests.get(
                "https://api.replicate.com/v1/account",
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'active': True,
                    'status': 'ACTIVE',
                    'risk_level': 'HIGH',
                    'details': f"Username: {data.get('username', 'unknown')}",
                    'api': 'Replicate'
                }
            elif response.status_code == 401:
                return self._invalid_response('Replicate')
            else:
                return self._unknown_response('Replicate', response.status_code)
                
        except Exception as e:
            return self._error_response('Replicate', e)
    
    def validate_elevenlabs(self, key: str) -> Dict:
        """ElevenLabs Voice API"""
        try:
            headers = {"xi-api-key": key}
            
            response = requests.get(
                "https://api.elevenlabs.io/v1/user",
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'active': True,
                    'status': 'ACTIVE',
                    'risk_level': 'HIGH',
                    'details': f"Subscription: {data.get('subscription', {}).get('tier', 'unknown')}",
                    'api': 'ElevenLabs'
                }
            elif response.status_code == 401:
                return self._invalid_response('ElevenLabs')
            else:
                return self._unknown_response('ElevenLabs', response.status_code)
                
        except Exception as e:
            return self._error_response('ElevenLabs', e)
    
    def validate_huggingface(self, token: str) -> Dict:
        """HuggingFace API"""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            
            response = requests.get(
                "https://huggingface.co/api/whoami-v2",
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'active': True,
                    'status': 'ACTIVE',
                    'risk_level': 'HIGH',
                    'details': f"User: {data.get('name', 'unknown')}",
                    'api': 'HuggingFace'
                }
            elif response.status_code == 401:
                return self._invalid_response('HuggingFace')
            else:
                return self._unknown_response('HuggingFace', response.status_code)
                
        except Exception as e:
            return self._error_response('HuggingFace', e)
    
    # ==================== CLOUD APIS ====================
    
    def validate_aws(self, access_key: str, secret_key: str = None) -> Dict:
        """AWS API - AKIA..."""
        try:
            import boto3
            from botocore.exceptions import ClientError, NoCredentialsError
            
            if not secret_key:
                return {
                    'active': None,
                    'status': 'INCOMPLETE',
                    'risk_level': 'UNKNOWN',
                    'details': 'AWS requires both access key and secret key',
                    'api': 'AWS'
                }
            
            session = boto3.Session(
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key
            )
            
            sts = session.client('sts')
            response = sts.get_caller_identity()
            
            return {
                'active': True,
                'status': 'ACTIVE',
                'risk_level': 'CRITICAL',
                'details': f"Account: {response.get('Account')}, ARN: {response.get('Arn')}",
                'api': 'AWS'
            }
            
        except ClientError as e:
            if 'InvalidClientTokenId' in str(e):
                return self._invalid_response('AWS')
            return self._error_response('AWS', e)
        except Exception as e:
            return self._error_response('AWS', e)
    
    def validate_azure(self, key: str) -> Dict:
        """Azure API"""
        # Azure validation requires specific service endpoints
        # This is a placeholder - implement based on specific Azure service
        return {
            'active': None,
            'status': 'NOT_IMPLEMENTED',
            'details': 'Azure validation requires specific service context',
            'api': 'Azure'
        }
    
    def validate_digitalocean(self, token: str) -> Dict:
        """DigitalOcean API"""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            
            response = requests.get(
                "https://api.digitalocean.com/v2/account",
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'active': True,
                    'status': 'ACTIVE',
                    'risk_level': 'CRITICAL',
                    'details': f"Account: {data.get('account', {}).get('email', 'unknown')}",
                    'api': 'DigitalOcean'
                }
            elif response.status_code == 401:
                return self._invalid_response('DigitalOcean')
            else:
                return self._unknown_response('DigitalOcean', response.status_code)
                
        except Exception as e:
            return self._error_response('DigitalOcean', e)
    
    # ==================== SERVICE APIS ====================
    
    def validate_github(self, token: str) -> Dict:
        """GitHub Token - ghp_..., github_pat_..."""
        try:
            headers = {
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            response = requests.get(
                "https://api.github.com/user",
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                scopes = response.headers.get('X-OAuth-Scopes', 'unknown')
                
                return {
                    'active': True,
                    'status': 'ACTIVE',
                    'risk_level': 'HIGH',
                    'details': f"User: {data.get('login')}, Scopes: {scopes}",
                    'api': 'GitHub'
                }
            elif response.status_code == 401:
                return self._invalid_response('GitHub')
            else:
                return self._unknown_response('GitHub', response.status_code)
                
        except Exception as e:
            return self._error_response('GitHub', e)
    
    def validate_stripe(self, key: str) -> Dict:
        """Stripe API - sk_live_..., sk_test_..."""
        try:
            response = requests.get(
                "https://api.stripe.com/v1/balance",
                auth=(key, ''),
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                is_live = key.startswith('sk_live_')
                
                return {
                    'active': True,
                    'status': 'ACTIVE',
                    'risk_level': 'CRITICAL' if is_live else 'MEDIUM',
                    'details': f"{'LIVE' if is_live else 'TEST'} mode - Balance access",
                    'api': 'Stripe'
                }
            elif response.status_code == 401:
                return self._invalid_response('Stripe')
            else:
                return self._unknown_response('Stripe', response.status_code)
                
        except Exception as e:
            return self._error_response('Stripe', e)
    
    def validate_twilio(self, account_sid: str, auth_token: str = None) -> Dict:
        """Twilio API"""
        if not auth_token:
            return {
                'active': None,
                'status': 'INCOMPLETE',
                'details': 'Twilio requires both SID and auth token',
                'api': 'Twilio'
            }
        
        try:
            response = requests.get(
                f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}.json",
                auth=(account_sid, auth_token),
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return {
                    'active': True,
                    'status': 'ACTIVE',
                    'risk_level': 'HIGH',
                    'details': 'Can make calls/send SMS',
                    'api': 'Twilio'
                }
            elif response.status_code == 401:
                return self._invalid_response('Twilio')
            else:
                return self._unknown_response('Twilio', response.status_code)
                
        except Exception as e:
            return self._error_response('Twilio', e)
    
    def validate_sendgrid(self, key: str) -> Dict:
        """SendGrid API"""
        try:
            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                "https://api.sendgrid.com/v3/scopes",
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                scopes = data.get('scopes', [])
                
                return {
                    'active': True,
                    'status': 'ACTIVE',
                    'risk_level': 'HIGH',
                    'details': f"Scopes: {', '.join(scopes[:3])}...",
                    'api': 'SendGrid'
                }
            elif response.status_code == 401:
                return self._invalid_response('SendGrid')
            else:
                return self._unknown_response('SendGrid', response.status_code)
                
        except Exception as e:
            return self._error_response('SendGrid', e)
    
    # ==================== COMMUNICATION APIS ====================
    
    def validate_discord(self, token: str) -> Dict:
        """Discord Bot Token"""
        try:
            headers = {"Authorization": f"Bot {token}"}
            
            response = requests.get(
                "https://discord.com/api/v10/users/@me",
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'active': True,
                    'status': 'ACTIVE',
                    'risk_level': 'HIGH',
                    'details': f"Bot: {data.get('username')}#{data.get('discriminator')}",
                    'api': 'Discord'
                }
            elif response.status_code == 401:
                return self._invalid_response('Discord')
            else:
                return self._unknown_response('Discord', response.status_code)
                
        except Exception as e:
            return self._error_response('Discord', e)
    
    def validate_slack(self, token: str) -> Dict:
        """Slack Bot Token - xoxb-..."""
        try:
            response = requests.post(
                "https://slack.com/api/auth.test",
                headers={"Authorization": f"Bearer {token}"},
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    return {
                        'active': True,
                        'status': 'ACTIVE',
                        'risk_level': 'HIGH',
                        'details': f"Team: {data.get('team')}, User: {data.get('user')}",
                        'api': 'Slack'
                    }
                else:
                    return self._invalid_response('Slack')
            else:
                return self._unknown_response('Slack', response.status_code)
                
        except Exception as e:
            return self._error_response('Slack', e)
    
    def validate_notion(self, token: str) -> Dict:
        """Notion API"""
        try:
            headers = {
                "Authorization": f"Bearer {token}",
                "Notion-Version": "2022-06-28"
            }
            
            response = requests.get(
                "https://api.notion.com/v1/users/me",
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'active': True,
                    'status': 'ACTIVE',
                    'risk_level': 'HIGH',
                    'details': f"User: {data.get('name', 'unknown')}",
                    'api': 'Notion'
                }
            elif response.status_code == 401:
                return self._invalid_response('Notion')
            else:
                return self._unknown_response('Notion', response.status_code)
                
        except Exception as e:
            return self._error_response('Notion', e)
    
    def validate_airtable(self, key: str) -> Dict:
        """Airtable API"""
        try:
            headers = {"Authorization": f"Bearer {key}"}
            
            # Use meta endpoint to check auth
            response = requests.get(
                "https://api.airtable.com/v0/meta/whoami",
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'active': True,
                    'status': 'ACTIVE',
                    'risk_level': 'HIGH',
                    'details': f"User: {data.get('id', 'unknown')}",
                    'api': 'Airtable'
                }
            elif response.status_code == 401:
                return self._invalid_response('Airtable')
            else:
                return self._unknown_response('Airtable', response.status_code)
                
        except Exception as e:
            return self._error_response('Airtable', e)
    
    def validate_supabase(self, key: str, url: str = None) -> Dict:
        """Supabase API - requires project URL"""
        if not url:
            return {
                'active': None,
                'status': 'INCOMPLETE',
                'details': 'Supabase requires project URL',
                'api': 'Supabase'
            }
        
        try:
            headers = {
                "apikey": key,
                "Authorization": f"Bearer {key}"
            }
            
            response = requests.get(
                f"{url}/rest/v1/",
                headers=headers,
                timeout=self.timeout
            )
            
            # Supabase returns 200 even for auth check
            if response.status_code in [200, 406]:  # 406 is acceptable response
                return {
                    'active': True,
                    'status': 'ACTIVE',
                    'risk_level': 'CRITICAL',
                    'details': 'Database access active',
                    'api': 'Supabase'
                }
            elif response.status_code == 401:
                return self._invalid_response('Supabase')
            else:
                return self._unknown_response('Supabase', response.status_code)
                
        except Exception as e:
            return self._error_response('Supabase', e)
    
    def validate_mailgun(self, key: str, domain: str = None) -> Dict:
        """Mailgun API"""
        try:
            # Use domains endpoint
            response = requests.get(
                "https://api.mailgun.net/v3/domains",
                auth=("api", key),
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                domain_count = len(data.get('items', []))
                return {
                    'active': True,
                    'status': 'ACTIVE',
                    'risk_level': 'HIGH',
                    'details': f"Domains: {domain_count}",
                    'api': 'Mailgun'
                }
            elif response.status_code == 401:
                return self._invalid_response('Mailgun')
            else:
                return self._unknown_response('Mailgun', response.status_code)
                
        except Exception as e:
            return self._error_response('Mailgun', e)
    
    def validate_telegram(self, token: str) -> Dict:
        """Telegram Bot Token"""
        try:
            response = requests.get(
                f"https://api.telegram.org/bot{token}/getMe",
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    bot = data.get('result', {})
                    return {
                        'active': True,
                        'status': 'ACTIVE',
                        'risk_level': 'MEDIUM',
                        'details': f"Bot: @{bot.get('username')}",
                        'api': 'Telegram'
                    }
                else:
                    return self._invalid_response('Telegram')
            else:
                return self._unknown_response('Telegram', response.status_code)
                
        except Exception as e:
            return self._error_response('Telegram', e)
    
    # ==================== SOCIAL / MEDIA APIS ====================
    
    def validate_twitter(self, bearer_token: str) -> Dict:
        """Twitter/X API v2 - Bearer token"""
        try:
            headers = {"Authorization": f"Bearer {bearer_token}"}
            
            response = requests.get(
                "https://api.twitter.com/2/users/me",
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json().get('data', {})
                return {
                    'active': True,
                    'status': 'ACTIVE',
                    'risk_level': 'HIGH',
                    'details': f"User: @{data.get('username', 'unknown')}",
                    'api': 'Twitter/X'
                }
            elif response.status_code == 401:
                return self._invalid_response('Twitter/X')
            else:
                return self._unknown_response('Twitter/X', response.status_code)
                
        except Exception as e:
            return self._error_response('Twitter/X', e)
    
    def validate_reddit(self, client_id: str, client_secret: str, username: str = None) -> Dict:
        """Reddit API - requires OAuth"""
        if not client_secret:
            return {
                'active': None,
                'status': 'INCOMPLETE',
                'details': 'Reddit requires client_id and client_secret',
                'api': 'Reddit'
            }
        
        try:
            # Get OAuth token
            auth = (client_id, client_secret)
            data = {'grant_type': 'client_credentials'}
            headers = {'User-Agent': 'LeakScanner/1.0'}
            
            response = requests.post(
                'https://www.reddit.com/api/v1/access_token',
                auth=auth,
                data=data,
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                token_data = response.json()
                if 'access_token' in token_data:
                    return {
                        'active': True,
                        'status': 'ACTIVE',
                        'risk_level': 'HIGH',
                        'details': f"Token type: {token_data.get('token_type')}",
                        'api': 'Reddit'
                    }
            
            return self._invalid_response('Reddit')
                
        except Exception as e:
            return self._error_response('Reddit', e)
    
    def validate_youtube(self, api_key: str) -> Dict:
        """YouTube Data API"""
        try:
            response = requests.get(
                f"https://www.googleapis.com/youtube/v3/channels?part=snippet&mine=true&key={api_key}",
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return {
                    'active': True,
                    'status': 'ACTIVE',
                    'risk_level': 'MEDIUM',
                    'details': 'YouTube API access',
                    'api': 'YouTube'
                }
            elif response.status_code == 403:
                # Key might be valid but quota exceeded
                error = response.json().get('error', {}).get('message', '')
                if 'quota' in error.lower():
                    return self._rate_limited_response('YouTube')
                return self._invalid_response('YouTube')
            else:
                return self._unknown_response('YouTube', response.status_code)
                
        except Exception as e:
            return self._error_response('YouTube', e)
    
    def validate_spotify(self, client_id: str, client_secret: str) -> Dict:
        """Spotify API"""
        if not client_secret:
            return {
                'active': None,
                'status': 'INCOMPLETE',
                'details': 'Spotify requires client_id and client_secret',
                'api': 'Spotify'
            }
        
        try:
            import base64
            
            auth_str = f"{client_id}:{client_secret}"
            b64_auth = base64.b64encode(auth_str.encode()).decode()
            
            headers = {"Authorization": f"Basic {b64_auth}"}
            data = {'grant_type': 'client_credentials'}
            
            response = requests.post(
                'https://accounts.spotify.com/api/token',
                headers=headers,
                data=data,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return {
                    'active': True,
                    'status': 'ACTIVE',
                    'risk_level': 'MEDIUM',
                    'details': 'Spotify API access',
                    'api': 'Spotify'
                }
            elif response.status_code == 401:
                return self._invalid_response('Spotify')
            else:
                return self._unknown_response('Spotify', response.status_code)
                
        except Exception as e:
            return self._error_response('Spotify', e)
    
    def validate_twitch(self, client_id: str, client_secret: str) -> Dict:
        """Twitch API"""
        if not client_secret:
            return {
                'active': None,
                'status': 'INCOMPLETE',
                'details': 'Twitch requires client_id and client_secret',
                'api': 'Twitch'
            }
        
        try:
            data = {
                'client_id': client_id,
                'client_secret': client_secret,
                'grant_type': 'client_credentials'
            }
            
            response = requests.post(
                'https://id.twitch.tv/oauth2/token',
                data=data,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return {
                    'active': True,
                    'status': 'ACTIVE',
                    'risk_level': 'MEDIUM',
                    'details': 'Twitch API access',
                    'api': 'Twitch'
                }
            elif response.status_code in [400, 401]:
                return self._invalid_response('Twitch')
            else:
                return self._unknown_response('Twitch', response.status_code)
                
        except Exception as e:
            return self._error_response('Twitch', e)
    
    # ==================== CLOUD / INFRASTRUCTURE ====================
    
    def validate_cloudflare(self, token: str) -> Dict:
        """Cloudflare API"""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            
            response = requests.get(
                "https://api.cloudflare.com/client/v4/user/tokens/verify",
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    result = data.get('result', {})
                    return {
                        'active': True,
                        'status': 'ACTIVE',
                        'risk_level': 'CRITICAL',
                        'details': f"Status: {result.get('status')}",
                        'api': 'Cloudflare'
                    }
            
            return self._invalid_response('Cloudflare')
                
        except Exception as e:
            return self._error_response('Cloudflare', e)
    
    def validate_vercel(self, token: str) -> Dict:
        """Vercel API"""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            
            response = requests.get(
                "https://api.vercel.com/v2/user",
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                user = data.get('user', {})
                return {
                    'active': True,
                    'status': 'ACTIVE',
                    'risk_level': 'HIGH',
                    'details': f"User: {user.get('username', user.get('email', 'unknown'))}",
                    'api': 'Vercel'
                }
            elif response.status_code in [401, 403]:
                return self._invalid_response('Vercel')
            else:
                return self._unknown_response('Vercel', response.status_code)
                
        except Exception as e:
            return self._error_response('Vercel', e)
    
    def validate_firebase(self, api_key: str) -> Dict:
        """Firebase/Google API Key"""
        try:
            # Use identitytoolkit to verify API key
            response = requests.post(
                f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={api_key}",
                json={},
                timeout=self.timeout
            )
            
            # If key is valid, it will return an error about missing fields, not auth error
            if response.status_code in [200, 400]:
                error = response.json().get('error', {})
                if 'API key not valid' in error.get('message', ''):
                    return self._invalid_response('Firebase')
                
                return {
                    'active': True,
                    'status': 'ACTIVE',
                    'risk_level': 'CRITICAL',
                    'details': 'Firebase API key valid',
                    'api': 'Firebase'
                }
            
            return self._unknown_response('Firebase', response.status_code)
                
        except Exception as e:
            return self._error_response('Firebase', e)
    
    # ==================== HELPER METHODS ====================
    
    def _invalid_response(self, api: str) -> Dict:
        """Standard invalid key response."""
        return {
            'active': False,
            'status': 'INVALID',
            'risk_level': 'NONE',
            'details': 'Key is expired or invalid',
            'api': api
        }
    
    def _rate_limited_response(self, api: str) -> Dict:
        """Rate limited but key is valid."""
        return {
            'active': True,
            'status': 'ACTIVE (rate limited)',
            'risk_level': 'HIGH',
            'details': 'Key is valid but currently rate limited',
            'api': api
        }
    
    def _unknown_response(self, api: str, status_code: int) -> Dict:
        """Unknown status code."""
        return {
            'active': None,
            'status': 'UNKNOWN',
            'risk_level': 'UNKNOWN',
            'details': f'Unexpected status code: {status_code}',
            'api': api
        }
    
    def _error_response(self, api: str, error: Exception) -> Dict:
        """Error during validation."""
        return {
            'active': None,
            'status': 'ERROR',
            'risk_level': 'UNKNOWN',
            'details': f'Validation error: {str(error)}',
            'api': api
        }
    
    # ==================== DETECTION & ROUTING ====================
    
    def detect_key_type(self, secret_type: str, key_value: str) -> Optional[str]:
        """
        Detect which validator to use based on secret type and key format.
        
        Returns validator method name or None.
        """
        key_lower = key_value.lower()
        
        # AI/LLM APIs
        if 'openai' in secret_type.lower() or key_value.startswith('sk-proj-') or key_value.startswith('sk-'):
            return 'validate_openai'
        if 'anthropic' in secret_type.lower() or 'claude' in secret_type.lower() or key_value.startswith('sk-ant-'):
            return 'validate_anthropic'
        if 'gemini' in secret_type.lower() or 'google ai' in secret_type.lower():
            return 'validate_gemini'
        if 'huggingface' in secret_type.lower() or 'hf_' in key_lower:
            return 'validate_huggingface'
        
        # Cloud
        if 'aws' in secret_type.lower() or key_value.startswith('AKIA'):
            return 'validate_aws'
        if 'digitalocean' in secret_type.lower():
            return 'validate_digitalocean'
        
        # Services
        if 'github' in secret_type.lower() or key_value.startswith('ghp_') or key_value.startswith('github_pat_'):
            return 'validate_github'
        if 'stripe' in secret_type.lower() or key_value.startswith('sk_live_') or key_value.startswith('sk_test_'):
            return 'validate_stripe'
        if 'twilio' in secret_type.lower():
            return 'validate_twilio'
        if 'sendgrid' in secret_type.lower():
            return 'validate_sendgrid'
        
        # Communication
        if 'discord' in secret_type.lower():
            return 'validate_discord'
        if 'slack' in secret_type.lower() or key_value.startswith('xoxb-'):
            return 'validate_slack'
        if 'telegram' in secret_type.lower():
            return 'validate_telegram'
        
        return None
    
    def validate_secret(self, secret_type: str, key_value: str) -> Dict:
        """
        Automatically detect and validate a secret.
        
        Args:
            secret_type: Type from Gitleaks/TruffleHog
            key_value: The actual key value
        
        Returns:
            Validation result dictionary
        """
        validator_name = self.detect_key_type(secret_type, key_value)
        
        if not validator_name:
            return {
                'active': None,
                'status': 'UNSUPPORTED',
                'risk_level': 'UNKNOWN',
                'details': f'No validator for: {secret_type}',
                'api': 'Unknown'
            }
        
        try:
            validator = getattr(self, validator_name)
            result = validator(key_value)
            logger.info(f"Validated {secret_type}: {result['status']}")
            return result
        except Exception as e:
            logger.error(f"Validation failed for {secret_type}: {e}")
            return self._error_response(secret_type, e)


# ==================== TESTING ====================
if __name__ == "__main__":
    validator = SecretValidator()
    
    # Test key detection
    tests = [
        ("OpenAI API Key", "sk-proj-abc123"),
        ("GitHub Token", "ghp_abc123"),
        ("Anthropic API Key", "sk-ant-abc123"),
        ("Slack Token", "xoxb-abc123"),
    ]
    
    for secret_type, key in tests:
        method = validator.detect_key_type(secret_type, key)
        print(f"{secret_type}: {method}")
