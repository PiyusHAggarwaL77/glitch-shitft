
import asyncio
import math, random, sys, array
from dataclasses import dataclass

try:
    import pygame
except ImportError:
    print("Install Pygame with: python -m pip install pygame")
    raise

pygame.init()
try:
    pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)
    AUDIO_OK = True
except pygame.error:
    AUDIO_OK = False

W, H = 1360, 800
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("GLITCH//SHIFT FINAL // Reality Heist")
clock = pygame.time.Clock()
FPS = 60

# -------------------- Theme --------------------
BG=(5,7,15); PANEL=(11,15,28); PANEL2=(16,21,39)
GRID=(27,36,61); TEXT=(238,244,255); MUTED=(125,140,175)
CYAN=(40,225,255); PURPLE=(157,101,255); GREEN=(63,235,157)
RED=(255,72,103); GOLD=(255,207,80); ORANGE=(255,140,72)
WHITE=(255,255,255); BLUE=(90,155,255)

FONT=pygame.font.SysFont("consolas",18)
SMALL=pygame.font.SysFont("consolas",13)
MED=pygame.font.SysFont("consolas",23,bold=True)
BIG=pygame.font.SysFont("consolas",42,bold=True)
HUGE=pygame.font.SysFont("consolas",62,bold=True)

GAME=pygame.Rect(28,128,900,630)
TILE=40; COLS=21; ROWS=15; OX=GAME.x+15; OY=GAME.y+15

@dataclass
class Level:
    name:str
    subtitle:str
    objective:str
    data:list
    max_echo:int
    limit:float
    threat:str

LEVELS=[
Level("THE FIRST LOOP","LEARN TO COOPERATE WITH YOUR PAST",
      "Create an Echo that holds the cyan switch while you cross the gate.",
["#####################","#P....S.......G....E#","#.....#####.........#","#...................#","#.....#####.........#","#...................#","#...................#","#.........G.........#","#...................#","#...................#","#...................#","#...................#","#...................#","#...................#","#####################"],1,70,"LOW"),
Level("DOUBLE EXPOSURE","TWO PASTS. ONE PRESENT",
      "Use two Echoes to activate both switches and escape.",
["#####################","#P..S.......G......E#","#...................#","#....#####..........#","#....#...#..........#","#....#...#..........#","#....#...#.....S....#","#....#...#..........#","#....#####.....G....#","#...................#","#...................#","#...................#","#...................#","#...................#","#####################"],2,85,"MEDIUM"),
Level("THE PARADOX ROOM","THE PAST CAN WALK WHERE THE PRESENT CANNOT",
      "Cross the red paradox field using an Echo route.",
["#####################","#P........R.........#","#.#######.#########.#","#.......R.R.........#","#.#######.#########.#","#.......R.R.......E.#","#.#######.#########.#","#.......R.R.........#","#.#######.#########.#","#...................#","#...................#","#...................#","#...................#","#...................#","#####################"],2,100,"HIGH"),
Level("HUNTER / HUNTED","THE SECURITY AI PREDICTS YOUR FUTURE",
      "Distract the drone with an Echo, then reach the exit.",
["#####################","#P.................E#","#...................#","#....#####..........#","#...................#","#..........D........#","#...................#","#....#####..........#","#...................#","#...................#","#...................#","#...................#","#...................#","#...................#","#####################"],2,95,"CRITICAL"),
Level("THE LAST SHIFT","EVERY ECHO BECOMES PART OF THE CORE",
      "Hold both switches, survive the anomaly, and escape.",
["#####################","#P..S......R......E.#","#...................#","#....#####..........#","#....#...#....S.....#","#....#...#..........#","#....#####.....R....#","#...................#","#.........A.........#","#...................#","#...................#","#...................#","#...................#","#...................#","#####################"],
3,115,"CORE COLLAPSE")
]

# -------------------- Game state --------------------
state="menu"
level_idx=0
player=[1,1]; start=[1,1]; exit_pos=[0,0]
switches=[]; echoes=[]; current=[]; drone=None; anomaly=None
level_time=0.0; score=0; combo=0
toast=""; toast_t=0.0; particles=[]; shake=0.0; flash=0.0
menu_choice=0; help_open=False
music_enabled=True
boss_hp=100; boss_phase=0; boss_timer=0; boss_shield=False
boss_projectiles=[]; boss_orbs=[]; boss_hits=0; boss_intro=0
last_move_time=0.0

# -------------------- Sound --------------------
def tone(freq=440, duration=0.08, volume=0.12):
    if not AUDIO_OK or not music_enabled:
        return
    sr=44100
    n=max(1,int(sr*duration))
    buf=array.array("h")
    for i in range(n):
        t=i/sr
        env=min(1,i/500,n-i)/max(1,min(500,n))
        v=int(32767*volume*env*math.sin(2*math.pi*freq*t))
        buf.append(v)
    try:
        s=pygame.mixer.Sound(buffer=buf.tobytes())
        s.play()
    except Exception:
        pass

def sfx(name):
    tones={
        "move":(440,.025,.05),
        "echo":(620,.12,.12),
        "gate":(820,.16,.13),
        "hit":(120,.12,.16),
        "danger":(180,.18,.14),
        "boss":(72,.35,.18),
        "win":(740,.22,.15),
        "menu":(520,.06,.08),
        "pulse":(300,.07,.08),
    }
    if name in tones: tone(*tones[name])

# -------------------- Helpers --------------------
def txt(s,x,y,font=FONT,color=TEXT):
    screen.blit(font.render(str(s),True,color),(x,y))

def center_text(s,y,font=FONT,color=TEXT):
    im=font.render(str(s),True,color)
    screen.blit(im,(W//2-im.get_width()//2,y))

def wrap(s,n):
    words=s.split(); out=[]; line=""
    for w in words:
        if len(line)+len(w)+1>n:
            out.append(line); line=w
        else: line=(line+" "+w).strip()
    if line: out.append(line)
    return out

def tile_center(x,y):
    return OX+x*TILE+20, OY+y*TILE+20

def cell(x,y):
    if 0<=x<COLS and 0<=y<ROWS:
        return LEVELS[level_idx].data[y][x]
    return "#"

def gate_open():
    return all(s["pressed"] for s in switches) if switches else True

def solid(x,y,echo=False):
    c=cell(x,y)
    if c=="#": return True
    if c=="G": return not gate_open()
    if c=="R": return not echo
    return False

def toast_msg(s,t=2.0):
    global toast,toast_t
    toast=s; toast_t=t

def particles_at(pos,color,n=8):
    x,y=pos
    for _ in range(n):
        a=random.random()*math.tau; sp=random.uniform(30,145)
        particles.append([x,y,math.cos(a)*sp,math.sin(a)*sp,random.uniform(.25,.75),color])

def panel(rect):
    pygame.draw.rect(screen,PANEL,rect,border_radius=14)
    pygame.draw.rect(screen,(38,49,78),rect,2,border_radius=14)

# -------------------- Level logic --------------------
def parse():
    global player,start,exit_pos,switches,echoes,current,drone,anomaly,level_time,combo
    switches=[]; echoes=[]; current=[]; drone=None; anomaly=None
    level_time=0; combo=0
    for y,row in enumerate(LEVELS[level_idx].data):
        for x,c in enumerate(row):
            if c=="P": player=[x,y]; start=[x,y]
            elif c=="E": exit_pos=[x,y]
            elif c=="S": switches.append({"pos":[x,y],"pressed":False})
            elif c=="D": drone={"pos":[x,y],"timer":0}
            elif c=="A": anomaly={"pos":[x,y],"phase":0}
    toast_msg(f"SECTOR {level_idx+1}: {LEVELS[level_idx].name}",2.5)

def begin():
    global level_idx,score,state
    level_idx=0; score=0; state="game"; parse()

def reset():
    global state
    parse(); state="game"; sfx("pulse")

def move(dx,dy):
    global shake,last_move_time
    if state!="game": return
    nx,ny=player[0]+dx,player[1]+dy
    if solid(nx,ny,False):
        shake=.10; particles_at(tile_center(*player),RED,4); sfx("hit"); return
    player[:]=[nx,ny]; current.append(tuple(player)); last_move_time=level_time
    particles_at(tile_center(nx,ny),CYAN,3); sfx("move")
    update_switches()
    if anomaly and player==anomaly["pos"]: hit_anomaly()
    if player==exit_pos and gate_open(): finish()

def update_switches():
    poss=[tuple(player)]
    for e in echoes:
        if e["active"] and e["path"]:
            poss.append(e["path"][min(int(e["i"]),len(e["path"])-1)])
    for s in switches: s["pressed"]=tuple(s["pos"]) in poss

def deploy():
    global current,score,combo
    if not current:
        toast_msg("MOVE FIRST — THEN DEPLOY YOUR ECHO",1.3); return
    if len(echoes)>=LEVELS[level_idx].max_echo:
        toast_msg("ECHO CAPACITY REACHED — RESET TO REWRITE",1.5); return
    echoes.append({"path":list(current),"i":0.0,"active":True,
                   "color":PURPLE if len(echoes)%2 else ORANGE})
    score+=100; combo+=1; current=[]
    toast_msg(f"ECHO {len(echoes)} DEPLOYED — PAST SELF ONLINE",2)
    particles_at(tile_center(*player),PURPLE,18); sfx("echo"); update_switches()

def hit_anomaly():
    global score,combo,flash,shake
    score=max(0,score-40); combo=0; flash=.25; shake=.25
    particles_at(tile_center(*player),PURPLE,24); sfx("danger")
    player[:]=start
    toast_msg("PARADOX COLLISION — TIMELINE REJECTED",1.5)

def update_echo(dt):
    for e in echoes:
        if e["active"]:
            e["i"]+=dt*13
            if e["i"]>=len(e["path"])-1:
                e["i"]=len(e["path"])-1; e["active"]=False
    update_switches()

def update_drone(dt):
    if not drone: return
    drone["timer"]+=dt
    if drone["timer"] < (.85 if echoes else .55): return
    drone["timer"]=0
    targets=[tuple(player)]
    for e in echoes:
        if e["active"] and e["path"]:
            targets.append(e["path"][min(int(e["i"]),len(e["path"])-1)])
    target=min(targets,key=lambda p:abs(p[0]-drone["pos"][0])+abs(p[1]-drone["pos"][1]))
    dx=1 if target[0]>drone["pos"][0] else -1 if target[0]<drone["pos"][0] else 0
    dy=1 if target[1]>drone["pos"][1] else -1 if target[1]<drone["pos"][1] else 0
    opts=[(dx,0),(0,dy)]; random.shuffle(opts)
    for mx,my in opts:
        if mx or my:
            nx,ny=drone["pos"][0]+mx,drone["pos"][1]+my
            if not solid(nx,ny,False):
                drone["pos"]=[nx,ny]; break
    if drone["pos"]==player:
        global score,combo,flash,shake
        score=max(0,score-60); combo=0; flash=.3; shake=.35
        player[:]=start; sfx("danger")
        toast_msg("DRONE CAUGHT THE PRESENT — TIMELINE RESET",1.6)

def finish():
    global state,score
    L=LEVELS[level_idx]
    bonus=300+max(0,int((L.limit-level_time)*8))+max(0,(L.max_echo-len(echoes))*60)+combo*75
    score+=bonus; state="complete"; sfx("win")
    particles_at(tile_center(*player),GREEN,40)
    toast_msg(f"SECTOR COMPLETE +{bonus}",3)

# -------------------- Final boss --------------------
def start_boss():
    global state,boss_hp,boss_phase,boss_timer,boss_shield,boss_projectiles,boss_orbs,boss_hits,boss_intro
    state="boss"; boss_hp=100; boss_phase=0; boss_timer=0; boss_shield=False
    boss_projectiles=[]; boss_orbs=[]; boss_hits=0; boss_intro=3.0
    globals()["boss_player_x"] = W//2
    sfx("boss")

def boss_action():
    # Player fires by SPACE. Echoes can absorb a projectile.
    global boss_hp,boss_shield,boss_hits,state,score,flash
    if boss_intro>0: return
    if boss_shield:
        toast_msg("CORE SHIELD ACTIVE — WAIT FOR THE OPEN WINDOW",1.2); return
    boss_hp=max(0,boss_hp-10); boss_hits+=1; score+=80
    particles_at((W//2,300),CYAN,20); sfx("echo")
    if boss_hp<=0:
        state="victory"; score+=1000; sfx("win")

def update_boss(dt):
    global boss_phase,boss_timer,boss_shield,boss_intro,flash,score
    boss_phase+=dt; boss_timer+=dt; boss_intro=max(0,boss_intro-dt)
    # Shield cycles: open for 2.4 sec, closed for 1.8 sec.
    cycle=boss_phase%4.2
    boss_shield=cycle>2.4
    if boss_timer>.72 and boss_intro<=0:
        boss_timer=0
        angle=random.uniform(0,math.tau)
        speed=random.uniform(120,190)
        boss_projectiles.append([W//2,300,math.cos(angle)*speed,math.sin(angle)*speed,3.2])
    # move projectiles
    for p in boss_projectiles[:]:
        p[0]+=p[2]*dt; p[1]+=p[3]*dt; p[4]-=dt
        # collision with the player avatar at lower center
        if math.hypot(p[0]-globals().get("boss_player_x",W//2),p[1]-620)<28:
            p[4]=0; score=max(0,score-50); flash=.2; sfx("hit")
        if p[4]<=0 or not (-40<p[0]<W+40 and -40<p[1]<H+40):
            boss_projectiles.remove(p)

def draw_boss():
    screen.fill(BG)
    # arena grid
    for x in range(0,W,40): pygame.draw.line(screen,(10,17,32),(x,0),(x,H),1)
    for y in range(0,H,40): pygame.draw.line(screen,(10,17,32),(0,y),(W,y),1)
    center_text("THE CHRONO CORE",28,BIG,TEXT)
    center_text("FINAL PROTOCOL // DEFEAT THE SYSTEM THAT OWNS TIME",80,SMALL,CYAN)
    # boss core
    cx,cy=W//2,300
    pulse=math.sin(boss_phase*3)
    for rr,col in [(110,(45,20,85)),(82,PURPLE),(52,RED if boss_shield else CYAN)]:
        pygame.draw.circle(screen,col,(cx,cy),max(10,int(rr+pulse*5)),2)
    pygame.draw.circle(screen,WHITE,(cx,cy),20,2)
    txt("CORE",cx-28,cy-8,SMALL,TEXT)
    # shield
    if boss_shield:
        center_text("SHIELD ONLINE",420,MED,RED)
    else:
        center_text("WINDOW OPEN — FIRE!",420,MED,GREEN)
    # player
    boss_player_x = globals().get("boss_player_x", W//2)
    pygame.draw.circle(screen,CYAN,(boss_player_x,620),18,2)
    pygame.draw.circle(screen,WHITE,(boss_player_x,620),8)
    # projectiles
    for p in boss_projectiles:
        pygame.draw.circle(screen,ORANGE,(int(p[0]),int(p[1])),6)
    # HUD
    panel(pygame.Rect(270,515,820,170))
    txt("CORE INTEGRITY",300,545,SMALL,CYAN)
    pygame.draw.rect(screen,(38,42,60),(300,580,760,18),border_radius=8)
    pygame.draw.rect(screen,RED,(300,580,int(760*boss_hp/100),18),border_radius=8)
    txt(f"{boss_hp}%",1080,575,MED,TEXT)
    txt(f"SCORE {score:05d}",300,625,MED,GOLD)
    txt("A/D OR ←/→ = DODGE   •   SPACE = FIRE   •   ESC = QUIT",300,658,SMALL,MUTED)
    if boss_intro>0:
        shade=pygame.Surface((W,H),pygame.SRCALPHA); shade.fill((3,4,12,150)); screen.blit(shade,(0,0))
        center_text("THE CORE AWAKENS",290,HUGE,RED)
        center_text("IT HAS YOUR ENTIRE MOVEMENT HISTORY.",370,MED,TEXT)
        center_text("SPACE TO FIGHT WHEN THE SHIELD OPENS.",420,FONT,CYAN)

# -------------------- Drawing --------------------
def draw_world():
    off=random.randint(-3,3) if shake>0 else 0
    for y in range(ROWS):
        for x in range(COLS):
            r=pygame.Rect(OX+x*TILE+off,OY+y*TILE,TILE,TILE); c=cell(x,y)
            pygame.draw.rect(screen,(8,12,24) if (x+y)%2==0 else (10,14,28),r)
            pygame.draw.rect(screen,GRID,r,1)
            if c=="#":
                pygame.draw.rect(screen,(44,54,82),r.inflate(-4,-4),border_radius=5)
                pygame.draw.line(screen,(72,84,116),r.topleft,r.topright,2)
            elif c=="S":
                pygame.draw.circle(screen,CYAN,r.center,11,2)
                if any(s["pos"]==[x,y] and s["pressed"] for s in switches):
                    pygame.draw.circle(screen,GREEN,r.center,8)
            elif c=="G":
                pygame.draw.rect(screen,GREEN if gate_open() else RED,r.inflate(-9,-9),2,border_radius=5)
            elif c=="R":
                pygame.draw.rect(screen,(120,39,72),r.inflate(-7,-7),border_radius=4)
                pygame.draw.line(screen,(255,75,110),r.topleft,r.bottomright,2)
            elif c=="E":
                pygame.draw.rect(screen,GREEN,r.inflate(-9,-9),2,border_radius=5)
                pygame.draw.circle(screen,GREEN,r.center,7,2)
            elif c=="A":
                rr=13+int(math.sin(anomaly["phase"]*5)*3) if anomaly else 13
                pygame.draw.circle(screen,PURPLE,r.center,rr,2)
    for e in echoes:
        if e["path"]:
            p=e["path"][min(int(e["i"]),len(e["path"])-1)]
            x,y=tile_center(*p)
            pygame.draw.circle(screen,e["color"],(x,y),12,2); pygame.draw.circle(screen,e["color"],(x,y),5)
            txt("E",x-5,y-8,SMALL,BG)
    if drone:
        x,y=tile_center(*drone["pos"])
        pygame.draw.circle(screen,RED,(x,y),14,2); pygame.draw.circle(screen,RED,(x,y),5); txt("D",x-5,y-8,SMALL,BG)
    x,y=tile_center(*player)
    pygame.draw.circle(screen,CYAN,(x,y),13,2); pygame.draw.circle(screen,(180,250,255),(x,y),6)
    pygame.draw.circle(screen,WHITE,(x-4,y-3),2); pygame.draw.circle(screen,WHITE,(x+4,y-3),2)

def draw_header():
    txt("GLITCH//SHIFT",28,24,HUGE,TEXT)
    txt("REALITY HEIST  //  CHRONO CORE PROTOCOL",31,88,SMALL,CYAN)
    txt(f"SCORE {score:05d}",1060,35,MED,GREEN)
    txt(f"SECTOR {level_idx+1}/5",1060,68,SMALL,MUTED)

def bar(x,y,w,val,maxv,color):
    pygame.draw.rect(screen,(28,35,55),(x,y,w,8),border_radius=4)
    frac=0 if maxv<=0 else max(0,min(1,val/maxv))
    pygame.draw.rect(screen,color,(x,y,int(w*frac),8),border_radius=4)

def draw_sidebar():
    r=pygame.Rect(950,128,382,630); panel(r)
    L=LEVELS[level_idx]
    txt(L.name,972,150,BIG,TEXT); txt(L.subtitle,974,202,SMALL,CYAN)
    txt("MISSION",974,242,SMALL,CYAN); y=267
    for line in wrap(L.objective,38):
        txt(line,974,y,SMALL,TEXT); y+=20
    y+=18; txt("CHRONO STATUS",974,y,SMALL,CYAN); y+=27
    remain=max(0,L.limit-level_time)
    txt(f"TIME  {remain:05.1f}s",974,y,SMALL,TEXT); bar(974,y+20,300,remain,L.limit,GOLD); y+=48
    txt(f"ECHOES  {len(echoes)} / {L.max_echo}",974,y,SMALL,TEXT); bar(974,y+20,300,len(echoes),L.max_echo,PURPLE); y+=50
    txt(f"COMBO  x{combo}",974,y,SMALL,TEXT); y+=36
    txt("CONTROLS",974,y,SMALL,CYAN); y+=25
    for a,b in [("WASD / ARROWS","MOVE"),("SPACE","DEPLOY ECHO"),("R","RESET"),("P","PAUSE")]:
        txt(a,974,y,SMALL,GOLD); txt(b,1090,y,SMALL,TEXT); y+=21
    y+=16; pygame.draw.line(screen,(39,49,76),(974,y),(1307,y),1); y+=18
    txt("CORE LOG",974,y,SMALL,CYAN); y+=25
    for line in wrap(L.subtitle+" — "+L.threat,38):
        txt(line,974,y,SMALL,MUTED); y+=19
    y=690
    for c,l in [(CYAN,"YOU"),(PURPLE,"ECHO"),(GREEN,"EXIT / OPEN"),(RED,"THREAT")]:
        pygame.draw.circle(screen,c,(978,y+6),5); txt(l,990,y,SMALL,MUTED); y+=19

def draw_menu():
    screen.fill(BG)
    for x in range(0,W,40): pygame.draw.line(screen,(12,18,34),(x,0),(x,H),1)
    for y in range(0,H,40): pygame.draw.line(screen,(12,18,34),(0,y),(W,y),1)
    center_text("GLITCH//SHIFT",120,HUGE,TEXT); center_text("REALITY HEIST",192,BIG,CYAN)
    center_text("YOUR PAST IS YOUR TEAMMATE.",248,MED,MUTED)
    cx,cy=W//2,355
    for rr in range(82,15,-10): pygame.draw.circle(screen,(50,30,90),(cx,cy),rr,1)
    pygame.draw.circle(screen,PURPLE,(cx,cy),18,3); pygame.draw.circle(screen,CYAN,(cx,cy),7)
    options=["START HEIST","HOW TO PLAY","SOUND: ON","QUIT"]
    for i,o in enumerate(options):
        y=455+i*50; col=CYAN if i==menu_choice else MUTED
        center_text(("▶ " if i==menu_choice else "  ")+o,y,MED,col)
    center_text("W/S OR ↑/↓  •  ENTER TO SELECT",670,SMALL,MUTED)
    center_text("OUT LIARS  //  PIYUSH AGGARWAL  //  PROMPT & PLAY",712,SMALL,(82,95,130))

def draw_help():
    screen.fill(BG); center_text("HOW THE CHRONO CORE WORKS",55,BIG,TEXT)
    items=[
        ("1","MOVE","Your route is recorded automatically."),
        ("2","DEPLOY","Press SPACE. Your route becomes an Echo."),
        ("3","COOPERATE","Echoes replay your past route and hold switches."),
        ("4","PARADOX","Echoes can cross red tiles that the present cannot."),
        ("5","ESCAPE","Open every gate and reach the green EXIT."),
        ("6","FINAL BOSS","After Sector 5, fight the Chrono Core."),
    ]
    y=135
    for a,b,c in items:
        txt(a,180,y,BIG,CYAN); txt(b,285,y+7,MED,GOLD); txt(c,285,y+38,FONT,MUTED); y+=82
    center_text("PRESS ESC TO RETURN",690,SMALL,MUTED)

def draw_complete():
    screen.fill(BG); center_text("SECTOR CLEARED",150,BIG,GREEN)
    center_text(LEVELS[level_idx].name,205,HUGE,TEXT)
    center_text(f"SCORE  {score:05d}",305,MED,GOLD)
    center_text("ENTER / SPACE  →  NEXT SECTOR",400,FONT,CYAN)
    center_text("R  →  REPLAY THIS SECTOR",450,FONT,MUTED)
    center_text("The Core remembers everything.",590,MED,PURPLE)

def draw_pause():
    shade=pygame.Surface((W,H),pygame.SRCALPHA); shade.fill((2,3,8,190)); screen.blit(shade,(0,0))
    center_text("SIMULATION PAUSED",280,BIG,TEXT); center_text("Press P to resume",345,FONT,CYAN)

def draw_toast():
    if toast_t<=0: return
    w=min(850,max(420,len(toast)*9)); r=pygame.Rect((W-w)//2,105,w,36)
    pygame.draw.rect(screen,(15,22,42),r,border_radius=8); pygame.draw.rect(screen,CYAN,r,1,border_radius=8)
    im=SMALL.render(toast,True,TEXT); screen.blit(im,(r.centerx-im.get_width()//2,r.y+10))

def draw_victory():
    screen.fill(BG)
    for i in range(16):
        x=(i*113+int(pygame.time.get_ticks()/5))%W; y=(i*71)%H
        pygame.draw.circle(screen,PURPLE,(x,y),2)
    center_text("CHRONO CORE DEFEATED",140,BIG,GREEN)
    center_text("YOU DIDN'T ESCAPE TIME.",205,HUGE,TEXT)
    center_text("YOU TAUGHT IT TO OBEY.",280,MED,CYAN)
    center_text(f"FINAL SCORE  {score:06d}",370,BIG,GOLD)
    center_text("ENTER = PLAY AGAIN",465,FONT,CYAN)
    center_text("OUT LIARS // PIYUSH AGGARWAL",650,SMALL,MUTED)

def update_fx(dt):
    global toast_t,shake,flash
    toast_t=max(0,toast_t-dt); shake=max(0,shake-dt); flash=max(0,flash-dt)
    for p in particles[:]:
        p[0]+=p[2]*dt; p[1]+=p[3]*dt; p[4]-=dt
        if p[4]<=0: particles.remove(p)

def draw_particles():
    for p in particles:
        pygame.draw.circle(screen,p[5],(int(p[0]),int(p[1])),max(1,int(5*p[4])))

# -------------------- Main --------------------
async def main():
    global state,menu_choice,level_time,flash,music_enabled,level_idx
    running=True
    parse()
    last_ticks=pygame.time.get_ticks()
    while running:
        now_ticks=pygame.time.get_ticks()
        dt=min(0.05, max(0.0, (now_ticks-last_ticks)/1000.0))
        last_ticks=now_ticks
        for ev in pygame.event.get():
            if ev.type==pygame.QUIT: running=False
            elif ev.type==pygame.MOUSEBUTTONDOWN and ev.button==1:
                if state=="menu":
                    mx,my=ev.pos
                    if 430 <= my <= 505:
                        menu_choice=0; begin()
                    elif 505 < my <= 555:
                        menu_choice=1; state="help"
                    elif 555 < my <= 605:
                        menu_choice=2; music_enabled=not music_enabled
                    elif 605 < my <= 655:
                        menu_choice=3; running=False
                elif state=="complete":
                    if 380 <= ev.pos[1] <= 450:
                        if level_idx<4:
                            level_idx+=1; parse(); state="game"
                        else:
                            start_boss()
                elif state=="victory":
                    begin()
            elif ev.type==pygame.KEYDOWN:
                if state=="menu":
                    if ev.key in (pygame.K_UP,pygame.K_w): menu_choice=(menu_choice-1)%4; sfx("menu")
                    elif ev.key in (pygame.K_DOWN,pygame.K_s): menu_choice=(menu_choice+1)%4; sfx("menu")
                    elif ev.key in (pygame.K_RETURN,pygame.K_KP_ENTER,pygame.K_SPACE):
                        if menu_choice==0:
                            begin()
                        elif menu_choice==1:
                            state="help"
                        elif menu_choice==2:
                            music_enabled=not music_enabled
                            toast_msg("SOUND "+("ON" if music_enabled else "OFF"),1.2)
                        elif menu_choice==3:
                            running=False
                elif state=="help":
                    if ev.key in (pygame.K_ESCAPE,pygame.K_RETURN): state="menu"
                elif state=="game":
                    if ev.key==pygame.K_ESCAPE: state="menu"
                    elif ev.key==pygame.K_p: state="pause"
                    elif ev.key==pygame.K_r: reset()
                    elif ev.key==pygame.K_SPACE: deploy()
                    elif ev.key in (pygame.K_UP,pygame.K_w): move(0,-1)
                    elif ev.key in (pygame.K_DOWN,pygame.K_s): move(0,1)
                    elif ev.key in (pygame.K_LEFT,pygame.K_a): move(-1,0)
                    elif ev.key in (pygame.K_RIGHT,pygame.K_d): move(1,0)
                elif state=="pause":
                    if ev.key==pygame.K_p: state="game"
                    elif ev.key==pygame.K_r: reset()
                    elif ev.key==pygame.K_ESCAPE: state="menu"
                elif state=="complete":
                    if ev.key==pygame.K_r: reset()
                    elif ev.key in (pygame.K_RETURN,pygame.K_SPACE):
                        if level_idx<4:
                            level_idx+=1; parse(); state="game"
                        else:
                            start_boss()
                elif state=="boss":
                    if ev.key==pygame.K_ESCAPE: state="menu"
                    elif ev.key==pygame.K_SPACE: boss_action()
                    elif ev.key in (pygame.K_LEFT, pygame.K_a):
                        boss_player_x = globals().get("boss_player_x", W//2)
                        globals()["boss_player_x"] = max(220, boss_player_x-34)
                    elif ev.key in (pygame.K_RIGHT, pygame.K_d):
                        boss_player_x = globals().get("boss_player_x", W//2)
                        globals()["boss_player_x"] = min(W-220, boss_player_x+34)
                elif state=="victory":
                    if ev.key in (pygame.K_RETURN,pygame.K_SPACE): begin()
                    elif ev.key==pygame.K_ESCAPE: state="menu"

        if state=="game":
            level_time+=dt
            if level_time>=LEVELS[level_idx].limit:
                toast_msg("TIME FRACTURE — PRESS R TO REBUILD",2); state="pause"
            update_echo(dt); update_drone(dt)
            if anomaly: anomaly["phase"]+=dt
        elif state=="boss":
            update_boss(dt)

        update_fx(dt)
        screen.fill(BG)
        if state=="menu": draw_menu()
        elif state=="help": draw_help()
        elif state in ("game","pause"):
            draw_header(); draw_world(); draw_sidebar(); draw_particles(); draw_toast()
            if state=="pause": draw_pause()
        elif state=="complete":
            draw_complete(); draw_particles(); draw_toast()
        elif state=="boss": draw_boss(); draw_particles()
        elif state=="victory": draw_victory(); draw_particles()
        if flash>0:
            f=pygame.Surface((W,H),pygame.SRCALPHA); f.fill((180,30,100,int(120*flash))); screen.blit(f,(0,0))
        pygame.display.flip()
        await asyncio.sleep(0)
    pygame.quit()

if __name__=="__main__":
    asyncio.run(main())
