"""

TODO: Parse cs, stat, math, etc to have "domains"
* Rank the author (with how many publications they have)
* Provide links to topic-specific articles (not just subject)

"""
import os
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

def get_arxiv(arx_list, arx_dict):
    """Loop all the arx_list categories and combine into one"""
    df = pd.DataFrame()
    for cat in arx_list:
        posts = feedparser.parse(arxiv_query(cat))['items']
        for post in posts:
            df = df.append(parse_arxiv_post(post, arx_dict))

    # Pares date 
    df['date'] = pd.to_datetime(df['date']).dt.date.astype('str')

    # filter to today's date and remove duplicates
    yesterday = datetime.strftime(datetime.now() - timedelta(1), '%Y-%m-%d')
    df = df[df['date'] == yesterday]
    df = df.drop_duplicates(['title', 'date'])
    return df



# def get_arxiv(arx_list, arx_dict):
#     """Get all arxiv from list in arxivapi.py"""

#     df = pd.DataFrame()
#     for cat in arx_list:
#         df_new = parse_rss(post, arx_dict)
#         df_new['field'] = cat
#         df_new['topic'] = arx_dict[cat]
#         df = df.append(df_new)

#     # multiple postings on same category
#     df = df.drop_duplicates(['title', 'published'])
#     return df

# def combine_feeds(feeds: dict) -> pd.DataFrame:
#     """Combine multiple feeds"""
#     df = pd.DataFrame()
#     for category, feed in feeds.items():
#         for f, url in feed.items():
#             try:
#                 df_new = parse_rss(url)
#             except:
#                 print('error on', f, category, url, 'trying a replace')
#                 r = requests.get(url)
#                 t = r.text.replace('\r\n', '')
#                 df_new = parse_rss(t)
#             df_new['feed'] = f
#             df_new['category'] = category
#             df = df.append(df_new)

#     # Add the arxiv feeds (it's not a category)
#     if date.today().weekday() in [0, 4]: #0,4=monday and friday
#         df = df.append(get_arxiv(), sort=False)

#     df['summary'] = df['summary'].apply(lambda x: strip_html(x))
#     df['domain'] = df['link'].apply(lambda x: extract_domain(x))
#     df['date'] = pd.to_datetime(df['published'])
#     df['short_date'] = df['date'].dt.date

#     # sort
#     df = df.sort_values('date', ascending=False)

#     return df

# def produce_html(df):
#     cats = df.category.unique().tolist()

#     msg = ''
#     for cat in cats:
#         df_cat = (df.query(f'category == "{cat}"')
#                     .sort_values('date', ascending=False))
#         # msg += f'<h3>{cat}</h3>'
#         msg += f'\n### {cat}'

#         domains = df_cat.domain.unique().tolist()
#         # Create a TOC within each cat
#         for dom in domains:
#             df_dom = (df_cat.query(f'domain == "{dom}"')
#                        .sort_values('date', ascending=False))
#             msg += f'\n* {dom} ({df_dom.shape[0]})'


#         for dom in domains:
#             df_dom = (df_cat.query(f'domain == "{dom}"')
#                        .sort_values('date', ascending=False))
#             # msg += f'\n#####{dom} ({df_dom.shape[0]})\n\n'
#             msg += f'\n\n<details open><summary><strong>{dom} ({df_dom.shape[0]})</strong></summary>'

#             for idx, r in df_dom.iterrows():
#                 link = str(r.link)#.replace('_', '\_') #underscores get messed up in markdown conversion. You can escape them in a markdown bracket, but i'm wrapping all this in an html tag. Maybe not necessary to do all in html, and could just do details tags
#                 date = r.short_date.strftime('%m-%d')
#                 if r.feed == 'arxiv':
#                     msg += f'\t<details><summary><a href={link}>({date})</a> <strong>{r.topic}</strong> {r.title}</summary><br>{r.summary}</br><br></details>'
#                 else:
#                     msg += f'\t<details><summary><a href={link}>({date})</a> {r.title}</summary><br>{r.summary}</br><br></details>'

#             msg += f'\n</details>'

#     # msg = '<html><head></head><body>' + msg + '</body></html>'
#     # display(HTML(msg))
#     return msg

def produce_rmd(df):

    today = datetime.now().strftime('%Y-%m-%d')
    yesterday = datetime.strftime(datetime.now() - timedelta(1), '%Y-%m-%d')
    md = rmd_template.format(n = len(df), date=today, yesterday=yesterday)

    post_folder = os.path.expanduser(f'~/github/ds-arxiv/_posts/{today}')
    os.makedirs(post_folder, exist_ok=True)
    with open(os.path.expanduser(f'~/github/ds-arxiv/_posts/{today}/news.Rmd'), 'w') as file:
        file.write(md)
    
    # Save the dataframe there
    fp_df = os.path.join(post_folder, 'arxiv.csv')
    df.to_csv(path_or_buf=fp_df, index=False)


def main():
    df = get_arxiv(arx_list, arx_dict)
    produce_rmd(df)



def produce_md(html, feeds):

    today = datetime.now().strftime('%Y-%m-%d')
    cats = list(feeds.keys())
    title = ', '.join(cats)
    mdhead = mdheadtemplate.format(today=today, title=title, cats=cats)
    md = mdhead + '\n' + html

    with open(os.path.expanduser(f'~/gitlab/newsfeed/content/post/{today}-news.md'), 'w') as file:
        file.write(md)
    return md


def main(emails=True):

    today = datetime.now().strftime('%Y-%m-%d')
    y = datetime.now().strftime('%Y')
    m = datetime.now().strftime('%m')
    # if emails:
        #sendemail.send_email(subject=f'Daily news for {today}', body='starting')
        #sendemail.send_email(subject=f'Daily news for {today}', body='starting', _to='2038224355@vtext.com')

    last_week = datetime.now() - timedelta(days=7)
    df = combine_feeds(feeds)

    df = df[df['short_date'] > last_week.date()]
    html = produce_html(df)
    md = produce_md(html, feeds)

    if emails:
        email_body = f'https://relaxed-darwin-5226d1.netlify.com/{y}/{m}/{today}/'
        #sendemail.send_email(subject=f'Daily news for {today}', body=email_body)
        sendemail.send_email(subject=f'Daily news for {today}', body=email_body, _to='2038224355@vtext.com')

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
