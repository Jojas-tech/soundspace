import socket, subprocess, sys, time, urllib.request, webbrowser
from pathlib import Path
BASE=Path(__file__).resolve().parent
URL='http://localhost:8000/Soundspace.html'
def healthy():
    try:
        with urllib.request.urlopen('http://localhost:8000/api/health',timeout=.45) as r:
            return r.status==200 and b'SS-JAMENDO-OFFLINE-DOWNLOADS-20261031-V4' in r.read(2048)
    except Exception:return False
if not healthy():
    with socket.socket() as s:
        if s.connect_ex(('127.0.0.1',8000))==0:
            print('Port 8000 is running an older Sound Space build. Close ALL old Sound Space server/console windows, then run this launcher again.');sys.exit(2)
    subprocess.Popen([sys.executable,str(BASE/'soundspace_server.py')],cwd=BASE,creationflags=getattr(subprocess,'CREATE_NEW_CONSOLE',0))
    for _ in range(60):
        if healthy():break
        time.sleep(.1)
    else:
        print('Sound Space server did not start. Check Python and port 8000.');sys.exit(1)
webbrowser.open(URL)
print('Sound Space opened:',URL)
