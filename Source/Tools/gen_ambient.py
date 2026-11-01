# Звуки Зоны: синтез с нуля (ветер, гул, далёкая перестрелка, вой). Никаких чужих записей.
import math, random, struct, wave, os
SR=22050; ROOT='/mnt/user-data/outputs/StalkerZone/Common/Sounds/SZ/Ambient'
def write(path,x):
    os.makedirs(os.path.dirname(path),exist_ok=True); pk=max(1e-9,max(abs(v) for v in x))
    with wave.open(path,'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(b''.join(struct.pack('<h',int(v/pk*0.8*32767)) for v in x))
def lp(x,a):
    y=0.0; o=[]
    for v in x: y+=a*(v-y); o.append(y)
    return o
def wind(seed):
    r=random.Random(seed); n=int(4*SR); x=lp([r.uniform(-1,1) for _ in range(n)],0.03)
    return [v*(math.sin(math.pi*i/n)**1.5)*(0.6+0.4*math.sin(2*math.pi*0.7*i/SR+seed)) for i,v in enumerate(x)]
def drone(seed):
    r=random.Random(seed); n=int(5*SR); f=r.uniform(38,52)
    return [(math.sin(2*math.pi*f*i/SR)+0.5*math.sin(2*math.pi*f*1.5*i/SR+0.3)+0.25*math.sin(2*math.pi*f*2.01*i/SR))
            *(math.sin(math.pi*i/n)**2)*(0.8+0.2*math.sin(2*math.pi*0.3*i/SR)) for i in range(n)]
def shots(seed):
    r=random.Random(seed); n=int(3*SR); x=[0.0]*n; t=0.2
    while t<2.6:
        p=int(t*SR); amp=r.uniform(0.4,1)
        for j in range(int(0.12*SR)):
            if p+j<n: x[p+j]+=r.uniform(-1,1)*amp*math.exp(-j/(0.02*SR))
        t+=r.choice([0.09,0.1,0.11,0.35,0.6])
    return lp(x,0.12)
def howl(seed):
    r=random.Random(seed); n=int(3*SR); out=[]; ph=0.0; f0=r.uniform(380,460)
    for i in range(n):
        u=i/n; f=f0*(1+0.35*math.sin(math.pi*u))+6*math.sin(2*math.pi*5*i/SR); ph+=2*math.pi*f/SR
        out.append((math.sin(ph)+0.3*math.sin(2*ph))*(math.sin(math.pi*u)**1.2))
    return lp(out,0.2)
for i in range(3): write(f'{ROOT}/Wind/wind_{i}.wav',wind(10+i))
for i in range(2): write(f'{ROOT}/Drone/drone_{i}.wav',drone(20+i))
for i in range(2): write(f'{ROOT}/Shots/shots_{i}.wav',shots(30+i))
for i in range(2): write(f'{ROOT}/Howl/howl_{i}.wav',howl(40+i))
print('ambient ok')
