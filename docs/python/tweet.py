"""

Another way to publish a tweet using python-twitter

python-twitter
import twitter
https://developer.twitter.com/en/apps/17165693
api = twitter.Api(consumer_key=mypass.TWITTER_CONSUMER_API_KEY,
                  consumer_secret=mypass.TWITTER_CONSUMER_API_SECRET_KEY,
                  access_token_key=mypass.TWITTER_ACCESS_TOKEN,
                  access_token_secret=mypass.TWITTER_ACCESS_SECRET_TOKEN)
api.PostUpdate('hello world')

"""

import tweepy
import mypass

def create_twitter_api():
    auth = tweepy.OAuthHandler(
        mypass.TWITTER_CONSUMER_API_KEY, 
        mypass.TWITTER_CONSUMER_API_SECRET_KEY)

    auth.set_access_token(mypass.TWITTER_ACCESS_TOKEN, 
    mypass.TWITTER_ACCESS_SECRET_TOKEN)
    api = tweepy.API(auth, wait_on_rate_limit=True)
    return api

# TODO: scrape tweets: https://gist.github.com/vickyqian/f70e9ab3910c7c290d9d715491cde44c