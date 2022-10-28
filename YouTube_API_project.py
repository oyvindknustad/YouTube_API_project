from googleapiclient.discovery import build
import pandas as pd
from IPython.display import JSON

# Data viz packages
import seaborn as sns
import matplotlib.pyplot as plt
from nltk.corpus import stopwords
import nltk
nltk.download('stopwords')

# NLP
from wordcloud import WordCloud


api_key = '########################################'
youtube = build("youtube", "v3", developerKey=api_key)


channel_ids = ['UCSHtaUm-FjUps090S7crO4Q', #Bernadette Banner
               'UCgz4oLdeKP1Pt2BpiUn2iXQ', #V. Birchwood – Historical Fashion
               'UCNwZIGnHkzy6KpHPQtserzQ', #Karolina Żebrowska
               'UCJI86v9et-IZd1KJSfahN8g', #Rachel Maksy
               'UCXidSGLe42axucCsEigBA-Q', #Morgan Donner
               'UCGfIQhkqB_CMTW7wVGYSz_A', #Costuming Drama
               'UClE05Q8Hh939-3BY8p9MPoQ', #Sewstine
               'UCca-WkVPVe9nzs2iFct4wxg', #Nicole Rudolph
               'UCWmQGoSY-lmWlakti_Br3cQ', #Cathy Hay
              ]


def get_channel_stats(youtube, channel_ids):
    """
    Get channel statistics: title, subscriber count, view count, video count, upload playlist
    Parameters:
    
    youtube: the build object from googleapiclient.discovery
    channels_ids: list of channel IDs
    
    Returns:
    Dataframe containing the channel statistics for all channels in the list: title, subscriber count, view count, video count, upload playlist
    
    """
    all_data = []
    
    request = youtube.channels().list(
        part="snippet,contentDetails,statistics",
        id=','.join(channel_ids)
    )
    response = request.execute()
    
    for item in response['items']:
        data = {'channelName': item['snippet']['title'],
                'playlistId': item['contentDetails']['relatedPlaylists']['uploads']
               }
        all_data.append(data)
    return pd.DataFrame(all_data)
channels = get_channel_stats(youtube, channel_ids)


def get_video_ids(youtube, channels):
    
    video_ids = []
    
    for i in range(len(channels['playlistId'])):
        request = youtube.playlistItems().list(
            part="snippet,contentDetails",
            playlistId=channels['playlistId'][i],
            maxResults=50
        )
        response = request.execute()

        for item in response['items']:
            video_ids.append(item['contentDetails']['videoId'])
            
        next_page_token = response.get('nextPageToken')
        
        while next_page_token is not None:
            request = youtube.playlistItems().list(
                part="snippet,contentDetails",
                playlistId=channels['playlistId'][i],
                maxResults = 50,
                pageToken = next_page_token
            )
            response = request.execute()
                
            for item in response['items']:
                video_ids.append(item['contentDetails']['videoId'])
            
            next_page_token = response.get('nextPageToken')
            
 
    return video_ids

video_ids = get_video_ids(youtube, channels)


def get_video_details(youtube, video_ids):
    all_video_info = []
    
    n = 0
    m = 50

    while m < 50+len(video_ids):

        request = youtube.videos().list(
            part="snippet,contentDetails,statistics",
            id=video_ids[n:m]
        )
        response = request.execute()

        for video in response['items']:
            stats = {'snippet': ['channelTitle', 'title', 'description', 'tags', 'publishedAt'],
                            'statistics': ['viewCount', 'likeCount', 'favouriteCount', 'commentCount'],
                            'contentDetails': ['duration', 'definition', 'caption']
                            }
            video_info = {'video_id': video['id']}

            for key in stats.keys():
                for val in stats[key]:
                    try:
                        video_info[val] = video[key][val]
                    except:
                        video_info[val] = None        

            all_video_info.append(video_info)

        n += 50
        m += 50
            
            
    return pd.DataFrame(all_video_info)

df = get_video_details(youtube, video_ids)


#Turn numeric columns into numeric datatypes
numeric_cols = ['viewCount', 'likeCount', 'favouriteCount', 'commentCount']
df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors = 'coerce', axis=1)


#Make a column for tag count
df['tagCount'] = df['tags'].apply(lambda x: 0 if x is None else len(x))


#Reorder columns
df = df[['channelTitle', 'title', 'tags', 'tagCount', 
                        'viewCount', 'duration', 'video_id', 'description', 
                        'publishedAt', 'likeCount', 'favouriteCount',
                       'commentCount', 'definition', 'caption']]


### Wordcloud for video titles


stop_words = set(stopwords.words('english'))
df['title_no_stopwords'] = df['title'].apply(lambda x: [item for item in str(x). split() if item not in stop_words])

all_words = list([a for b in df['title_no_stopwords'].tolist() for a in b])
all_words_str = ' '.join(all_words)

def plot_cloud(wordclooud):
    plt.figure(figsize=(30, 20))
    plt.imshow(wordcloud)
    plt.axis("off");
    
wordcloud = WordCloud(width = 2000, height = 1000, random_state=1, background_color='black', colormap='viridis', collocations=False).generate(all_words_str)

plot_cloud(wordcloud)


### Wordcloud for tags


stop_words = set(stopwords.words('english'))
df['tags_no_stopwords'] = df['tags'].apply(lambda x: [item for item in str(x). split() if item not in stop_words])

all_words = list([a for b in df['tags_no_stopwords'].tolist() for a in b])
all_words_str = ' '.join(all_words)

def plot_cloud(wordclooud):
    plt.figure(figsize=(30, 20))
    plt.imshow(wordcloud)
    plt.axis("off");
    
wordcloud = WordCloud(width = 2000, height = 1000, random_state=1, background_color='black', colormap='viridis', collocations=False).generate(all_words_str)

plot_cloud(wordcloud)


###Looking at correlation between tag count and views


#Make scatter plot to show correlation between viewCount and tagCount
sns.scatterplot(data = df, x = "tagCount", y = "viewCount")


#Make time readable
import isodate
df['durationSecs'] = df['duration'].apply(lambda x: isodate.parse_duration(x))
df['durationSecs'] = df['durationSecs'].astype('timedelta64[s]')
df['durationMin'] = df['durationSecs']/60


#Reorder columns
df = df[['channelTitle', 'title', 'tags', 'tagCount', 'viewCount', 'durationMin', 'video_id', 'description', 'publishedAt', 'likeCount',
       'favouriteCount', 'commentCount', 'definition', 'caption',
       'title_no_stopwords',
       'durationSecs', 'tags_no_stopwords']]


#Make a data frame with the videos with no tags for further investigation. 
noTag_df = df.loc[df['tagCount'] == 0]
noTag_df.describe()


#Find out which videos have the min value of 0 secs. 
noTag_df.loc[df['durationSecs'] == 0]


#Get data about the no tag videos and one of the channels. 
Karolina_noTag_df = noTag_df.loc[df['channelTitle'].str.contains('Karolina Żebrowska')]
Karolina_noTag_df.describe()


