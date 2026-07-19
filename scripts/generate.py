from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta, timezone
import urllib.request, json, math, os, random

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
OUT = ROOT / "assets" / "generated"
OUT.mkdir(parents=True, exist_ok=True)

BG="#0d1117"; PANEL_2="#161f29"; BORDER="#30363d"; TEXT="#e6edf3"; MUTED="#8b949e"
GREEN="#3fb950"; GREEN_2="#2ea043"; GREEN_DARK="#0e4429"; AMBER="#d7ae68"
AMBER_DARK="#6f5528"; BONE="#e8dfc8"; BONE_SHADOW="#b9aa8a"; BLACK="#05070a"
RED="#f85149"
W,H=1200,340

def get_font(size,bold=False):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationMono-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationMono-Regular.ttf",
    ]
    for p in paths:
        if Path(p).exists():
            return ImageFont.truetype(p,size)
    return ImageFont.load_default()

def rect(draw,xy,fill=None,outline=None,width=1,radius=0):
    if radius: draw.rounded_rectangle(xy,radius=radius,fill=fill,outline=outline,width=width)
    else: draw.rectangle(xy,fill=fill,outline=outline,width=width)

def px(draw,x,y,w,h,fill): draw.rectangle((x,y,x+w-1,y+h-1),fill=fill)

def graphql(query, variables):
    token=os.getenv("GITHUB_TOKEN")
    if not token: return None
    req=urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query":query,"variables":variables}).encode(),
        headers={"Authorization":f"Bearer {token}","Content-Type":"application/json","User-Agent":"dechive-profile-engine"},
    )
    try:
        with urllib.request.urlopen(req,timeout=20) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print(f"GitHub GraphQL failed: {e}")
        return None

def fetch_data():
    username=CONFIG["github_username"]
    now=datetime.now(timezone.utc)
    start=now-timedelta(days=126)
    query="""
    query($login:String!, $from:DateTime!, $to:DateTime!) {
      user(login:$login) {
        contributionsCollection(from:$from,to:$to) {
          contributionCalendar {
            weeks {
              contributionDays { contributionCount contributionLevel date }
            }
          }
        }
        repositories(first:12, orderBy:{field:PUSHED_AT,direction:DESC}, privacy:PUBLIC) {
          nodes { name url pushedAt defaultBranchRef { target { ... on Commit { messageHeadline oid } } } }
        }
      }
    }
    """
    data=graphql(query,{"login":username,"from":start.isoformat(),"to":now.isoformat()})
    if not data or "errors" in data:
        random.seed(7)
        vals=[0 if (r:=random.random())<.45 else 1 if r<.7 else 2 if r<.86 else 3 if r<.96 else 4 for _ in range(126)]
        return vals, CONFIG["latest_record_fallback"]
    user=data["data"]["user"]
    vals=[]
    level_map={"NONE":0,"FIRST_QUARTILE":1,"SECOND_QUARTILE":2,"THIRD_QUARTILE":3,"FOURTH_QUARTILE":4}
    for week in user["contributionsCollection"]["contributionCalendar"]["weeks"]:
        for day in week["contributionDays"]:
            vals.append(level_map.get(day["contributionLevel"],0))
    vals=vals[-126:]
    while len(vals)<126: vals.insert(0,0)
    latest=CONFIG["latest_record_fallback"]
    for repo in user["repositories"]["nodes"]:
        ref=repo.get("defaultBranchRef")
        if ref and ref.get("target"):
            latest=f'{repo["name"]}: {ref["target"]["messageHeadline"]}'
            break
    return vals,latest

def draw_skull(d,x,y,s=3,pose=0,carrying=False):
    for a,b,c,e in [(7,1,7,2),(5,2,11,2),(4,3,13,4),(3,5,14,9),(4,10,13,12),(5,13,12,14)]:
        px(d,x+a*s,y+b*s,(c-a+1)*s,(e-b+1)*s,"#252b35")
    px(d,x+13*s,y+7*s,4*s,7*s,"#433727"); px(d,x+14*s,y+8*s,3*s,2*s,AMBER_DARK)
    px(d,x+6*s,y+4*s,6*s,6*s,BONE); px(d,x+5*s,y+5*s,8*s,4*s,BONE); px(d,x+7*s,y+10*s,5*s,3*s,BONE)
    px(d,x+6*s,y+6*s,2*s,2*s,BLACK); px(d,x+10*s,y+6*s,2*s,2*s,BLACK); px(d,x+8*s,y+8*s,2*s,1*s,BONE_SHADOW)
    for tx in [7,9,11]: px(d,x+tx*s,y+11*s,1*s,1*s,BLACK)
    px(d,x+7*s,y+13*s,5*s,5*s,"#d5c9ae"); px(d,x+6*s,y+14*s,7*s,2*s,"#2a3039")
    if carrying:
        px(d,x+4*s,y+14*s,4*s,2*s,BONE); px(d,x+11*s,y+14*s,4*s,2*s,BONE)
    else:
        px(d,x+(4 if pose%2==0 else 5)*s,y+(14 if pose%2==0 else 15)*s,3*s,1*s,BONE)
        px(d,x+12*s,y+(15 if pose%2==0 else 14)*s,3*s,1*s,BONE)
    if pose%2==0:
        px(d,x+7*s,y+18*s,2*s,4*s,BONE); px(d,x+11*s,y+18*s,2*s,3*s,BONE)
    else:
        px(d,x+7*s,y+18*s,2*s,3*s,BONE); px(d,x+11*s,y+18*s,2*s,4*s,BONE)
    if carrying:
        px(d,x+7*s,y+14*s,6*s,5*s,GREEN_DARK); px(d,x+8*s,y+15*s,4*s,3*s,GREEN)
        px(d,x+9*s,y+15*s,1*s,3*s,"#9be9a8"); px(d,x+8*s,y+16*s,3*s,1*s,"#9be9a8")

def draw_grid(d,x,y,data,active=None):
    colors=[PANEL_2,GREEN_DARK,"#006d32",GREEN_2,GREEN]; pos=[]; idx=0; cell=12; gap=4
    for col in range(18):
        for row in range(7):
            level=data[idx%len(data)]; fill=colors[max(0,min(4,level))]
            xx=x+col*(cell+gap); yy=y+row*(cell+gap)
            if active is not None and idx==active: fill="#9be9a8"
            rect(d,(xx,yy,xx+cell,yy+cell),fill=fill,outline="#26303a",radius=2)
            pos.append((xx+cell//2,yy+cell//2)); idx+=1
    return pos

def draw_machine(d,x,y,pulse=0,verifying=False):
    rect(d,(x,y,x+238,y+176),fill="#1a222c",outline=BORDER,width=3,radius=12)
    rect(d,(x+18,y+15,x+220,y+54),fill=BLACK,outline="#56606d",width=2,radius=5)
    d.text((x+119,y+35),"VERIFYING..." if verifying else "READY",font=get_font(20,True),fill=AMBER if verifying else GREEN,anchor="mm")
    rect(d,(x+58,y+71,x+180,y+150),fill="#07120c",outline="#3a4a43",width=3,radius=8)
    d.ellipse((x+86,y+86,x+152,y+152),outline=GREEN,width=4); d.ellipse((x+102,y+102,x+136,y+136),fill="#0f301c",outline=GREEN,width=3)
    d.line((x+112,y+120,x+121,y+130),fill="#9be9a8",width=5); d.line((x+121,y+130,x+137,y+111),fill="#9be9a8",width=5)

def draw_shelf(d,x,y,count):
    rect(d,(x,y,x+185,y+176),fill="#2a2118",outline="#6b5130",width=3,radius=5)
    for shelf in range(3):
        yy=y+18+shelf*50; d.rectangle((x+10,yy+30,x+175,yy+35),fill="#7f6037")
        for j in range(5):
            if shelf*5+j>=count: continue
            xx=x+15+j*32; rect(d,(xx,yy,xx+23,yy+27),fill=GREEN_DARK,outline=GREEN_2,width=2,radius=3)
            d.text((xx+11,yy+13),"+",font=get_font(15,True),fill="#9be9a8",anchor="mm")

def frame(i,data,latest):
    im=Image.new("RGB",(W,H),BG); d=ImageDraw.Draw(im)
    rect(d,(8,8,W-8,H-8),fill=BG,outline=BORDER,width=2,radius=13)
    d.text((32,28),"DECHIVE",font=get_font(30,True),fill=TEXT); d.text((218,35),"RECORD ENGINE",font=get_font(17,True),fill=AMBER)
    d.text((W-32,36),CONFIG["tagline"].upper(),font=get_font(14),fill=MUTED,anchor="ra"); d.line((28,68,W-28,68),fill=BORDER,width=2)
    d.text((38,86),"UNVERIFIED COMMITS",font=get_font(15,True),fill=TEXT); d.text((38,108),"PAST ACTIVITY",font=get_font(12),fill=GREEN)
    d.text((890,86),"VERIFIED RECORDS",font=get_font(15,True),fill=TEXT)
    pos=draw_grid(d,38,130,data,58 if i<18 else None)
    rect(d,(28,280,W-28,310),fill="#0b0f14",outline="#252d36",width=2,radius=4)
    for n in range(18):
        xx=42+n*63; d.ellipse((xx,289,xx+10,299),fill="#4d5662")
    verifying=30<=i<48; draw_machine(d,590,92,(math.sin(i/3)+1)/2 if verifying else .15,verifying)
    draw_shelf(d,872,104,12+(1 if i>=48 else 0))
    if i<18: sx=int(310+(365-310)*(i/17)); carry=False
    elif i<30: sx=int(365+(525-365)*((i-18)/11)); carry=True
    elif i<48: sx=525; carry=False
    else: sx=int(525+(310-525)*((i-48)/11)); carry=False
    draw_skull(d,sx,205,3,i//3,carry)
    if i<18:
        bx,by=pos[58]; g=3+int(3*((math.sin(i)+1)/2)); d.rectangle((bx-7-g,by-7-g,bx+7+g,by+7+g),outline="#9be9a8")
    elif 30<=i<36:
        xx=552+(i-30)*8; rect(d,(xx,228,xx+22,250),fill=GREEN,outline="#9be9a8",radius=3)
    status="VERIFIED" if i>=48 else ("VERIFYING" if verifying else "COLLECTING")
    d.text((38,322),f"ENGINE LOG  |  {latest[:74]}",font=get_font(12),fill=MUTED)
    d.text((W-38,322),status,font=get_font(12,True),fill=GREEN if status=="VERIFIED" else AMBER if status=="VERIFYING" else TEXT,anchor="ra")
    return im

data,latest=fetch_data()
frames=[frame(i,data,latest) for i in range(CONFIG["animation"]["frames"])]
frames[0].save(OUT/"dechive-record-engine.gif",save_all=True,append_images=frames[1:],duration=CONFIG["animation"]["frame_duration_ms"],loop=0,optimize=False,disposal=2)
frames[26].save(OUT/"dechive-record-engine-preview.png")
print("Generated:", OUT/"dechive-record-engine.gif")
