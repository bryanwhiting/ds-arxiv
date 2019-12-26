"""

TODO: Parse cs, stat, math, etc to have "domains"
* Rank the author (with how many publications they have)
* Provide links to topic-specific articles (not just subject)

"""
import os 
import shutil
import feedparser
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from IPython.core.display import display, HTML
import pandas as pd
from datetime import datetime, timedelta, date

import sendemail
import mypass
from arxivapi import arx_dict, arx_list
from resources.config import feeds
from resources.rmdhead import rmd_template

def extract_domain(url):
    parsed_uri = urlparse(url)
    return '{uri.netloc}'.format(uri=parsed_uri).replace('www.', '').replace('.com', '')

def strip_html(text):
    return BeautifulSoup(str(text), 'html5lib').text

def parse_rss(url: str) -> pd.DataFrame:
    items = feedparser.parse(url)['items']
    # TODO:  build this into a try-catch to get "content["image"]" if possible
    tags = ['title', 'link', 'summary', 'published']
    return pd.DataFrame(items)[tags]

def arxiv_query(cat, n=20) -> dict:
    """https://arxiv.org/help/api/user-manual#Architecture"""
    sort = '&sortBy=lastUpdatedDate&sortOrder=descending'
    max_res = f'&max_results={n}'
    # q = f'http://export.arxiv.org/api/query?search_query=all:{term}{sort}{max_res}'
    q = f'http://export.arxiv.org/api/query?search_query=cat:{cat}{sort}{max_res}'
    r = requests.get(q)
    return r.text


def parse_arxiv_post(post, arx_dict):
    """Code to parse the arxiv query:

    Example:
        x = arxiv_query('cs.AI', n=2)
        y = feedparser.parse(x)['items']
        post = y[0]
        parse_arxiv_post(post)
    """

    # Extract main data
    author = post['author']
    title = post['title']
    summary = post['summary']

    # Extract the tags
    primary_tag = post['arxiv_primary_category']['term']
    primary_cat = arx_dict[primary_tag] if primary_tag in arx_dict else primary_tag 
    tags = list(set([t['term'] for t in post['tags']]))
    n_tags = len(tags)
    categories = ', '.join([arx_dict[tag] for tag in tags if tag in arx_dict])
    tags = ', '.join(tags)
    
    # Parse authors
    authors = [t['name'] for t in post['authors']]
    n_authors = len(authors)
    authors = ', '.join(authors)
    
    # Parse URLs. There are two urls:
    # [{'href': 'http://arxiv.org/abs/1912.07544v1',
    #   'rel': 'alternate',
    #   'type': 'text/html'},
    #  {'title': 'pdf',
    #   'href': 'http://arxiv.org/pdf/1912.07544v1',
    #   'rel': 'related',
    #   'type': 'application/pdf'}]
    url_pdf = [h['href'] for h in post['links'] if 'pdf' in h['href']]
    url_href = [h['href'] for h in post['links'] if 'abs' in h['href']]
    return pd.DataFrame({
        'title': title,
        'summary': summary,
        'primary_tag': primary_tag,
        'tags': tags,
        'n_tags': n_tags,
        'primary_category': primary_cat,
        'categories': categories,
        'author': author,
        'authors': authors,
        'n_authors': n_authors,
        'url_pdf': url_pdf,
        'url_href': url_href,
        'date': post['published']
    })

def get_arxiv(
    arx_list, 
    arx_dict, 
    filter_to_date=datetime.strftime(datetime.now() - timedelta(1), '%Y-%m-%d'),
 ):
    """Loop all the arx_list categories and combine into one"""
    df = pd.DataFrame()
    for cat in arx_list:
        posts = feedparser.parse(arxiv_query(cat))['items']
        for post in posts:
            df = df.append(parse_arxiv_post(post, arx_dict))

    # Pares date 
    df['date'] = pd.to_datetime(df['date']).dt.date.astype('str')

    # filter to today's date and remove duplicates
    df = df[df['date'] == filter_to_date]
    df = df.drop_duplicates(['title', 'date'])
    return df


def main():
    df = get_arxiv(arx_list, arx_dict, '2019-12-24')

    # Articles aren't published every day:
    if len(df) > 0:
    today = datetime.now().strftime('%Y-%m-%d')

    # Create the post folder
    dir_post = os.path.expanduser(f'~/github/ds-arxiv/_posts/{today}')
    os.makedirs(post_folder, exist_ok=True)

    # Copy in the Rmarkdown template file
    fp_template = os.path.expanduser(f'~/github/ds-arxiv/python/resources/rmd_template.Rmd')
    fp_post = os.path.join(dir_post, 'news.Rmd')
    shutil.copy(fp_template, fp_post)

    # Compile the HTML

    
    # Publish via git commit, git push
    from git import Repo
    repo = Repo(os.path.expanduser('~/github/ds-arxiv/.git'))
    repo.git.add('.')
    repo.index.commit('Daily batch run')
    repo.remote(name='origin').push()

    
    # Read in the produced tweet (after HTML compiled)

    # Tweet out

#%%

if __name__ == '__main__':
    main()
    # main(emails=False)
    # display(HTML(msg))

    # df.query('feed == "devto"').loc[0, 'link']


# DOESNT HANDLE MISSING DATA WELL
# def parse_rss(url) -> pd.DataFrame:
#     feed = feedparser.parse(url)
#     df = pd.DataFrame()
#     for i in feed['items']:
#         df = df.append(pd.DataFrame({
#             'title': [i['title']],
#             'link': [i['link']],
#             'date': [pd.to_datetime(i['published'])],
#             'summary': [BeautifulSoup(i['summary'], 'html5lib').text],
#         }))
#     return df


# %%
