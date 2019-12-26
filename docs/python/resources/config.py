from datetime import date



feeds = {
    'engineering': {
        'openai': 'https://blog.openai.com/rss/',
        'fb': 'https://research.fb.com/blog/feed/',
        'airbnb-ds': 'https://medium.com/feed/airbnb-engineering/tagged/data-science',
        'ggl_dev': 'http://feeds.feedburner.com/GDBcode',
        'ggl_ai': 'http://feeds.feedburner.com/blogspot/gJZg',
        'instacart': ' https://tech.instacart.com/feed',

        'Google Developers': 'http://feeds.feedburner.com/GDBcode',
        'Google Open Source': 'http://feeds.feedburner.com/GoogleOpenSourceBlog',
        'fb_code': 'https://code.fb.com/feed/',
        'uber_ai': 'https://eng.uber.com/tag/uber-ai-labs/feed',
        'uber_eng': 'https://eng.uber.com/feed',
        'netflix_tech': 'https://medium.com/feed/netflix-techblog',
        'pinterest': 'https://medium.com/feed/@Pinterest_Engineering',
        'sebrash': 'https://sebastianraschka.com/rss_feed.xml',
        'zillow': 'https://www.zillow.com/data-science/feed/',
    },
    'tutorials': {
        'databricks': 'https://databricks.com/feed',
        'datacamp': 'https://www.datacamp.com/community/rss.xml',
        'ml_mast': 'https://machinelearningmastery.com/blog/feed/',
        'twrds': 'https://towardsdatascience.com/feed/',
        'devto': 'https://dev.to/feed',
    },
    'general': {
        'gnews': 'https://news.google.com/news/rss/?hl=en&amp;ned=us&amp;gl=US&ned=us&gl=US',
        'espn': 'http://www.espn.com/espn/rss/news',
        'Science': 'http://feeds.reuters.com/reuters/scienceNews',
        'TopNews': 'http://feeds.reuters.com/reuters/topNews',
        'World News': 'http://feeds.reuters.com/Reuters/worldNews',
        'Sports News': 'http://feeds.reuters.com/reuters/sportsNews',
        'BBC': 'http://feeds.bbci.co.uk/news/video_and_audio/news_front_page/rss.xml',
        'BBC US': 'http://feeds.bbci.co.uk/news/video_and_audio/news_front_page/rss.xml?edition=us',
        'BBC International': 'http://feeds.bbci.co.uk/news/rss.xml?edition=int',
        'Snopes': 'https://www.snopes.com/feed/',
    },
    'tech': {
        'mit': 'https://www.technologyreview.com/stories.rss',
        'fc': 'https://www.fastcompany.com/technology/rss',
        'reuters': 'http://feeds.reuters.com/reuters/technologyNews',
        'bbc': 'http://feeds.bbci.co.uk/news/video_and_audio/technology/rss.xml',
        'tc': 'https://techcrunch.com/startups/',
        'vb': 'https://venturebeat.com/feed/'
    },
    'startups': {
        'avc': 'http://feeds.feedburner.com/avc',
        'andrew chen': 'https://andrewchen.co/feed/',
        'ycombinator': 'https://blog.ycombinator.com/feed/',
        'A Horowitz': 'https://a16z.com/feed/',
        'AVC': 'https://avc.com/feed/',
        'Sam Altman': 'http://blog.samaltman.com/posts.atom',

    },
    'religious': {
        'lds': 'https://www.mormonnewsroom.org/rss'
    },
}

# What categories I want
map = {
    0: [], #monday arxiv is not above, but a separate function
    1: ['tutorials'],
    2: ['general'],
    3: ['startups', 'tech'],
    4: ['engineering'],
    5: ['general'],
    6: ['religious'], #sunday
}
# TODO: add arxiv more cleanly: check main.py for implementation
feeds = {c:feeds[c] for c in map[date.today().weekday()]} # 1 = monday
