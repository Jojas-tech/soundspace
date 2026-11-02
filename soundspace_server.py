#!/usr/bin/env python3
"""Sound Space local helper: YouTube search/pagination and LRCLIB lookup."""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from pathlib import Path
import json, re, os
BASE = Path(__file__).resolve().parent
SimpleHTTPRequestHandler.extensions_map.update({'.webmanifest':'application/manifest+json','.js':'text/javascript'})

def get_key():
    key=os.environ.get('SOUNDSPACE_YOUTUBE_API_KEY','').strip()
    if not key and (BASE/'youtube_key.txt').exists(): key=(BASE/'youtube_key.txt').read_text(encoding='utf-8').strip()
    if key.startswith('PASTE_YOUR_') or key=='': return ''
    return key

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*a,**kw): super().__init__(*a,directory=str(BASE),**kw)
    def reply(self,status,obj):
        body=json.dumps(obj).encode(); self.send_response(status); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Cache-Control','no-store'); self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body)
    def do_GET(self):
        p=urlparse(self.path); qs=parse_qs(p.query)
        if p.path=='/api/health': return self.reply(200,{'ok':True,'service':'Sound Space local server','build':'SS-JAMENDO-OFFLINE-DOWNLOADS-20261031-V4'})
        if p.path=='/api/jamendo/search':
            q=qs.get('q',[''])[0].strip(); client_id=qs.get('client_id',[''])[0].strip()
            if not q:return self.reply(400,{'error':'Enter a title, artist or genre.'})
            if not client_id:return self.reply(400,{'error':'Add your Jamendo Client ID in SoundSpace Settings.'})
            params={'client_id':client_id,'format':'json','limit':'30','order':'relevance','audioformat':'mp32','audiodlformat':'mp32','search':q,'type':'single albumtrack','include':'musicinfo'}
            try:
                req=Request('https://api.jamendo.com/v3.0/tracks/?'+urlencode(params),headers={'User-Agent':'SoundSpace/3.0','Accept':'application/json'})
                with urlopen(req,timeout=20) as r:data=json.loads(r.read().decode())
                if data.get('headers',{}).get('status')!='success':return self.reply(502,{'error':data.get('headers',{}).get('error_message') or 'Jamendo search failed.'})
                items=[]
                for x in data.get('results',[]):
                    items.append({'id':str(x.get('id','')),'title':x.get('name') or 'Unknown title','artist':x.get('artist_name') or 'Unknown artist','album':x.get('album_name') or '', 'duration':int(x.get('duration') or 0),'image':x.get('image') or x.get('album_image') or '', 'audio':x.get('audio') or '', 'downloadAllowed':bool(x.get('audiodownload_allowed')),'license':x.get('license_ccurl') or '', 'url':x.get('shareurl') or ''})
                return self.reply(200,{'results':items,'count':len(items)})
            except HTTPError as e:return self.reply(e.code,{'error':f'Jamendo API HTTP {e.code}'})
            except (URLError,TimeoutError,OSError,ValueError) as e:return self.reply(502,{'error':f'Cannot reach Jamendo: {e}'})
        if p.path=='/api/jamendo/download':
            track_id=qs.get('id',[''])[0].strip(); client_id=qs.get('client_id',[''])[0].strip()
            if not track_id.isdigit() or not client_id:return self.reply(400,{'error':'A valid track ID and Jamendo Client ID are required.'})
            try:
                check={'client_id':client_id,'format':'json','id':track_id,'fields':'id,name,artist_name,audiodownload_allowed'}
                req=Request('https://api.jamendo.com/v3.0/tracks/?'+urlencode(check),headers={'User-Agent':'SoundSpace/3.0','Accept':'application/json'})
                with urlopen(req,timeout=15) as r:meta=json.loads(r.read().decode())
                rows=meta.get('results',[])
                if not rows or not rows[0].get('audiodownload_allowed'):return self.reply(403,{'error':'The artist has not enabled downloads for this track.'})
                fileurl='https://api.jamendo.com/v3.0/tracks/file/?'+urlencode({'client_id':client_id,'id':track_id,'action':'download','audioformat':'mp32'})
                with urlopen(Request(fileurl,headers={'User-Agent':'SoundSpace/3.0'}),timeout=60) as audio:
                    ctype=audio.headers.get('Content-Type','audio/mpeg')
                    if not ctype.startswith('audio/') and 'octet-stream' not in ctype:return self.reply(502,{'error':'Jamendo did not return an audio file.'})
                    self.send_response(200);self.send_header('Content-Type',ctype);self.send_header('Content-Disposition',f'attachment; filename="jamendo-{track_id}.mp3"')
                    if audio.headers.get('Content-Length'):self.send_header('Content-Length',audio.headers['Content-Length'])
                    self.send_header('Cache-Control','no-store');self.end_headers()
                    while True:
                        chunk=audio.read(128*1024)
                        if not chunk:break
                        self.wfile.write(chunk)
            except HTTPError as e:return self.reply(e.code,{'error':f'Jamendo download failed (HTTP {e.code}).'})
            except (URLError,TimeoutError,OSError,ValueError) as e:
                try:return self.reply(502,{'error':f'Cannot download from Jamendo: {e}'})
                except Exception:return
            return
        if p.path=='/api/lyrics':
            track=qs.get('track',[''])[0].strip(); artist=qs.get('artist',[''])[0].strip()
            if not track:return self.reply(400,{'error':'A track title is required.'})
            def clean(s):
                s=re.sub(r'\([^)]*(official|lyrics?|audio|video|visualizer|remaster|hd|4k)[^)]*\)',' ',s,flags=re.I)
                s=re.sub(r'\[[^]]*(official|lyrics?|audio|video|visualizer|remaster|hd|4k)[^]]*\]',' ',s,flags=re.I)
                return re.sub(r'\s+',' ',s).strip(' -|')
            def norm(s):return re.sub(r'[^a-z0-9]+','',str(s or '').lower())
            def toks(s):return set(re.findall(r'[a-z0-9]+',str(s or '').lower()))
            cleaned=clean(track); queries=[]
            for t in dict.fromkeys([track,cleaned]):
                if artist: queries.append({'track_name':t,'artist_name':artist})
                queries.extend([{'track_name':t},{'q':(artist+' '+t).strip()},{'q':t}])
            found={}
            try:
                for query in queries:
                    req=Request('https://lrclib.net/api/search?'+urlencode(query),headers={'User-Agent':'SoundSpace/2.0 (lyrics lookup)','Accept':'application/json'})
                    with urlopen(req,timeout=12) as r: batch=json.loads(r.read().decode())
                    if isinstance(batch,list):
                        for x in batch:
                            if x.get('id') is not None:found[x['id']]=x
                def score(x):
                    title=x.get('trackName',''); art=x.get('artistName','')
                    a=toks(cleaned); b=toks(title); overlap=len(a&b)/max(1,len(a|b))
                    artist_score=1 if artist and (norm(artist) in norm(art) or norm(art) in norm(artist)) else 0
                    return (int(norm(title)==norm(cleaned)),artist_score,overlap,int(bool(x.get('syncedLyrics'))),int(bool(x.get('plainLyrics'))))
                matches=sorted(found.values(),key=score,reverse=True)[:12]
                good=[x for x in matches if score(x)[0] or score(x)[2]>=.34]
                return self.reply(200,{'item':good[0] if good else None,'matches':good,'count':len(good)})
            except (HTTPError,URLError,TimeoutError,OSError,ValueError) as e:return self.reply(502,{'error':f'LRCLIB lookup failed: {e}'})
        if p.path=='/api/youtube':
            q=qs.get('q',[''])[0].strip(); key=get_key()
            if not q:return self.reply(400,{'error':'Enter a search term.'})
            if not key:return self.reply(503,{'error':'Add a newly generated YouTube Data API key to youtube_key.txt, then restart Sound Space.'})
            count=max(1,min(50,int(qs.get('maxResults',['25'])[0] or 25))); page=qs.get('pageToken',[''])[0]
            params={'part':'snippet','type':'video','videoEmbeddable':'true','maxResults':str(count),'q':q,'key':key}
            if page:params['pageToken']=page
            try:
                req=Request('https://www.googleapis.com/youtube/v3/search?'+urlencode(params),headers={'User-Agent':'SoundSpaceLocal/2.0','Accept':'application/json'})
                with urlopen(req,timeout=18) as r:data=json.loads(r.read().decode())
                items=data.get('items',[]); ids=[x.get('id',{}).get('videoId') for x in items]; ids=[x for x in ids if x]
                if ids:
                    durl='https://www.googleapis.com/youtube/v3/videos?'+urlencode({'part':'contentDetails','id':','.join(ids),'key':key})
                    try:
                        with urlopen(Request(durl,headers={'User-Agent':'SoundSpaceLocal/2.0'}),timeout=12) as r: details=json.loads(r.read().decode())
                        durations={}
                        for v in details.get('items',[]):
                            m=re.fullmatch(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?',v.get('contentDetails',{}).get('duration',''))
                            if m: durations[v['id']]=int(m[1] or 0)*3600+int(m[2] or 0)*60+int(m[3] or 0)
                        for x in items:x['contentDetails']={'durationSeconds':durations.get(x.get('id',{}).get('videoId'),0)}
                    except Exception:pass
                data['items']=items; return self.reply(200,data)
            except HTTPError as e:
                try:d=json.loads(e.read().decode())
                except Exception:d={}
                return self.reply(e.code,{'error':d.get('error',{}).get('message',f'YouTube API HTTP {e.code}'),'details':d})
            except (URLError,TimeoutError,OSError,ValueError) as e:return self.reply(502,{'error':f'Cannot reach YouTube: {e}'})
        return super().do_GET()

if __name__=='__main__':
    print('Sound Space: http://localhost:8000/Soundspace.html')
    ThreadingHTTPServer(('127.0.0.1',8000),Handler).serve_forever()
