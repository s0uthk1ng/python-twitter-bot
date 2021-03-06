# TelegramBot
import time
# heroku env variables
from os import environ

import telepot
# Import a text processing library
from textblob import TextBlob
# Twython twitter api
from twython import Twython, TwythonError

import time
import traceback
import sqlite3

'''
#no more command line or dynamic arguments, just kept it for reference.

keywords = input("twitter search keyword? ")
rt_fav_limit = input("max retweet_count or favorite_count? ")
'''

def create_table():
    c = db.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS pollachi (id string primary key)")
    try:
        db.commit()
    except:
        db.rollback()


def insert_error_string(id):
    c = db.cursor()
    try:
        vals = [id]
        query = "INSERT INTO pollachi (id) VALUES (?)"
        c.execute(query, vals)
        db.commit()
    except sqlite3.IntegrityError as i:
        pass
    except:
        error = traceback.print_exc()
        db.rollback()


def select_error_string(id):
    try:
        query = "select count(*) from pollachi where id = '{}'".format(id)
        cursor = db.execute(query)
        db.commit()
        return cursor
    except:
        error = traceback.print_exc()
        db.rollback()
        return None


# TelegramBot method
def sendtotelegram(TELEGRAM_TOKEN, TELEGRAM_TELEGRAM_CHAT_ID, tweetToTelegram):
    TelegramBot = telepot.Bot(TELEGRAM_TOKEN)
    chat_id = TELEGRAM_TELEGRAM_CHAT_ID
    # aboutme = TelegramBot.getMe()
    # print (TelegramBot.getMe())
    # messages = TelegramBot.getUpdates()
    # for message in messages:
    #    chat_id = message["message"]["from"]["id"]
    # print(chat_id)

    TelegramBot.sendMessage(chat_id, tweetToTelegram)
    print("****updated TelegramBot****")


# Analysis method
def analysis(sentence):
    # for sentence in sentences:
    # Instantiate TextBlob
    analysis = TextBlob(sentence)
    # Parts of speech
    # print("{}\n\nParts of speech:\n{}\n".format(sentence, analysis.tags))
    # Sentiment analysis
    sentiment = analysis.sentiment
    # print("Sentiment:\n{}\n\n".format(sentiment))
    return sentiment.polarity


keywords_rt_fav_limits_all = [[50, ['signalapp', 'degoogle', 'f-droid', 'pinebook', 'pine64', 'pinephone']], [50, ['algotrading']], [100, ['tutanota', 'protonmail', 'duckduckgo', 'protonvpn', 'tails OS', 'tor browser', 'manjarolinux', 'manjaro']], [150, ['linux', 'ubuntu']]]


# for database
dbfilewithpath = "./tbot.db"
db = sqlite3.connect(dbfilewithpath)

create_table()

APP_KEY = environ.get('APP_KEY')
APP_SECRET = environ.get('APP_SECRET')
OAUTH_TOKEN = environ.get('OAUTH_TOKEN')
OAUTH_TOKEN_SECRET = environ.get('OAUTH_TOKEN_SECRET')
TELEGRAM_TOKEN = environ.get('TELEGRAM_TOKEN')
TELEGRAM_TELEGRAM_CHAT_ID = environ.get('TELEGRAM_TELEGRAM_CHAT_ID')

twitter = Twython(APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET)

# results = twitter.cursor(twitter.search, q='fiveperfectmovies')
# for result in results:
#    print(result['id_str'] + " : " + result['text'])

'''
#below section of code is to read the lines from a file and to tweet.
#not in use now, just kept for reference.

with open('tweets.txt', 'r+') as tweetfile:
	buff = tweetfile.readlines()

for line in buff[:]:
	line = line.strip(r'\n')
	if len(line)<=280 and len(line)>0:
		print ("Tweeting...")
		try:
			twitter.update_status(status=line)
		except TwythonError as e:
			print (e)
		with open ('tweets.txt','w') as tweetfile:
			buff.remove(line)
			tweetfile.writelines(buff)
		time.sleep(1)
	else:
		with open ('tweets.txt', 'w') as tweetfile:
			buff.remove(line)
			tweetfile.writelines(buff)
		print ("Skipped line - Too long for a tweet!")
		continue
'''

# indefinite while loop that runs every 1 hour. To remove the dependency on scheduler.
while True:
    for keywords_rt_fav_limits_entry in keywords_rt_fav_limits_all:
        rt_fav_limit = keywords_rt_fav_limits_entry[0]
        keywords = keywords_rt_fav_limits_entry[1]
        search_results = ""
        for keyword in keywords:
            for lang_list in ['en', 'ta']:
                for result_type in ['popular', 'recent']:
                    try:
                        # count=100 max (default 15), result_type='mixed' or 'recent'
                        # count=15 max (default 15), result_type='popular'
                        # print ("search twitter......", keyword, " in ", lang_list, " with max_limit as ", rt_fav_limit)
                        search_results = twitter.search(q=keyword, count=100, lang=lang_list, result_type=result_type)
                        # print (search_results)
                    except TwythonError as e:
                        print("error on search ", e)

                    if len(search_results) > 0:
                        count = 0
                        for tweet in search_results['statuses']:
                            if "RT @" not in tweet['text'] and (tweet['favorite_count'] >= int(rt_fav_limit) or tweet['retweet_count'] >= int(rt_fav_limit)) and tweet['retweeted'] == False and tweet['is_quote_status'] == False:  # and tweet['possibly_sensitive'] == False:
                                polarity_result = analysis(tweet['text'])
                                if polarity_result >= 0.15 or lang_list == 'ta':
                                    try:
                                        cursor = select_error_string(tweet['id'])
                                        for row in cursor:
                                            if row[0] == 0:
                                                if len(tweet['text']) > 200 or "https" in tweet['text']:
                                                    twitter.retweet(id=int(tweet['id']))
                                                    print(tweet['text'])
                                                    sendtotelegram(TELEGRAM_TOKEN, TELEGRAM_TELEGRAM_CHAT_ID, tweet['text'])
                                                    time.sleep(5)
                                                else:
                                                    tempStatus = "RT @" + tweet['user']['screen_name'] + " : " + tweet['text'] + " via #5k6mbot"
                                                    # this code is commented because of difficult in identifying the polls. #TODO
                                                    # twitter.update_status(status=tempStatus.encode('utf-8'))
                                                    twitter.retweet(id=int(tweet['id']))
                                                    sendtotelegram(TELEGRAM_TOKEN, TELEGRAM_TELEGRAM_CHAT_ID, tweet['text'])
                                                    print(tempStatus.encode('utf-8'))
                                                    time.sleep(5)
                                                count = count + 1
                                                # print ('Tweet from @%s Date: %s' % (tweet['user']['screen_name'].encode('utf-8'),tweet['created_at']))
                                                # print (tweet['text'].encode('utf-8'), '\n', polarity_result)
                                    except TwythonError as e:
                                        if "You have already retweeted this Tweet" in str(e):
                                            insert_error_string(tweet['id'])
                                            print("error on action", tweet['id'], e)
                                        else:
                                            print("error on action ", e)
                        # print ("total filtered and retweeted..." + str(count))
                # added this to avoid "Twitter API returned a 429 (Too Many Requests), Rate limit exceeded"
                time.sleep(10)
        # print ("end of search")
    print("sleeping for 1hr")
    time.sleep(3600)
