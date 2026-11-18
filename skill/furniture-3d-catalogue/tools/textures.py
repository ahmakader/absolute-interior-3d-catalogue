"""Procedural PBR texture sets (albedo / normal / roughness) for the catalogue materials.
Usage: python textures.py [leather|wood|travertine|boucle|marble]
"""
import numpy as np, sys, os
from PIL import Image
from scipy.spatial import cKDTree
N=1024
OUT='../tex/'; os.makedirs(OUT,exist_ok=True)

def fnoise(beta=2.0,ax=1.0,ay=1.0,seed=0,n=N):
    r=np.random.default_rng(seed)
    w=np.fft.fft2(r.standard_normal((n,n)))
    fy=np.fft.fftfreq(n)[:,None]*n; fx=np.fft.fftfreq(n)[None,:]*n
    f=np.sqrt((fx/ax)**2+(fy/ay)**2); f[0,0]=1
    out=np.real(np.fft.ifft2(w*f**(-beta/2))); out-=out.mean(); out/=np.abs(out).max()+1e-9
    return out
def norm01(a): a=a-a.min(); return a/(a.max()+1e-9)
def smooth(a,lo,hi): t=np.clip((a-lo)/(hi-lo),0,1); return t*t*(3-2*t)
def to_normal(h,strength=None,target=0.6):
    gx=(np.roll(h,-1,1)-np.roll(h,1,1))/2
    gy=(np.roll(h,-1,0)-np.roll(h,1,0))/2
    k=target/(np.percentile(np.sqrt(gx*gx+gy*gy),98)+1e-9)
    gx*=k;gy*=k
    l=np.sqrt(gx*gx+gy*gy+1)
    return np.clip(((np.stack([-gx/l,gy/l,1/l],-1))*.5+.5)*255+.5,0,255).astype(np.uint8)
def save(name,alb,nrm,rough):
    Image.fromarray(np.clip(alb,0,255).astype(np.uint8)).save(OUT+name+'_albedo.webp',quality=90)
    # normal maps: JPEG with 4:4:4 chroma — lossy WebP/4:2:0 subsampling corrupts normal maps
    Image.fromarray(nrm).save(OUT+name+'_normal.jpg',quality=92,subsampling=0)
    r=Image.fromarray(np.clip(rough*255,0,255).astype(np.uint8)).resize((512,512),Image.LANCZOS)
    r.convert('L').save(OUT+name+'_rough.webp',quality=90)

def voronoi(cells,seed,jit=.9):
    r=np.random.default_rng(seed)
    g=np.stack(np.meshgrid(np.arange(cells),np.arange(cells),indexing='ij'),-1).reshape(-1,2).astype(float)
    p=(g+.5+(r.random(g.shape)-.5)*jit)/cells
    pp=np.concatenate([p+[dy,dx] for dy in (-1,0,1) for dx in (-1,0,1)])
    t=cKDTree(pp)
    yy,xx=np.meshgrid((np.arange(N)+.5)/N,(np.arange(N)+.5)/N,indexing='ij')
    d,_=t.query(np.stack([yy.ravel(),xx.ravel()],1),k=2)
    return d[:,0].reshape(N,N),d[:,1].reshape(N,N)

def leather():
    cells=64
    f1,f2=voronoi(cells,3); e=(f2-f1)*cells                    # 0 at cell edges
    micro=smooth(e,0.0,0.42)                                     # plateau 1, creases 0
    f1b,f2b=voronoi(40,8); eb=(f2b-f1b)*40
    micro=micro*(0.75+0.25*smooth(eb,0,.5))
    # soft cm-scale folds + very low-frequency blotch
    macro=fnoise(3.2,seed=11)                                    # smooth wrinkles
    ridge=1-np.abs(fnoise(2.4,ax=1,ay=1,seed=12))                # creased folds
    fold=0.6*macro+0.4*smooth(ridge,.55,1)
    h=0.30*micro+1.2*fold
    blot=fnoise(2.6,seed=13)
    alb=0.70+0.08*blot-0.03*(1-micro)*(0.7+0.3*smooth(ridge,.4,1))+0.05*fold
    # polished wear: slightly lighter on high points
    alb+=0.04*smooth(h,.5,1.2)
    rough=0.46+0.20*(1-micro)+0.07*blot-0.05*smooth(h,.7,1.3)
    rgb=np.stack([alb,alb,alb],-1)*255
    nrm=to_normal(0.10*micro+0.55*fold,0.9)
    save('leather',rgb,nrm,rough)

def wood(name,light,dark,seed,rings=6,pore=.05,fig=.5):
    yy,xx=np.meshgrid(np.arange(N)/N,np.arange(N)/N,indexing='ij')
    L=np.array(light)/255.; D=np.array(dark)/255.
    warp=0.012*np.sin(2*np.pi*xx+1.3)+0.01*np.sin(2*np.pi*(2*xx)+4.1)+0.03*fnoise(2.4,ax=.35,ay=1.0,seed=seed)
    y=yy+warp
    band=0.5+0.5*np.sin(2*np.pi*(rings*y+0.35*fnoise(1.8,ax=.25,ay=1,seed=seed+7)))
    fine=0.5+0.5*np.sin(2*np.pi*(rings*5*y+1.2*fnoise(1.6,ax=.25,ay=1,seed=seed+8)))
    fine=fine**2.4
    fib=fnoise(1.1,ax=0.02,ay=1.0,seed=seed+2)
    fib2=fnoise(1.6,ax=0.08,ay=1.0,seed=seed+5)
    t=0.22+fig*0.55*band**1.3+0.42*fine*(0.5+0.5*band)+0.2*fib+0.08*fib2
    pn=fnoise(0.5,ax=0.03,ay=1.0,seed=seed+3); p=smooth(pn,np.quantile(pn,1-pore),np.quantile(pn,1-pore)+.15)
    t=np.clip(t+0.09*p,0,1)
    col=L[None,None,:]*(1-t[...,None])+D[None,None,:]*t[...,None]
    col*=(0.965+0.035*fnoise(2.0,seed=seed+4))[...,None]
    h=-0.6*p-0.18*fine+0.10*fib
    nrm=to_normal(h,0.45)
    rough=0.50+0.18*p+0.05*fib2
    save(name,col*255,nrm,rough)


def travertine():
    yy,xx=np.meshgrid(np.arange(N)/N,np.arange(N)/N,indexing='ij')
    A=np.array((236,227,206))/255.;B=np.array((212,195,164))/255.;C=np.array((178,155,121))/255.
    band=0.5+0.5*np.sin(2*np.pi*(7*(yy+0.02*fnoise(2.2,ax=.3,ay=1,seed=61))+0.4*fnoise(1.6,ax=.2,ay=1,seed=62)))
    strata=fnoise(1.6,ax=0.06,ay=1.0,seed=63)
    fibre=fnoise(1.0,ax=0.03,ay=1.0,seed=64)
    t=np.clip(0.35+0.22*band+0.25*strata+0.10*fibre,0,1)
    dark=smooth(fnoise(1.8,ax=.08,ay=1,seed=65),0.45,0.9)          # warm brown streaks
    col=A*(1-t[...,None])+B*t[...,None]
    col=col*(1-0.35*dark[...,None])+C*(0.35*dark[...,None])
    pn=fnoise(0.5,ax=0.045,ay=1.0,seed=66); p=smooth(pn,np.quantile(pn,0.965),np.quantile(pn,0.965)+.1)  # elongated pits
    col=col*(1-0.12*p[...,None])
    col*=(0.975+0.025*fnoise(2.0,seed=67))[...,None]
    h=-0.5*p+0.15*strata
    save('travertine',col*255,to_normal(h,0.35),0.58+0.12*p+0.05*strata)

def boucle():
    # dense curly yarn loops: random points convolved with ring kernels (FFT), clumped by low-freq density
    rng=np.random.default_rng(5)
    yy,xx=np.meshgrid(np.arange(N)-N//2,np.arange(N)-N//2,indexing='ij'); rr=np.sqrt(yy**2+xx**2)
    clump=smooth(fnoise(2.2,seed=41),-.35,.45)            # where yarn bunches into nubs
    h=np.zeros((N,N))
    for r0,cnt,w in ((5.0,9000,1.3),(7.5,5000,1.6),(10.5,2500,1.9)):
        P=np.zeros((N,N)); ys=rng.integers(0,N,cnt*3); xs=rng.integers(0,N,cnt*3)
        keep=rng.random(cnt*3)<(0.7+0.3*clump[ys,xs]); ys,xs=ys[keep][:cnt],xs[keep][:cnt]
        np.add.at(P,(ys,xs),rng.uniform(.6,1,len(ys)))
        K=np.exp(-((rr-r0)/w)**2); K=np.fft.ifftshift(K)
        h+=np.real(np.fft.ifft2(np.fft.fft2(P)*np.fft.fft2(K)))
    h=1-np.exp(-1.1*h)                                     # soft saturation: overlapping loops pile up
    h=0.95*h+0.05*clump
    cav=1-h
    alb=np.clip(0.99-0.38*cav**1.3+0.02*fnoise(2.6,seed=32),0,1)
    save('boucle',np.stack([alb]*3,-1)*255,to_normal(h,target=0.9),0.95-0.12*h)

def marble(name,base,vein,seed,dark=False):
    from scipy.ndimage import map_coordinates
    yy,xx=np.meshgrid(np.arange(N),np.arange(N),indexing='ij')
    def z(a): return a/a.std()
    def warp(a,amt,sd):
        dy=z(fnoise(3.6,seed=sd))*amt; dx=z(fnoise(3.6,seed=sd+1))*amt
        return map_coordinates(a,[(yy+dy)%N,(xx+dx)%N],order=1,mode='wrap')
    B=np.array(base)/255.;Vc=np.array(vein)/255.
    n1=warp(z(fnoise(3.8,ax=1,ay=.5,seed=seed)),70,seed+10)
    n1=n1+0.08*z(fnoise(2.2,seed=seed+11))                          # slight irregularity along veins
    v1=1-smooth(np.abs(n1),0,0.07)
    n2=warp(z(fnoise(3.4,seed=seed+3)),45,seed+20)+0.06*z(fnoise(2.0,seed=seed+21))
    v2=1-smooth(np.abs(n2),0,0.035)
    halo=1-smooth(np.abs(n1),0,0.45)
    cloud=z(fnoise(2.8,seed=seed+5))*.33
    vis2=smooth(z(fnoise(3.0,seed=seed+6)),-.3,.8)
    t=np.clip(0.9*v1+0.5*v2*vis2+0.12*halo,0,1)
    col=B*(1+0.04*cloud[...,None])
    col=col*(1-t[...,None])+Vc*t[...,None]
    h=0.3*cloud-0.2*t
    save(name,col*255,to_normal(h,target=0.12),0.12+0.06*t+0.02*cloud)

if __name__=='__main__':
    what=sys.argv[1:] or ['leather','wood','travertine']
    if 'travertine' in what: travertine()
    if 'boucle' in what: boucle()
    if 'marble' in what:
        marble('marble_white',(238,236,232),(120,118,116),71)
        marble('marble_black',(26,25,26),(205,202,196),81)
    if 'leather' in what: leather()
    if 'wood' in what:
        wood('wood_walnut',(128,88,58),(52,32,21),21,rings=5,pore=.05,fig=.5)
        wood('wood_oak',(206,164,110),(150,108,64),31,rings=6,pore=.06,fig=.42)
        wood('wood_ash',(226,201,158),(186,152,106),41,rings=5,pore=.05,fig=.36)
        wood('wood_ebony',(52,40,34),(24,18,16),51,rings=5,pore=.04,fig=.3)
