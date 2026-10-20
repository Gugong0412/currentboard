"""Authored application schematics. Coordinates are explanatory, never PCB layout.

Each terminal and every drawn wire is checked against the native netlist.
Repeated named labels are conventional electrical connections; crossings are not.
"""
from html import escape as E
import json, math
from guide_model import C, PINS, NETS, FW, OUT, block, short

DEST=OUT/"schematics"
DEST.mkdir(exist_ok=True)
STYLE="""
text{font:18px 'Malgun Gothic',Arial;fill:#193b49;paint-order:stroke;stroke:white;stroke-width:3px;stroke-linejoin:round}
.small{font-size:14px}.title{font-size:25px;font-weight:bold}.caption{font-size:16px}
.wire{fill:none;stroke:#167d83;stroke-width:2.6;stroke-linecap:round;stroke-linejoin:round}
.body{fill:white;stroke:#193b49;stroke-width:2}.ic{fill:#eef8f8;stroke:#193b49;stroke-width:2}
.dnp{stroke:#b57b22;stroke-dasharray:6 4}.net-label{cursor:pointer}
.selected{stroke:#d04d20!important}.faded{opacity:.16}
"""
AUDIT=[]

class Sheet:
 def __init__(self,title,h=1100,w=1600):
  self.w=w;self.h=h;self.parts={};self.ends={};self.wires=[];self.s=[]
  self.text(35,38,title,"title")
  self.text(35,68,"● 접속점 · 선 교차만으로는 미접속 · 같은 넷 이름은 연결 · 주황 점선 DNP · IC 배치는 기능 기준","small")
 def text(self,x,y,t,cls="",anchor="start"):
  self.s.append(f'<text x="{x}" y="{y}" class="{cls}" text-anchor="{anchor}">{E(str(t))}</text>')
 def raw(self,t):self.s.append(t)
 def term(self,r,p,x,y):
  key=r+"."+str(p);assert key not in self.ends,(key,"duplicate terminal")
  assert key in PINS,key
  self.ends[key]=(x,y,PINS[key])
  self.raw(f'<circle cx="{x}" cy="{y}" r="2" fill="#167d83" data-pin="{E(key)}" data-net="{E(PINS[key])}"/>')
  return self.ends[key]
 def at(self,r,p):return self.ends[r+"."+str(p)]
 def mark(self,r):
  assert r not in self.parts,r
  self.parts[r]=C[r]
  self.raw(f'<g class="component" data-ref="{r}"><title>{E(r+" · "+C[r]["function"])}</title></g>')
 def wire(self,n,*pts):
  assert n in NETS,n
  self.wires.append((n,pts))
  self.raw(f'<polyline class="wire" data-net="{E(n)}" points="{" ".join(f"{x},{y}" for x,y in pts)}"/>')
 def join(self,a,b,*via):
  a=self.ends[a] if isinstance(a,str) else a;b=self.ends[b] if isinstance(b,str) else b
  assert a[2]==b[2],(a,b,"different nets joined")
  self.wire(a[2],a[:2],*via,b[:2])
 def dot(self,x,y,n):self.raw(f'<circle cx="{x}" cy="{y}" r="4" fill="#167d83" data-net="{E(n)}"/>')
 def label(self,endpoint,direction="right",length=70):
  x,y,n=self.ends[endpoint] if isinstance(endpoint,str) else endpoint
  if short(n).startswith("unconnected-"):
   self.raw(f'<path d="M{x-5} {y-5}l10 10m-10 0l10 -10" stroke="#789" stroke-width="2"/>')
   self.text(x+10,y+5,"NC","small");return
  if short(n) in ["GND","GND_F","USB_GND","PWR_RTN"]:
   self.wire(n,(x,y),(x,y+18))
   for dy,w in [(18,16),(25,11),(32,5)]:self.wire(n,(x-w,y+dy),(x+w,y+dy))
   self.text(x+24 if direction=="right" else x-24,y+10,short(n),"small","start" if direction=="right" else "end");return
  dx=length if direction=="right" else -length
  self.wire(n,(x,y),(x+dx,y))
  self.raw(f'<g class="net-label" data-net="{E(n)}">')
  anchor="start" if direction=="right" else "end";tx=x+dx;estimate=len(short(n))*8;ty=y-10
  if anchor=="end" and tx-estimate<20:anchor="start";ty=y+32
  if anchor=="start" and tx+estimate>self.w-20:anchor="end"
  self.text(tx,ty,short(n),"small",anchor);self.raw("</g>")
 def part(self,r,x,y,vertical=False):
  c=C[r];self.mark(r);pins=c["pins"];dnp=c["Population"]=="DNP";cl="body dnp" if dnp else "body"
  if r.startswith("Y"):pins=[next(p for p in pins if p["number"]==n) for n in ["1","3","2","4"]]
  assert len(pins) in [1,2,4],r
  if len(pins)==1:
   self.term(r,pins[0]["number"],x,y);self.raw(f'<circle cx="{x}" cy="{y-16}" r="8" class="body"/>')
   self.wire(PINS[r+"."+pins[0]["number"]],(x,y),(x,y-8));self.text(x+15,y-40,r,"small");return
  self.raw(f'<g transform="translate({x} {y})'+(' rotate(90)' if vertical else '')+'">')
  if r.startswith("C"):
   self.raw(f'<path d="M-7 -20V20 M7 -20V20 M-24 0H-7 M7 0H24" class="wire {"dnp" if dnp else ""}"/>')
  elif r.startswith("L"):
   self.raw('<path d="M-24 0c0 -22 12 -22 12 0c0 -22 12 -22 12 0c0 -22 12 -22 12 0c0 -22 12 -22 12 0" class="wire"/>')
  elif r.startswith("D"):
   # Contract pin1=K, pin2=A: cathode is the left side.
   self.raw('<path d="M-12 -17V17 M-12 0L15 -17V17Z M-24 0H-12 M15 0H24" class="body"/>')
   self.raw('<path d="M4 -24l13 -13m-7 0h7v7 M17 -17l13 -13m-7 0h7v7" class="wire"/>')
  elif r.startswith("SW"):
   self.raw('<path d="M-24 0L20 -20 M24 0H30" class="wire"/>')
  elif r.startswith("Y"):
   self.raw('<rect x="-12" y="-20" width="24" height="40" class="body"/><path d="M-20 -22V22 M20 -22V22" class="wire"/>')
  elif r.startswith("NT"):
   self.raw('<path d="M-24 0H24" class="wire"/>')
  elif r.startswith("U"):
   self.raw('<path d="M-20 -17V17 M-20 0L0 -16V16Z M20 -17V17 M20 0L0 -16V16Z" class="body"/>')
  else:self.raw(f'<rect x="-24" y="-10" width="48" height="20" class="{cl}"/>')
  self.raw("</g>")
  label=c["Value"]+(" · DNP" if dnp else "")
  self.text(x+30 if vertical else x,y-12 if vertical else y-35,r,"", "start" if vertical else "middle")
  self.text(x+30 if vertical else x,y+12 if vertical else y-52 if r.startswith("U") else y-15,label,"small","start" if vertical else "middle")
  for i,p in enumerate(pins[:2]):
   sign=-1 if i==0 else 1;xx=x if vertical else x+60*sign;yy=y+60*sign if vertical else y
   self.term(r,p["number"],xx,yy);self.text(xx-12,yy+20 if r.startswith("U") else yy-7,p["number"],"small")
   near=(x,y+24*sign) if vertical else (x+24*sign,y)
   self.wire(PINS[r+"."+p["number"]],(xx,yy),near)
  if len(pins)==4:
   for i,p in enumerate(pins[2:]):
    # Kelvin/case terminal is independently shown; no implicit copper short.
    xx=x-42 if i==0 else x+42;yy=y+65
    self.term(r,p["number"],xx,yy);self.text(xx+7,yy,p["number"],"small")
    if r.startswith("R"):self.raw(f'<path d="M{xx} {yy}V{y}" stroke="#b27c42" fill="none" stroke-width="2.6"/>')
   if r.startswith("R"):self.text(x,y+94,"1↔3 / 2↔4: 단자 동박","small","middle")
 def ic(self,r,x,y,left,right,w=320,step=55):
  """Groups may combine only same-name, same-net physical pins."""
  self.mark(r);h=100+max(len(left),len(right))*step
  self.raw(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" class="ic"/>')
  self.text(x+w/2,y+28,r,"title","middle");self.text(x+w/2,y+55,C[r]["Value"],"small","middle")
  for side,groups in [("left",left),("right",right)]:
   for i,group in enumerate(groups):
    nums=[str(t) for t in (group if isinstance(group,(list,tuple)) else [group])]
    ps=[next(p for p in C[r]["pins"] if p["number"]==num) for num in nums]
    assert len({PINS[r+"."+p["number"]] for p in ps})==1,(r,nums)
    yy=y+95+i*step;xx=x-30 if side=="left" else x+w+30;edge=x if side=="left" else x+w
    for num in nums:self.term(r,num,xx,yy)
    self.wire(PINS[r+"."+nums[0]],(xx,yy),(edge,yy))
    names="/".join(dict.fromkeys(p["name"] for p in ps))
    if "EP_GND" in names and len(ps)>1:names="GND / EP"
    self.text(x+10 if side=="left" else x+w-10,yy-8,",".join(nums)+" "+names,"small","start" if side=="left" else "end")
  return h
 def loose(self,refs,x=80,y=900,cols=4):
  """Secondary discrete components use real symbols and labelled electrical stubs."""
  for i,r in enumerate(refs):
   xx=x+(i%cols)*360;yy=y+(i//cols)*180
   c=C[r]
   if not c["pins"]:
    self.mark(r);self.raw(f'<circle cx="{xx+60}" cy="{yy}" r="18" class="body"/>') if r.startswith("H") else None
    self.text(xx,yy+40,r+" "+("M3 NPTH" if r.startswith("H") else "실크 지시"),"small")
   elif len(c["pins"])<=2 or r.startswith(("R","Y")):
    self.part(r,xx+90,yy)
    for p in c["pins"]:self.label(r+"."+p["number"],"left" if p==c["pins"][0] else "right",25)
   else:
    ps=[p["number"] for p in c["pins"]];self.ic(r,xx,yy,[],ps,w=230,step=42)
    for p in c["pins"]:self.label(r+"."+p["number"],length=35)
 def save(self,name,expected):
  assert set(self.parts)==set(expected),(name,"missing parts",set(expected)-set(self.parts),"extra",set(self.parts)-set(expected))
  need={r+"."+p["number"] for r in expected for p in C[r]["pins"]}
  assert set(self.ends)==need,(name,need-set(self.ends))
  for x,y,n in self.ends.values():assert 0<=x<=self.w and 0<=y<=self.h,(name,x,y)
  # Visible wire bridges prevent crossings of different nets looking like joins.
  segments=[(n,a,b) for n,pts in self.wires for a,b in zip(pts,pts[1:])]
  for n,a,b in segments:assert a[0]==b[0] or a[1]==b[1],(name,"non-orthogonal wire",a,b)
  for i,(n,a,b) in enumerate(segments):
   for m,c,d in segments[i+1:]:
    if n==m:continue
    for pt in (a,b):
     if c[0]==d[0]==pt[0]:
      assert not min(c[1],d[1])<pt[1]<max(c[1],d[1]),(name,"ambiguous different-net T",n,m,pt)
     if c[1]==d[1]==pt[1]:
      assert not min(c[0],d[0])<pt[0]<max(c[0],d[0]),(name,"ambiguous different-net T",n,m,pt)
    if a[1]==b[1]==c[1]==d[1]:
     assert min(max(a[0],b[0]),max(c[0],d[0]))-max(min(a[0],b[0]),min(c[0],d[0]))<=2,(name,"overlapping distinct nets",n,m)
    if a[0]==b[0]==c[0]==d[0]:
     assert min(max(a[1],b[1]),max(c[1],d[1]))-max(min(a[1],b[1]),min(c[1],d[1]))<=2,(name,"overlapping distinct nets",n,m)
  bridges=set()
  for n,a,b in segments:
   if a[1]!=b[1] or a[0]==b[0]:continue
   for m,c,d in segments:
    if n==m or c[0]!=d[0] or c[1]==d[1]:continue
    xx=c[0];yy=a[1]
    if min(a[0],b[0])<xx<max(a[0],b[0]) and min(c[1],d[1])<yy<max(c[1],d[1]):
     bridges.add((xx,yy,n))
  for x,y,n in bridges:
   self.raw(f'<path d="M{x-6} {y}h12" stroke="white" stroke-width="9"/><path d="M{x-6} {y}h12" class="wire" data-net="{E(n)}"/>')
  # Mark true same-net T branches, not mere crossings.
  candidates={(n,*pt) for n,a,b in segments for pt in (a,b)}
  for n,x,y in candidates:
   dirs=set()
   for m,a,b in segments:
    if m!=n:continue
    if a[1]==b[1]==y and min(a[0],b[0])<=x<=max(a[0],b[0]):
     if min(a[0],b[0])<x:dirs.add("L")
     if max(a[0],b[0])>x:dirs.add("R")
    if a[0]==b[0]==x and min(a[1],b[1])<=y<=max(a[1],b[1]):
     if min(a[1],b[1])<y:dirs.add("U")
     if max(a[1],b[1])>y:dirs.add("D")
   if len(dirs)>=3:self.dot(x,y,n)
  doc=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" role="img" aria-label="{E(name)}"><style>{STYLE}</style><rect width="100%" height="100%" fill="white"/>'+''.join(self.s)+'</svg>'
  (DEST/(name+".svg")).write_text(doc,encoding="utf-8")
  AUDIT.append({"name":name,"components":list(self.parts),"terminals":{k:v[2] for k,v in self.ends.items()},"checked_wires":len(self.wires),"canvas":[self.w,self.h]})
  return doc

def caps(s,refs,rail_y,x0,spacing=170):
 for i,r in enumerate(refs):
  x=x0+i*spacing;s.part(r,x,rail_y+100,True)
  a=s.at(r,1);s.wire(a[2],(x,rail_y),a[:2]);s.dot(x,rail_y,a[2])
  if i==0:s.label((x,rail_y,a[2]),"right",0)
  s.label(r+".2")
 if len(refs)>1:
  n=s.at(refs[0],1)[2]
  assert all(s.at(r,1)[2]==n for r in refs)
  s.wire(n,(x0,rail_y),(x0+(len(refs)-1)*spacing,rail_y))

def buck(n):
 refs=[r for r,c in C.items() if c["block"]==f"B{n//100}" and not r.startswith("#")]
 s=Sheet(f"B{n//100} · 벅 전원 통합 회로",1160)
 u=f"U{n}";s.ic(u,620,270,[(10,11,12),13,9,(6,15,16,17),7,8],[(1,2,3),14,5,4])
 caps(s,[f"C{n}",f"C{n+1}",f"C{n+2}"],130,90)
 a=s.at(f"C{n}",1);s.join(a,s.at(u,10),(90,130),(550,130),(550,365))
 s.part(f"L{n}",1110,365);s.join(u+".1",f"L{n}.1")
 out=s.at(f"L{n}",2);s.wire(out[2],out[:2],(1490,365));s.label((1490,365,out[2]),length=20)
 caps(s,[f"C{n+3}",f"C{n+4}"],365,1270,190)
 s.join(u+".14",(1240,365,out[2]),(1210,420),(1240,420));s.dot(1240,365,out[2])
 # FB ladder with two real top resistors.
 for i,r in enumerate([f"R{n}",f"R{n+1}",f"R{n+2}"]):s.part(r,1210,730+i*150,True)
 s.label(f"R{n}.1","right")
 s.join(f"R{n}.2",f"R{n+1}.1");s.join(f"R{n+1}.2",f"R{n+2}.1")
 fb=s.at(f"R{n+1}",2);s.join(u+".5",fb,(1080,475),(1080,955),(1210,955));s.dot(1210,955,fb[2])
 s.label(f"R{n+2}.2")
 s.part(f"C{n+5}",440,570,True);s.join(f"C{n+5}.1",u+".9",(440,475));s.label(f"C{n+5}.2")
 s.part(f"R{n+3}",990,160,True);s.label(f"R{n+3}.1","left")
 s.join(f"R{n+3}.2",u+".4",(1030,220),(1030,530));s.text(1000,560,short(s.at(u,4)[2]),"small")
 for num in [6,7,8]:s.label(u+"."+str(num),"left")
 if n==200:s.label(u+".13","left")
 else:
  s.part("R304",200,570,True);s.join("R304.1",u+".13",(200,420));s.label((200,420,s.at(u,13)[2]),"left",40);s.label("R304.2")
  s.part("R305",1450,800,True);s.label("R305.1","left");s.label("R305.2")
 s.text(50,1090,"읽는 순서: 입력 바이패스 → SW·L → 출력 C → VOS / FB 귀환 → PG·SS·EN","caption")
 return s,refs

def ldo(n):
 c=C[f"U{n}"];refs=[r for r,v in C.items() if v["block"]==c["block"] and not r.startswith("#")]
 s=Sheet(c["block"]+" · LDO / 피드백 선택 통합 회로",1380)
 u=f"U{n}";s.ic(u,590,270,[(9,10),7,8,(4,11),6],[(1,2),3,5],step=65)
 inputs=[r for r in [f"C{n}",f"C{n+1}",f"C{n+2}"] if r in C]
 caps(s,inputs,120,80)
 s.join(inputs[0]+".1",u+".9",(80,120),(525,120),(525,365))
 caps(s,[f"C{n+3}",f"C{n+4}"],365,1100,210)
 s.join(u+".1",(1100,365,s.at(u,1)[2]));s.label((1510,365,s.at(u,1)[2]),"left",0)
 s.wire(s.at(u,1)[2],(1100,365),(1510,365))
 s.part(f"C{n+5}",390,620,True);s.join(f"C{n+5}.1",u+".8",(390,495));s.label(f"C{n+5}.2")
 if f"R{n+3}" in refs:
  s.part(f"R{n+3}",200,620,True);s.join(f"R{n+3}.1",u+".7",(200,430));s.label((200,430,s.at(u,7)[2]),"left",40);s.label(f"R{n+3}.2")
 else:s.label(u+".7","left")
 for p in [4,6]:s.label(u+"."+str(p),"left")
 s.part(f"R{n+4}",980,170,True);s.label(f"R{n+4}.1","left")
 s.join(f"R{n+4}.2",u+".5",(1030,230),(1030,495));s.text(950,530,short(s.at(u,5)[2]),"small")
 # Feedback controls, arranged as one explicit ladder.
 top=[f"R{n}"]+([f"R{n+1}"] if f"R{n+1}" in refs else [])
 s.text(70,820,"전압 설정 / 피드백 경로","title")
 for i,r in enumerate(top):s.part(r,470+i*240,930)
 if len(top)>1:s.join(top[0]+".2",top[1]+".1")
 s.part(f"R{n+2}",1000,1060,True)
 s.join(top[-1]+".2",f"R{n+2}.1",(1000,930));s.dot(1000,930,s.at(f"R{n+2}",1)[2])
 s.join(u+".3",(1000,930,s.at(u,3)[2]),(1060,430),(1060,930))
 s.label(f"R{n+2}.2")
 s.part(f"C{n+6}",700,800);s.join(f"C{n+6}.2",(1000,930,s.at(u,3)[2]),(1000,800))
 if f"R{n+7}" in refs:
  s.part(f"R{n+7}",1320,650)
  s.join(u+".1",f"R{n+7}.1",(1180,365),(1180,650))
  for p in C[f"R{n+7}"]["pins"]:s.label(f"R{n+7}."+p["number"],"left" if p["number"] in ["1","3"] else "right",20)
  s.text(1140,790,"Kelvin 번호: 1/3=SRC, 2/4=DUT","small")
  s.part(f"R{n+5}",210,930);s.part(f"R{n+6}",210,1140)
  s.label(f"R{n+5}.1","left",100);s.label(f"R{n+6}.1","left",100)
  sel=s.at(f"R{n+5}",2);s.join(f"R{n+5}.2",f"R{n+6}.2",(330,930),(330,1140))
  s.join(sel,top[0]+".1");s.join(f"C{n+6}.1",sel,(360,800),(360,930))
  s.text(70,1270,"후단/전단 선택 점퍼는 한쪽만 실장 · DNP도 실제 연결 위치를 표시","caption")
 else:
  s.label(top[0]+".1","left",60);s.label(f"C{n+6}.1","left",60)
 s.text(70,1330,"출력 C는 SRC에 연결 · 분압 기준은 실제 선택 점퍼 및 넷 이름으로 확인","small")
 return s,refs

def ina(n):
 u=f"U{n}";ch=next(x for x in FW["channels"] if x["ref"]==u)
 refs=[r for r,c in C.items() if c["block"]==C[u]["block"] and not r.startswith("#")]
 # B8 power/isolator share a sheet, so select the measurement components explicitly.
 if n==820:refs=["R807","U820","R820","R821","R822","C820","C821","C822"]
 sh=ch["shunt_ref"]
 if sh not in refs:refs.append(sh)
 s=Sheet(f'{ch["rail"]} · INA228 + Kelvin 션트 통합 회로',1040)
 s.part(sh,540,190)
 for p in ["1","2"]:s.label(sh+"."+p,"left" if p=="1" else "right",65)
 s.text(50,115,"부하 전류 경로 / 실제 저항과 검출선","caption")
 s.ic(u,900,340,[10,9,8,6,7],[3,4,5,1,2],w=320,step=65)
 s.part(f"R{n}",600,435);s.part(f"R{n+1}",600,500)
 s.join(f"R{n}.2",u+".10");s.join(f"R{n+1}.2",u+".9")
 for i,r in enumerate([f"R{n}",f"R{n+1}"]):
  sp=next(p for p in ["3","4"] if s.at(sh,p)[2]==s.at(r,1)[2]);a=s.at(sh,sp);z=s.at(r,1);xx=350+i*70
  if sp=="4":s.join(a,z,(800,a[1]),(800,320),(xx,320),(xx,z[1]))
  else:s.join(a,z,(xx,a[1]),(xx,z[1]))
  s.text(xx,z[1]-12,short(z[2]),"small","end")
 s.part(f"C{n+1}",685,660,True)
 s.join(f"C{n+1}.1",u+".10",(685,435));s.dot(685,435,s.at(u,10)[2])
 s.join(f"C{n+1}.2",u+".9",(790,720),(790,500));s.dot(790,500,s.at(u,9)[2])
 s.label(u+".8","left",50);s.label(u+".7","left")
 caps(s,[f"C{n}",f"C{n+2}"],790,600,210);s.label(u+".6","left",50)
 s.join(f"C{n}.1",u+".6",(600,790),(840,790),(840,630))
 s.part(f"R{n+2}",1360,300,True);s.label(f"R{n+2}.1","left",20)
 s.join(f"R{n+2}.2",u+".3",(1360,435));s.dot(1360,435,s.at(u,3)[2]);s.label((1360,435,s.at(u,3)[2]),length=30)
 for p in [4,5,1,2]:s.label(u+"."+str(p),length=35)
 if n==700:
  for i,r in enumerate(["R708","R709"]):
   s.part(r,150+i*210,800,True);s.label(r+".1","left",20);s.label(r+".2","right",20)
 s.text(50,995,f'I2C{ch["bus"]} / 0x{ch["address_7bit"]:02X} · Rshunt={ch["R_ohm"]:g}Ω · full scale ±{ch["full_scale_current_A"]*1000:.5g}mA · C필터 DNP',"caption")
 return s,refs

def floating_power():
 refs="U800 C800 C801 R800 NT800 U810 R810 C810 C811 C812 C813".split()
 s=Sheet("B8 · 절연 전원 생성 / VGL 기준 고정",1120)
 s.ic("U800",520,230,[2,1],[4,3],w=300,step=100)
 caps(s,["C800","C801"],160,100,180)
 s.join("C800.1","U800.2",(100,160),(460,160),(460,325))
 s.part("R800",950,430,True);s.join("U800.4","R800.1",(950,325));s.label("R800.2")
 s.text(850,300,"RAW_5V_F","small")
 s.label("U800.1")
 s.part("NT800",740,640);s.label("NT800.1","left",60);s.label("NT800.2","right",60);s.label("U800.3")
 s.raw('<path d="M670 310V480" stroke="#b27c42" stroke-width="3" stroke-dasharray="7 7"/>')
 s.text(520,545,"입력 GND ≠ 출력 GND_F","caption")
 s.ic("U810",1120,680,[8,5],[1,3,4,9,2,6,7],w=300,step=40)
 caps(s,["C810","C811"],780,90,200)
 caps(s,["C812","C813"],780,560,200)
 s.part("R810",960,940,True);s.label("R810.1","left",20);s.label("R810.2","left",20)
 for p in C["U810"]["pins"]:s.label("U810."+p["number"],"left" if p["number"] in ["8","5"] else "right",25)
 s.join("U800.4","U810.8",(1040,325),(1040,775))
 s.join("U810.8","U810.5",(1040,775),(1040,815))
 s.join("C810.1","U810.8",(90,780),(90,720),(1040,720),(1040,775))
 s.join("C812.1","U810.1",(560,780),(560,660),(1500,660),(1500,775))
 s.text(45,1090,"NT800만 VGL_SRC ↔ GND_F를 결합 · F_3V3는 GND_F 기준 +3.3V","caption")
 return s,refs

def isolator():
 refs="U830 R830 R831 R832 R833 C830 C831 C832 C833".split()
 s=Sheet("B8 · I2C 절연 / 양쪽 풀업과 바이패스",1080)
 s.ic("U830",610,400,[3,5,6,(1,7),2,4,8],[14,12,11,(9,16),10,13,15],w=340,step=65)
 s.raw('<path d="M780 480V960" stroke="#b27c42" stroke-width="3" stroke-dasharray="7 7"/>')
 caps(s,["C830","C831"],120,110,200);caps(s,["C832","C833"],120,1130,200)
 for r,x,p in [("R830",200,5),("R831",450,6),("R832",1120,12),("R833",1390,11)]:
  s.part(r,x,440,True);s.label(r+".1","left",20)
  yy=s.at("U830",p)[1];s.join(r+".2","U830."+str(p),(x,yy));s.dot(x,yy,s.at("U830",p)[2])
  s.label((x,yy,s.at("U830",p)[2]),"left" if x<600 else "right",25)
 for p in [3,1,2,4,8,14,9,10,13,15]:s.label("U830."+str(p),"left" if p in [3,1,2,4,8] else "right",30)
 s.text(65,1030,"SDA 양방향 · SCL 시스템측 → 부유측 · 풀업은 각 도메인의 3.3V로","caption")
 return s,refs

def level():
 refs=[r for r,c in C.items() if block(c)==13]
 s=Sheet("B13 · 두 제어선의 3.3V → 1.8V 변환",1060)
 s.ic("U1300",620,350,[1,2,3,5,4],[8,7,6],w=320,step=110)
 caps(s,["C1300"],100,230);caps(s,["C1301"],100,1280)
 for r,x,p in [("R1300",190,2),("R1301",440,3)]:
  yy=s.at("U1300",p)[1];s.part(r,x,yy+100,True)
  s.join(r+".1","U1300."+str(p),(x,yy));s.dot(x,yy,s.at("U1300",p)[2]);s.label((x,yy,s.at("U1300",p)[2]),"left",30);s.label(r+".2")
 for r,p,rr,x in [("R1302",7,"R1304",1200),("R1303",6,"R1305",1430)]:
  yy=s.at("U1300",p)[1];s.part(r,1080,yy);s.join("U1300."+str(p),r+".1")
  s.part(rr,x,yy+150,True);s.join(r+".2",rr+".1",(x,yy));s.dot(x,yy,s.at(rr,1)[2]);s.label((x,yy,s.at(rr,1)[2]),length=30);s.label(rr+".2")
 for p in [1,5,4,8]:s.label("U1300."+str(p),"left" if p!=8 else "right",0 if p==5 else 40)
 s.join("C1300.1","U1300.1",(230,100),(520,100),(520,445))
 s.join("C1301.1","U1300.8",(1280,100),(1030,100),(1030,445))
 s.join("U1300.1","U1300.5",(550,445),(550,775))
 s.text(65,1000,"DIR=VCCA → A→B 고정 · EN 기본 Low / RESET_N 기본 Low(assert)","caption")
 return s,refs

def placeholder():
 refs=["U900"];s=Sheet("B9 · MOSCATO 인터페이스 (실제 IC 회로 미확정)",850)
 s.ic("U900",620,220,[1,2,3,4,5],[6,7,8,9],w=360,step=75)
 for p in C["U900"]["pins"]:s.label("U900."+p["number"],"left" if int(p["number"])<=5 else "right",100)
 s.text(80,760,"핀1~9는 프로젝트 임시 번호 · 내부 승압/반전 회로와 R/L/C를 추정해 그리지 않음","caption")
 return s,refs

def testpoints(refs,title):
 rows=math.ceil(len(refs)/4);s=Sheet(title,130+rows*125)
 for i,r in enumerate(refs):
  x=80+(i%4)*385;y=140+(i//4)*125;s.part(r,x,y);s.label(r+".1",length=30)
 s.text(35,s.h-20,"TP는 전기적 버퍼가 아님 · 각 패드의 명명 넷으로 원 회로에 직접 연결","small")
 return s,refs

def headers():
 refs=["J1400","J1401","J1402","J1403","J1404"];s=Sheet("B14 · DUT 헤더 실제 핀 결선",1600)
 for r,x,y in [("J1400",100,140),("J1401",850,140),("J1402",850,700),("J1403",100,900),("J1404",850,1030)]:
  ps=[p["number"] for p in C[r]["pins"]];s.ic(r,x,y,[],ps,w=280,step=43)
  for p in C[r]["pins"]:s.label(r+"."+p["number"],length=45)
 s.text(50,1570,"기능 기준 도면이며 커넥터 실물 정면도 아님 · 조립은 pin1·맞물림 방향을 별도 대조","caption")
 return s,refs

def services():
 refs=[r for r,c in C.items() if block(c)==15];s=Sheet("B15 · 표시 LED / 서비스 패드 / 기구",1320)
 for i,(r,d) in enumerate([("R1500","D1500"),("R1501","D1501"),("R1502","D1502")]):
  y=170+i*200;s.part(r,380,y);s.part(d,650,y)
  # resistor pin2 feeds LED anode2; route above the LED, keeping K1 distinct.
  s.label(r+".1","left",80)
  s.join(r+".2",d+".2",(470,y),(470,y-70),(750,y-70),(750,y))
  s.label(d+".1")
  s.text(850,y,["AUX_5V · 전원 표시","MCU LED_STATUS · High에서 점등","MCU LED_FAULT · High에서 점등"][i],"caption")
 tps=[r for r in refs if r.startswith("TP")]
 for i,r in enumerate(tps):
  x=90+(i%3)*510;y=830+(i//3)*130;s.part(r,x,y);s.label(r+".1",length=30)
 for i,r in enumerate(["H1500","H1501","H1502","H1503","LOGO1500"]):
  s.mark(r);s.text(65+i*300,1240,r,"small")
  if r.startswith("H"):s.raw(f'<circle cx="{100+i*300}" cy="1190" r="18" class="body"/>')
 s.text(50,1290,"홀: 3.2mm NPTH, 전기 핀 없음 · LOGO1500: 실크 지시, 전기 소자 아님","caption")
 return s,refs

def mcu():
 refs=[r for r,c in C.items() if block(c)==11];s=Sheet("B11 · MCU 전원·클록·리셋·SWD와 모든 GPIO",2110,2400)
 left=[1,24,36,48,9,8,23,35,47,5,6,7,44,34,37,2,3,4,20,25,26,27,28,29]
 right=[p["number"] for p in C["U1100"]["pins"] if int(p["number"]) not in left]
 s.ic("U1100",1020,170,left,right,w=370,step=70)
 for p in C["U1100"]["pins"]:
  s.label("U1100."+p["number"],"left" if int(p["number"]) in left else "right",45)
 caps(s,["C1100","C1101","C1102","C1103","C1104"],120,90,170)
 s.part("R1103",400,500);s.label("R1103.1","left",60);s.label("R1103.2","right",60)
 caps(s,["C1105","C1106"],600,200,270)
 # Crystal and load caps form a connected loop, with case pads separate to GND.
 s.part("Y1100",380,990);s.part("R1102",650,990)
 s.join("Y1100.3","R1102.2",(490,990),(490,1055),(740,1055),(740,990))
 s.label("R1102.1","left",40);s.label("Y1100.1","left",30)
 s.label("Y1100.2");s.label("Y1100.4")
 s.part("C1107",150,1170,True);s.part("C1108",700,1170,True)
 for r in ["C1107","C1108"]:s.label(r+".1","left",30);s.label(r+".2")
 for r,x in [("R1100",170),("C1109",400),("SW1100",690)]:
  s.part(r,x,1470,True);s.label(r+".1","left",25);s.label(r+".2","right",25)
 s.part("R1101",190,1800,True);s.label("R1101.1","left",30);s.label("R1101.2")
 s.ic("J1101",450,1750,[],[1,2],w=250,step=70)
 for p in [1,2]:s.label("J1101."+str(p),length=30)
 for r,y in [("R1104",450),("R1105",650)]:
  s.part(r,1900,y);s.label(r+".1","left",60);s.label(r+".2","right",60)
 ps=[p["number"] for p in C["J1100"]["pins"]]
 s.ic("J1100",1750,920,[],ps,w=280,step=70)
 for p in ps:s.label("J1100."+p,length=45)
 # Draw the local application circuits into the MCU; remote GPIO nets stay labelled.
 s.join("C1100.1","U1100.1",(90,120),(900,120),(900,265))
 for pin in [24,36,48]:
  a=s.at("U1100",pin);s.join("U1100.1",a,(900,265),(900,a[1]))
 s.join("R1103.2","U1100.9",(850,500),(850,545))
 s.join("C1105.1","R1103.2",(200,600),(850,600),(850,500))
 s.join("Y1100.1","U1100.5",(280,990),(280,895))
 s.join("R1102.1","U1100.6",(590,965))
 s.join("C1107.1","Y1100.1",(150,990))
 s.join("C1108.1","R1102.2",(740,1110),(740,990))
 s.join("R1100.2","U1100.7",(100,1530),(100,1360),(880,1360),(880,1035))
 s.join("C1109.1","SW1100.1",(400,1360),(690,1360))
 s.join("C1109.1","U1100.7",(400,1360),(880,1360),(880,1035))
 s.join("R1101.1","U1100.44",(920,1740),(920,1105))
 s.join("J1101.1","R1101.1",(920,1845),(920,1740))
 s.text(1550,1850,"VBAT 핀1 = CTRL_3V3 (B3 VBAT와 별개)","caption")
 s.text(1550,1900,"각 명명 넷은 왼쪽 MCU의 해당 핀과 연결","caption")
 s.text(1550,1950,"SWD 헤더는 실물 정면도가 아닌 전기 핀맵","caption")
 return s,refs

def usb():
 refs=[r for r,c in C.items() if block(c)==12 and not r.startswith("#")];s=Sheet("B12 · USB-C / ESD / ADuM4160 절연",1810,2200)
 s.ic("J1200",60,180,[],[p["number"] for p in C["J1200"]["pins"]],w=320,step=55)
 for p in C["J1200"]["pins"]:s.label("J1200."+p["number"],length=35)
 s.ic("U1200",1050,580,[1,3,4,5,6,7,(2,8)],[16,14,13,12,11,10,(9,15)],w=350,step=85)
 s.raw('<path d="M1225 660V1230" stroke="#b27c42" stroke-width="3" stroke-dasharray="8 8"/>')
 for r,x,p in [("R1203",800,6),("R1202",800,7),("R1205",1640,11),("R1204",1640,10)]:
  yy=s.at("U1200",p)[1];s.part(r,x,yy)
  # Match actual series resistor endpoint to the isolator pin.
  near=next(q["number"] for q in C[r]["pins"] if PINS[r+"."+q["number"]]==s.at("U1200",p)[2])
  other="2" if near=="1" else "1";s.join(r+"."+near,"U1200."+str(p));s.label(r+"."+other,"left" if x<1000 else "right",45)
 for p in [1,3,4,5,2,16,14,13,12,9]:s.label("U1200."+str(p),"left" if p<9 else "right",35)
 caps(s,["C1200","C1205"],130,750,230);caps(s,["C1201"],130,1250)
 caps(s,["C1202","C1203","C1204"],370,1570,210)
 for r,x in [("R1200",170),("R1201",440),("R1206",710),("R1207",1850)]:
  s.part(r,x,1510,True);s.label(r+".1","left",25);s.label(r+".2","right",25)
 s.ic("U1201",900,1370,[1,2],[3],w=290,step=65)
 for p in [1,2,3]:s.label("U1201."+str(p),"left" if p<3 else "right",0)
 for r,x in [("U1202",150),("U1203",450),("U1204",750)]:
  s.part(r,x,1740);s.label(r+".1","left",15);s.label(r+".2","right",15)
 # Route the two actual data paths from the connector through protection and series links.
 s.join("J1200.A6","R1202.1",(610,440),(610,1100))
 s.join("J1200.B6","J1200.A6",(610,880),(610,440))
 s.join("J1200.A7","R1203.1",(660,495),(660,1015))
 s.join("J1200.B7","J1200.A7",(660,935),(660,495))
 s.join("U1201.1","R1202.1",(735,1465),(735,1280),(610,1280),(610,1100))
 s.join("U1201.2","R1203.1",(810,1530),(810,1320),(660,1320),(660,1015))
 s.text(1300,1720,"USB_GND와 GND 사이 전기 배선 없음","caption")
 s.text(1300,1760,"ESD는 host측 USB_GND로 귀환","caption")
 return s,refs

def compose(name,children,title):
 """One block, several complete application circuits; do not shrink to thumbnail."""
 width=1600;height=sum(s.h*1600/s.w for s,refs in children)+90
 pieces=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}"><style>{STYLE}</style><rect width="100%" height="100%" fill="white"/>',
         f'<text x="35" y="40" class="title">{E(title)}</text>']
 y=70;allparts=set();terms={};nw=0
 for s,refs in children:
  import re
  source=(DEST/(s.saved_name+".svg")).read_text(encoding="utf-8")
  source=source.replace('viewBox=',f'x="0" y="{y}" width="1600" height="{s.h*1600/s.w}" viewBox=',1)
  pieces.append(source);y+=s.h*1600/s.w
  allparts.update(refs);terms.update({k:v[2] for k,v in s.ends.items()});nw+=len(s.wires)
 pieces.append('</svg>');(DEST/(name+".svg")).write_text(''.join(pieces),encoding='utf-8')
 AUDIT.append({"name":name,"components":sorted(allparts),"terminals":terms,"checked_wires":nw,"canvas":[width,height]})

def build():
 plans={};counter={}
 def add(b,label,pair):
  s,refs=pair;i=counter.get(b,0)+1;counter[b]=i;name=f"B{b}_{i}";s.save(name,refs);s.saved_name=name
  plans.setdefault(str(b),[]).append([label,name]);return pair
 def multi(b,title,items):
  children=[add(b,label,pair) for label,pair in items]
  compose(f"B{b}_0",children,title);plans[str(b)].insert(0,["통합 전체",f"B{b}_0"])
 add(2,"통합 회로",buck(200));add(3,"통합 회로",buck(300));add(4,"통합 회로",ldo(400))
 multi(5,"B5 · 세 LDO의 전체 회로",[("DIG",ldo(500)),("VDDI",ldo(520)),("VCI",ldo(540))])
 multi(6,"B6 · 보조 LDO 전체 회로",[("VDDIO1V2",ldo(600)),("SYS_1V8",ldo(620))])
 multi(7,"B7 · 10개 양전압 채널 전체 회로",[(next(c["rail"] for c in FW["channels"] if c["ref"]==f"U{n}"),ina(n)) for n in range(700,800,10)])
 multi(8,"B8 · 부유 전원 / 절연 I2C / VGL 2채널",[("부유 전원",floating_power()),("절연 I2C",isolator()),("VGL1",ina(820)),("VGL2",ina(840))])
 add(9,"임시 인터페이스",placeholder())
 alltp=[r for r,c in C.items() if block(c)==10 and not r.startswith("#")]
 add(10,"전체 테스트포인트",testpoints(alltp,"B10 · 전체 관측 위치"))
 add(11,"MCU 통합 회로",mcu());add(12,"USB 통합 회로",usb());add(13,"통합 회로",level())
 add(14,"전체 헤더",headers());add(15,"통합 회로",services())
 # Every block's electrical component is present in its full view.
 for b in range(2,16):
  full=next(x for x in AUDIT if x["name"]==plans[str(b)][0][1])
  required={r for r,c in C.items() if block(c)==b and not r.startswith("#")}
  assert required<=set(full["components"]),(b,required-set(full["components"]))
 (OUT/"diagram_plan.json").write_text(json.dumps(plans,ensure_ascii=False,indent=2),encoding="utf-8")
 (OUT/"SCHEMATIC_DRAWING_AUDIT.json").write_text(json.dumps({"type":"authored application schematics","diagrams":AUDIT},ensure_ascii=False,indent=2),encoding="utf-8")
 return plans,AUDIT

if __name__=="__main__":
 build();print("Authored schematics:",len(AUDIT),"all terminal/net checks passed")
