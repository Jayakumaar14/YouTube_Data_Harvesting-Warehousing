from googleapiclient.discovery import build
from pprint import pprint
from pymongo import MongoClient
import pymysql
import pandas as pd
import streamlit as st


def api_connect():
    api_key = 'AIzaSyDsv-TnxWGOMvVDe72-6m4-xaRvq5gZSqU'

    api_service_name = "youtube"
    api_version = "v3"
    youtube = build(api_service_name, api_version, developerKey=api_key)
    return youtube

youtube=api_connect()


def channel_info(channel_id):
    # request = youtube.channels().list(
    #     part="snippet,contentDetails,statistics",
    #     id=channel_id)

    #channel_response = request.execute()
    api_key = 'AIzaSyDCnoMA9QD-6c_H5riUKWggU17AFnGkPkM'
    api_service_name = "youtube"
    api_version = "v3"
    youtube = build(api_service_name, api_version, developerKey=api_key)
    request = youtube.channels().list(part='snippet,contentDetails,statistics',id=channel_id)
    channel_response=request.execute()

    #print(channel_response)

    for i in channel_response['items']:
        channel_data = {
            "Channel_id":i['id'],
            "channel_name":i['snippet']['title'],
            "channel_description":i['snippet']['description'],
            "channel_playlist":i['contentDetails']['relatedPlaylists']['uploads'],
            "Channel_viewcount":i['statistics']['viewCount'],
            "channel_subscribercount":i['statistics']['subscriberCount'],
            "channel_videocount":i['statistics']['videoCount'] }
    return channel_data

    #get video
def video_ids(channel_id):
    videoid=[]
    responses = youtube.channels().list(id=channel_id,
                                        part='contentDetails').execute()
    playlist_id=responses['items'][0]['contentDetails']['relatedPlaylists']['uploads']


    next_page_token=None

    while True:
        response1 = youtube.playlistItems().list(part='snippet',
                                                playlistId=playlist_id,
                                                maxResults=50,
                                                pageToken=next_page_token).execute()


        for i in range(len(response1['items'])):
            videoid.append(response1['items'][i]['snippet']['resourceId']['videoId'])

        next_page_token = response1.get('nextPageToken')

        if next_page_token is None:
            break
    return videoid

#get videos details of the channel
def videos_info(videoids):
    video_data=[]
    for video_id in videoids:
        request = youtube.videos().list(
            part="snippet,contentDetails,statistics",
            id=video_id)

        video_response = request.execute()

        for item in video_response['items']:
            videodata = {
                "Channel_Name":item['snippet']['channelTitle'],
                "channel_id":item['snippet']['channelId'],
                "Video_id":item['id'],
                "video_title":item['snippet']['title'],
                "Tags":item['snippet'].get('tags'),
                "Thumbnails":item['snippet']['thumbnails']['default']['url'],
                "Descriptions":item['snippet'].get('description'),
                "published_date":item['snippet']['publishedAt'],
                "Duration":item['contentDetails']['duration'],
                "Views":item['statistics'].get('viewCount'),
                "Likes":item['statistics'].get('likeCount'),
                "Comments":item['statistics'].get('commentCount'),
                "Favorite_count":item['statistics']['favoriteCount'],
                "definition":item['contentDetails']['definition'],
                "Caption_Status":item['contentDetails']['caption']
            }

            video_data.append(videodata)

    return video_data

    #get comments
def comment_info(videoids):
    comment_data=[]
    try:
        for video_id in videoids:
            request = youtube.commentThreads().list(
                part='snippet',
                videoId=video_id,
                maxResults=50
            )
            comment_response = request.execute()

            for items in comment_response['items']:
                cmt_data = {
                    "comment_id":items['snippet']['topLevelComment']['id'],
                    "video_id":items['snippet']['topLevelComment']['snippet']['videoId'],
                    "Comment_text":items['snippet']['topLevelComment']['snippet']['textDisplay'],
                    "Comment_author_name":items['snippet']['topLevelComment']['snippet']['authorDisplayName'],
                    "Comment_author_publishedat":items['snippet']['topLevelComment']['snippet']['publishedAt']
                }
                comment_data.append(cmt_data)
    except:
        pass

    return comment_data

    #get playlist details from the channel
def playlist_info(channel_ids):
    api_key = 'AIzaSyDsv-TnxWGOMvVDe72-6m4-xaRvq5gZSqU'
    api_service_name = "youtube"
    api_version = "v3"
    youtube = build(api_service_name, api_version, developerKey=api_key)
    next_page_token=None
    playlist_data=[]

    while True:
        request = youtube.playlists().list(
            part='snippet,contentDetails',
            channelId=channel_ids,
            maxResults=50,
            pageToken=next_page_token
        )
        playlist_response = request.execute()

        for item in playlist_response['items']:
            playl_data={
                "Playlist_id":item['id'],
                "Title":item['snippet']['title'],
                "channel_id":item['snippet']['channelId'],
                "Channel_title":item['snippet']['channelTitle'],
                "PublishedAt":item['snippet']['publishedAt'],
                "Video_count":item['contentDetails']['itemCount']
            }
            playlist_data.append(playl_data)
        
        next_page_token=playlist_response.get('nextPageToken')
        if next_page_token is None:
            break

    return playlist_data


#inserting the data to monogodb

client =MongoClient("mongodb://localhost:27017/")
db = client["YouTube_details"]

def channel_data_details(Channel_id):
    ch_info=channel_info(Channel_id)
    ply_info=playlist_info(Channel_id)
    vid_info=video_ids(Channel_id)
    video_info=videos_info(vid_info)
    cmt_info=comment_info(vid_info)

    coll1 = db["channel_data_details"]
    coll1.insert_one({"Channel_Information":ch_info,"Playlist_Information":ply_info,"Videos_Information":video_info,"Comment_Information":cmt_info})

    return "Uploaded Data Successfully"

#ch_id = channel_data_details("UCk3JZr7eS3pg5AGEvBdEvFg")

#Mysql

myconnection = pymysql.connect(host='localhost',user='root',passwd='Thanish@234')
cur = myconnection.cursor()

try:
    cur.execute("create database youtube_data")
except:
    print("Already database created on this name")

#myconnection = pymysql.connect(host='localhost',user='root',passwd='Thanish@234',database = 'youtube_data')
#cur = myconnection.cursor()

def channels_sql_table():

    myconnection = pymysql.connect(host='localhost',user='root',passwd='Thanish@234',database = 'youtube_data')
    cur = myconnection.cursor()

    drop_query = "drop table if exists channels"
    cur.execute(drop_query)
    myconnection.commit()

    try:
        cur.execute('''create table channels(Channel_Id varchar(100) primary key,
                    Channel_Name varchar(100),
                    Channel_Description text,
                    Channel_Playlist varchar(100),
                    Channel_Viewcount bigint,
                    Channel_Subscribercount bigint,
                    Channel_videocount bigint)''')

        myconnection.commit()

    except:
        print("Table name already created")

    ch_sql_data=[]
    db = client['YouTube_details']
    coll1=db["channel_data_details"]

    for ch_data in coll1.find({},{"_id":0,"Channel_Information":1}):
        ch_sql_data.append(ch_data["Channel_Information"])

    df = pd.DataFrame(ch_sql_data)

    for index,row in df.iterrows():
        insert_query = '''insert into channels(Channel_id,
                                            channel_name,
                                            channel_description,
                                            channel_playlist,
                                            Channel_viewcount,
                                            channel_subscribercount,
                                            channel_videocount)
                                            
                                            values(%s,%s,%s,%s,%s,%s,%s)'''

        values =(row['Channel_id'],
                row['channel_name'],
                row['channel_description'],
                row['channel_playlist'],
                row['Channel_viewcount'],
                row['channel_subscribercount'],
                row['channel_videocount'])

        try:
            cur.execute(insert_query,values)
            myconnection.commit()

        except:
            print("Channels values are already inserted")

def playlists_sql_table():

    myconnection = pymysql.connect(host='localhost',user='root',passwd='Thanish@234',database = 'youtube_data')
    cur = myconnection.cursor()

    drop_query = "drop table if exists playlists"
    cur.execute(drop_query)
    myconnection.commit()

    try:
        cur.execute('''create table if not exists playlists(Playlist_Id varchar(100) primary key,
                    Title varchar(100),
                    Channel_Id varchar(100),
                    Channel_Title text,
                    PublishedAt varchar(100),
                    Video_count bigint)''')

        myconnection.commit()

    except:
        print("Table name already created")

    pl_sql_data=[]
    db = client['YouTube_details']
    coll1=db["channel_data_details"]

    for pl_data in coll1.find({},{"_id":0,"Playlist_Information":1}):
        for i in range(len(pl_data["Playlist_Information"])):
            pl_sql_data.append(pl_data["Playlist_Information"][i])

    df = pd.DataFrame(pl_sql_data)

    for index,row in df.iterrows():
        insert_query = '''insert into playlists(Playlist_id,
                                            Title,
                                            channel_id,
                                            channel_title,
                                            PublishedAt,
                                            Video_count)
                                            
                                            values(%s,%s,%s,%s,%s,%s)'''

        values =(row['Playlist_id'],
                row['Title'],
                row['channel_id'],
                row['Channel_title'],
                row['PublishedAt'],
                row['Video_count'])

        try:
            cur.execute(insert_query,values)
            myconnection.commit()

        except:
            print("Playlists values are already inserted")


def videos_sql_table():

    myconnection = pymysql.connect(host='localhost',user='root',passwd='Thanish@234',database = 'youtube_data')
    cur = myconnection.cursor()

    drop_query = "drop table if exists videos"
    cur.execute(drop_query)
    myconnection.commit()

    try:
        create_query = '''create table if not exists videos(
                        Channel_Name varchar(150),
                        Channel_Id varchar(100),
                        Video_Id varchar(50) primary key, 
                        Title varchar(150), 
                        Tags text,
                        Thumbnail varchar(225),
                        Description text, 
                        Published_Date timestamp,
                        Duration interval, 
                        Views bigint, 
                        Likes bigint,
                        Comments int,
                        Favorite_Count int, 
                        Definition varchar(10), 
                        Caption_Status varchar(50) 
                        )''' 
                        
        cur.execute(create_query)             
        myconnection.commit()
    except:
        print("Videos Table alrady created")

    vi_list = []
    db = client["Youtube_details"]
    coll1 = db["channel_data_details"]

    for vi_data in coll1.find({},{"_id":0,"video_information":1}):
        for i in range(len(vi_data["video_information"])):
            vi_list.append(vi_data["video_information"][i])
    df2 = pd.DataFrame(vi_list)
        
    
    for index, row in df2.iterrows():
        insert_query = '''
                    INSERT INTO videos (Channel_Name,
                        Channel_Id,
                        Video_Id, 
                        Title, 
                        Tags,
                        Thumbnail,
                        Description, 
                        Published_Date,
                        Duration, 
                        Views, 
                        Likes,
                        Comments,
                        Favorite_Count, 
                        Definition, 
                        Caption_Status 
                        )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)

                '''
        values = (
                    row['Channel_Name'],
                    row['Channel_Id'],
                    row['Video_Id'],
                    row['Title'],
                    row['Tags'],
                    row['Thumbnail'],
                    row['Description'],
                    row['Published_Date'],
                    row['Duration'],
                    row['Views'],
                    row['Likes'],
                    row['Comments'],
                    row['Favorite_Count'],
                    row['Definition'],
                    row['Caption_Status'])
                                
        try:    
            cur.execute(insert_query,values)
            myconnection.commit()
        except:
            print("videos values already inserted in the table")

def comments_sql_table():
    myconnection = pymysql.connect(host='localhost',user='root',passwd='Thanish@234',database = 'youtube_data')
    cur = myconnection.cursor()

    drop_query = "drop table if exists comments"
    cur.execute(drop_query)
    myconnection.commit()

    try:
        create_query = '''CREATE TABLE if not exists comments(Comment_Id varchar(100) primary key,
                       Video_Id varchar(80),
                       Comment_Text text, 
                       Comment_Author varchar(150),
                       Comment_Published timestamp)'''
        cur.execute(create_query)
        myconnection.commit()
        
    except:
        print("Commentsp Table already created")

    com_list = []
    db = client["Youtube_details"]
    coll1 = db["channel_data_details"]
    for com_data in coll1.find({},{"_id":0,"comment_information":1}):
        for i in range(len(com_data["comment_information"])):
            com_list.append(com_data["comment_information"][i])
    df3 = pd.DataFrame(com_list)


    for index, row in df3.iterrows():
            insert_query = '''
                INSERT INTO comments (Comment_Id,
                                      Video_Id ,
                                      Comment_Text,
                                      Comment_Author,
                                      Comment_Published)
                VALUES (%s, %s, %s, %s, %s)

            '''
            values = (
                row['Comment_Id'],
                row['Video_Id'],
                row['Comment_Text'],
                row['Comment_Author'],
                row['Comment_Published']
            )
            try:
                cur.execute(insert_query,values)
                myconnection.commit()
            except:
               print("This comments are already exist in comments table")

def tables():
    channels_sql_table()
    playlists_sql_table()
    videos_sql_table()
    comments_sql_table()
    return "Tables Created successfully"


def show_channels_table():
    ch_list = []
    db = client["Youtube_details"]
    coll1 = db["channel_details"] 
    for ch_data in coll1.find({},{"_id":0,"channel_information":1}):
        ch_list.append(ch_data["channel_information"])
    channels_table = st.dataframe(ch_list)
    return channels_table

def show_playlists_table():
    db = client["Youtube_details"]
    coll1 =db["channel_details"]
    pl_list = []
    for pl_data in coll1.find({},{"_id":0,"playlist_information":1}):
        for i in range(len(pl_data["playlist_information"])):
                pl_list.append(pl_data["playlist_information"][i])
    playlists_table = st.dataframe(pl_list)
    return playlists_table

def show_videos_table():
    vi_list = []
    db = client["Youtube_data"]
    coll2 = db["channel_details"]
    for vi_data in coll2.find({},{"_id":0,"video_information":1}):
        for i in range(len(vi_data["video_information"])):
            vi_list.append(vi_data["video_information"][i])
    videos_table = st.dataframe(vi_list)
    return videos_table

def show_comments_table():
    com_list = []
    db = client["Youtube_data"]
    coll3 = db["channel_details"]
    for com_data in coll3.find({},{"_id":0,"comment_information":1}):
        for i in range(len(com_data["comment_information"])):
            com_list.append(com_data["comment_information"][i])
    comments_table = st.dataframe(com_list)
    return comments_table

with st.sidebar:
    st.title(":red[YOUTUBE DATA HARVESTING AND WAREHOUSING]")
    st.header("SKILL TAKE AWAY")
    st.caption('Python scripting')
    st.caption("Data Collection")
    st.caption("MongoDB")
    st.caption("API Integration")
    st.caption(" Data Managment using MongoDB and SQL")
    
channel_id = st.text_input("Enter the Channel id")
channels = channel_id.split(',')
channels = [ch.strip() for ch in channels if ch]

if st.button("Collect and Store data"):
    for channel in channels:
        ch_ids = []
        db = client["Youtube_data"]
        coll1 = db["channel_details"]
        for ch_data in coll1.find({},{"_id":0,"channel_information":1}):
            ch_ids.append(ch_data["channel_information"]["Channel_Id"])
        if channel in ch_ids:
            st.success("Channel details of the given channel id: " + channel + " already exists")
        else:
            output = channel_details(channel)
            st.success(output)
            
if st.button("Migrate to SQL"):
    display = tables()
    st.success(display)
    
show_table = st.radio("SELECT THE TABLE FOR VIEW",(":green[channels]",":orange[playlists]",":red[videos]",":blue[comments]"))

if show_table == ":green[channels]":
    show_channels_table()
elif show_table == ":orange[playlists]":
    show_playlists_table()
elif show_table ==":red[videos]":
    show_videos_table()
elif show_table == ":blue[comments]":
    show_comments_table()

#SQL connection
myconnection = pymysql.connect(host='localhost',user='root',passwd='Thanish@234',database = 'youtube_data')
cur = myconnection.cursor()
    
question = st.selectbox(
    'Please Select Your Question',
    ('1. All the videos and the Channel Name',
     '2. Channels with most number of videos',
     '3. 10 most viewed videos',
     '4. Comments in each video',
     '5. Videos with highest likes',
     '6. likes of all videos',
     '7. views of each channel',
     '8. videos published in the year 2022',
     '9. average duration of all videos in each channel',
     '10. videos with highest number of comments'))

     
if question == '1. All the videos and the Channel Name':
    query1 = "select Title as videos, Channel_Name as ChannelName from videos;"
    cur.execute(query1)
    myconnection.commit()
    t1=cur.fetchall()
    st.write(pd.DataFrame(t1, columns=["Video Title","Channel Name"]))

elif question == '2. Channels with most number of videos':
    query2 = "select Channel_Name as ChannelName,Total_Videos as NO_Videos from channels order by Total_Videos desc;"
    cur.execute(query2)
    myconnection.commit()
    t2=cur.fetchall()
    st.write(pd.DataFrame(t2, columns=["Channel Name","No Of Videos"]))

elif question == '3. 10 most viewed videos':
    query3 = '''select Views as views , Channel_Name as ChannelName,Title as VideoTitle from videos 
                        where Views is not null order by Views desc limit 10;'''
    cur.execute(query3)
    myconnection.commit()
    t3 = cur.fetchall()
    st.write(pd.DataFrame(t3, columns = ["views","channel Name","video title"]))

elif question == '4. Comments in each video':
    query4 = "select Comments as No_comments ,Title as VideoTitle from videos where Comments is not null;"
    cur.execute(query4)
    myconnection.commit()
    t4=cur.fetchall()
    st.write(pd.DataFrame(t4, columns=["No Of Comments", "Video Title"]))

elif question == '5. Videos with highest likes':
    query5 = '''select Title as VideoTitle, Channel_Name as ChannelName, Likes as LikesCount from videos 
                    where Likes is not null order by Likes desc;'''
    cur.execute(query5)
    myconnection.commit()
    t5 = cur.fetchall()
    st.write(pd.DataFrame(t5, columns=["video Title","channel Name","like count"]))

elif question == '6. likes of all videos':
    query6 = '''select Likes as likeCount,Title as VideoTitle from videos;'''
    cur.execute(query6)
    myconnection.commit()
    t6 = cur.fetchall()
    st.write(pd.DataFrame(t6, columns=["like count","video title"]))

elif question == '7. views of each channel':
    query7 = "select Channel_Name as ChannelName, Views as Channelviews from channels;"
    cur.execute(query7)
    myconnection.commit()
    t7=cur.fetchall()
    st.write(pd.DataFrame(t7, columns=["channel name","total views"]))

elif question == '8. videos published in the year 2022':
    query8 = '''select Title as Video_Title, Published_Date as VideoRelease, Channel_Name as ChannelName from videos 
                where extract(year from Published_Date) = 2022;'''
    cur.execute(query8)
    myconnection.commit()
    t8=cur.fetchall()
    st.write(pd.DataFrame(t8,columns=["Name", "Video Publised On", "ChannelName"]))

elif question == '9. average duration of all videos in each channel':
    query9 =  "SELECT Channel_Name as ChannelName, AVG(Duration) AS average_duration FROM videos GROUP BY Channel_Name;"
    cur.execute(query9)
    myconnection.commit()
    t9=cur.fetchall()
    t9 = pd.DataFrame(t9, columns=['ChannelTitle', 'Average Duration'])
    T9=[]
    for index, row in t9.iterrows():
        channel_title = row['ChannelTitle']
        average_duration = row['Average Duration']
        average_duration_str = str(average_duration)
        T9.append({"Channel Title": channel_title ,  "Average Duration": average_duration_str})
    st.write(pd.DataFrame(T9))

elif question == '10. videos with highest number of comments':
    query10 = '''select Title as VideoTitle, Channel_Name as ChannelName, Comments as Comments from videos 
                    where Comments is not null order by Comments desc;'''
    cur.execute(query10)
    myconnection.commit()
    t10=cur.fetchall()
    st.write(pd.DataFrame(t10, columns=['Video Title', 'Channel Name', 'NO Of Comments']))
