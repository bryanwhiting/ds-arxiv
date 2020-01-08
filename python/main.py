"""

TODO: Parse cs, stat, math, etc to have "domains"
* Rank the author (with how many publications they have)
* Provide links to topic-specific articles (not just subject)

Prefect
* Try caching
* Figure out how to force a run even with a schedule
* Submit request for log write out
* Submit request for launchd scheduling

DONE:
* Try Slack notifications
"""

import fileinput
from git import Repo
import os 
import shutil
import feedparser
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from IPython.core.display import display, HTML
import pandas as pd
from prefect import task, Flow
from prefect.schedules import Schedule
from prefect.schedules.clocks import CronClock
from prefect.tasks.core.constants import Constant
from prefect.utilities.notifications import slack_notifier
from prefect.tasks.notifications.slack_task import SlackTask
from prefect.engine.result_handlers import LocalResultHandler

from datetime import datetime, timedelta, date

import mypass
from tweet import create_twitter_api
from arxivapi import arx_dict, arx_list
from resources.config import feeds

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

# Checkpointing
# @task
@task(checkpoint=True, result_handler=LocalResultHandler(dir="~/.prefect/ds-arxiv"))
def df_get_arxiv(
    arx_list, 
    arx_dict, 
 ):
    """Loop all the arx_list categories and combine into one"""
    df = pd.DataFrame()
    for cat in arx_list:
        posts = feedparser.parse(arxiv_query(cat))['items']
        for post in posts:
            df = df.append(parse_arxiv_post(post, arx_dict))

    # Pares date 
    df['date'] = pd.to_datetime(df['date']).dt.date.astype('str')
    return df

@task
def determine_filter_date(df):

    # Default is to filter to yesterday's publications
    # filter_to_date = datetime.strftime(datetime.now() - timedelta(1), '%Y-%m-%d')
    # for debugging:
    # date_query = '2019-12-24'

    # filter to today's date and remove duplicates
    # FIXME
    # TODO: arxiv has odd publishing dates. So using "yesterday" as the query date doesn't necessarily make sense.
    # for example, arxiv might publish 4 days of work all on the same date.
    # this causes problems with getting "the latest".
    # In order to do this the RIGHT way, I'd keep some internal record of which dates
    # have been queried. But since nobody cares about this blog yet, I'm just going to do the "max" date.
    # If anyone ever cares, then I can start indexing which dates have been published. For now, i'll just 
    # publish the latest day on record.
    # Instead of taking filter_to_date as an argument I return it
    filter_to_date = df.date.max()
    return filter_to_date

@task
def filter_df_arxiv(df, filter_to_date):
    df = df[df['date'] == filter_to_date]
    df = df.drop_duplicates(['title', 'date'])
    if len(df) > 0:
        return df
    else:
        raise ValueError('Len of df = 0. No posts from yesterday.')

@task
def git_commit_push():
    repo = Repo(os.path.expanduser('~/github/ds-arxiv/.git'))
    repo.git.add('.')
    repo.index.commit('Daily batch run')
    repo.remote(name='origin').push()

@task
def create_dir_post(date_published):
    """Creates the folder where the post will live"""
    dir_post = os.path.expanduser(f'~/github/ds-arxiv/_posts/{date_published}')
    os.makedirs(dir_post, exist_ok=True)
    return dir_post


@task
def write_df_to_csv(df, dir_post):
    # save out arxiv.csv file
    fp_arxiv = os.path.join(dir_post, 'arxiv.csv')
    df.to_csv(fp_arxiv, index=False)
    return True


@task
def copy_rmd_template(dir_post):
    """Copy in the Rmarkdown template file"""
    fp_template = os.path.expanduser(f'~/github/ds-arxiv/python/resources/rmd_template.Rmd')
    fp_post = os.path.join(dir_post, 'news.Rmd')
    shutil.copy(fp_template, fp_post)
    return fp_post


def replace_in_template(filename, text_to_search, replacement_text):
    """https://stackoverflow.com/a/20593644/2138773"""
    with fileinput.FileInput(filename, inplace=True, backup='.bak') as file:
        for line in file:
            print(line.replace(text_to_search, replacement_text), end='')

def read_file(filename):
    with open(filename,'r') as f:
        text = f.read()
    return text

@task(max_retries=3, retry_delay=timedelta(minutes=2))
def replace_rmd_template_metadata(dir_post, fp_post, date_today, date_query):
    """After R Markdown is compiled, tweet.txt is created. This pulls that tweet and 
    replaces the XXDESCRIPTIONXX in the template

    Theoretically I could restructure the RMD as a long f string, but this seems simpler. 
    """

    # Replace the XXDESCRIPTIONXX with tweet content
    fp_tweet = os.path.join(dir_post, 'tweet.txt')
    tweet = read_file(filename=fp_tweet)
    tweet = tweet.replace('#datascience', 'data science')
    tweet = tweet.replace('#machinelearning', 'machine learning')
    replace_in_template(fp_post, text_to_search='XXDESCRIPTIONXX', replacement_text=tweet)

    # Replace 2000-01-01 with today's build_date
    replace_in_template(fp_post, text_to_search='2000-01-01', replacement_text=date_today)
    
    # Replace XXYESTERDAY_DATEXX with date_query's date (which will 99% be "yesterday")
    replace_in_template(fp_post, text_to_search='XXYESTERDAY_DATEXX', replacement_text=date_query)


@task
def knit_rmd_to_html(fp_post):
    """Renders to HTML"""
    cmd = f'Rscript -e \'rmarkdown::render(\"{fp_post}\")\''
    os.system(cmd)

@task
def create_tweet(dir_post, date_published, date_query):
    url_post = f'https://bryanwhiting.github.io/ds-arxiv/posts/{date_published}/'
    fp_tweet = os.path.join(dir_post, 'tweet.txt')
    tweet = read_file(filename=fp_tweet)
    tweet = tweet.replace('XXYESTERDAY_DATEXX', date_query)
    tweet = f'{tweet}Read at {url_post}'
    return tweet

@task
def tweet_bryan(tweet):

    api = create_twitter_api()
    api.send_direct_message(mypass.MY_TWITTER_ID, text=tweet)


@task 
def tweet_world(tweet):
    api = create_twitter_api()
    api.update_status(tweet)

if __name__ == '__main__':
    # Use Constant() to avoid prefect blowing up the DAG with the 
    # dicionary values: https://docs.prefect.io/core/tutorials/task-guide.html#adding-tasks-to-flows

    # Cron clock generator: https://crontab-generator.org/
    # 0 6 * * * means run every day at 6am
    schedule = Schedule(clocks=[CronClock("0 6 * * *")])
    # alternatively: crontab -l to list all crontabs, or see generator to generate the crontab
    # there's also launchctl and using plist files.
    # there's also using the calendar.
    # View Python command with `ps`
    # Rename `ps` command: https://stackoverflow.com/a/49097964/2138773
    # https://github.com/dvarrazzo/py-setproctitle
    from setproctitle import setproctitle
    setproctitle('prefect: ds arxiv')

    # Build a handler for slack
    # https://docs.prefect.io/core/tutorials/slack-notifications.html#using-your-url-to-get-notifications
    # You need to store the secrets in ~/.prefect/config.toml
    # Visit slack: https://app.slack.com/client/T04SR64EX/CS0P8PVKM
    slack_handler = slack_notifier(webhook_secret='SLACK_WEBHOOK_URL_DSARXIV')
    slack_message = SlackTask(webhook_secret='SLACK_WEBHOOK_URL_DSARXIV')


    # using the Imperitive API: https://docs.prefect.io/core/concepts/flows.html#imperative-api
    with Flow('Build Arxiv', state_handlers=[slack_handler]) as flow:

        # Dates
        date_today = datetime.now().strftime('%Y-%m-%d')

        # Begin the flow. Will fail if len(df) = 0
        # FIXME: date_query is actually overwritten within the function to just be the max date. See function for details.
        df_full = df_get_arxiv(Constant(arx_list), Constant(arx_dict))
        filter_to_date = determine_filter_date(df_full)
        df = filter_df_arxiv(df=df_full, filter_to_date=filter_to_date)


        # Creating the Post folder, save the dataframe there, and build the rmd
        dir_post = create_dir_post(date_published=date_today)
        dir_post.set_dependencies(upstream_tasks = [df])
        written_df = write_df_to_csv(df=df, dir_post=dir_post)
        fp_post = copy_rmd_template(dir_post)
        knit = knit_rmd_to_html(fp_post=fp_post)
        knit.set_dependencies(upstream_tasks = [written_df])
        
        # once knit, re-build with tweet. Requires set_dependencies to avoid conflict
        replace = replace_rmd_template_metadata(dir_post=dir_post, fp_post=fp_post, date_today=date_today, date_query=filter_to_date)
        replace.set_dependencies(upstream_tasks=[knit])
        knit2 = knit_rmd_to_html(fp_post=fp_post)
        knit2.set_dependencies(upstream_tasks=[knit, replace])
        gcp = git_commit_push()
        gcp.set_dependencies(upstream_tasks=[knit2])

        # Send tweets and slack messages
        tweet = create_tweet(dir_post, date_published=date_today, date_query=filter_to_date)
        tweet.set_dependencies(upstream_tasks=[gcp])
        tweet_b = tweet_bryan(tweet=tweet)
        tweet_w = tweet_world(tweet=tweet)
        slack_mess = slack_message(message=tweet)


    # flow.visualize()    
    state = flow.run()
    fp_pdf = os.path.expanduser('~/github/ds-arxiv/python/state-viz.dot')
    flow.visualize(flow_state=state, filename=fp_pdf)


# Todo: 
    # TO debug: 
    # put a breakpoint() in your functions above. you don't need the below.
    # state.result[df]
    # raise state.result[df].result   
    # breakpoint()
    # print('hello')     
        # Read in the produced tweet (after HTML compiled)

        # Tweet out