from flask import Flask,render_template, request,make_response

from pymongo import MongoClient
from apiclient.discovery import build
import pandas as pd
app = Flask(__name__)



cluster = MongoClient("--------your mongo db client connetion link----------------------")
db=cluster['youtube']
collection=db['comments']

@app.route('/predict', methods=['GET','POST'])
def predict():
    
    if request.method == 'POST':
        
        
    
        api_key ="----------your youtube api link---------------------"
        yt = build('youtube','v3',developerKey=api_key)
        
        query = request.form['input-url']
        if query=="":
            return render_template('index.html')
        
        req=yt.search().list(q=query,part='snippet',type='video',maxResults = 1).execute()
        
        videoid=req['items'][0]['id']['videoId']
        
        comments = yt.commentThreads().list(
                            part="snippet",
                            videoId = videoid,
                            maxResults = 100, # Only take top 100 comments...
                            order = 'relevance', #... ranked on relevance
                            textFormat = 'plainText',
                            ).execute()
    
        comment = []
        comment_id = []
        comment_name=[]
        comment_date=[]
        comment_likes=[]
        for i in comments['items']:
            comment_id.append(i['snippet']['topLevelComment']['id'])
            comment_name.append(i['snippet']['topLevelComment']['snippet']['authorDisplayName'])
            comment.append(i['snippet']['topLevelComment']['snippet']['textDisplay'])
            comment_date.append(i['snippet']['topLevelComment']['snippet']['updatedAt'])
            comment_likes.append(i['snippet']['topLevelComment']['snippet']['likeCount'])
        global video_name
        video_name=req['items'][0]['snippet']['title']
        channel_name=req['items'][0]['snippet']['channelTitle']
        
        yt_dict={
            'Video Name': video_name,
            'Channel Name':channel_name,
            'Comment Id':comment_id,
            'Name':comment_name,
            'Comment':comment,
            'Date':comment_date,
            'Likes':comment_likes
        }
        
        collection.update(yt_dict,yt_dict, upsert=True)
        global excel
        df=pd.DataFrame(yt_dict)
        df.sort_values("Likes",inplace=True,ascending=False,ignore_index=True)
        excel=df.copy()
        df.drop(['Comment Id','Video Name','Channel Name'],axis=1,inplace=True)
        
        return render_template('pred.html',link=query,name=video_name, data=df)
	
	

@app.route('/')
@app.route('/home')
def home():
    return render_template('index.html')

@app.route('/down')
def down ():
    resp = make_response(excel.to_csv(index=False))
    resp.headers={
        "Content-Disposition": "attachment;"
        "filename={}.csv".format(video_name)                     
        }
    return resp


if __name__ == '__main__':
    app.run(debug=True)
