import sys, numpy as np
from zones import *
from build import *

def nd(col,protos):
    p=np.array(protos)/255.
    return np.linalg.norm(col[:,None,:]-p[None],axis=2).min(1)

def lab_sofa(col,hy,g):
    brown=[[107,65,35],[80,54,34]]; rust=[[137,80,44]]; fab=[[179,160,141],[169,149,127],[143,116,90]]
    db,dr,df=nd(col,brown),nd(col,rust),nd(col,fab)
    lab=np.zeros(len(col),int)
    lab[((db<df)&(db<dr)&(hy<0.30))|(hy<0.13)]=1
    lab[(dr<df)&(dr<db)&(hy>0.30)]=2
    return lab
def lab_chair(col,hy,g):
    lum=col.mean(1)*255
    cen=g.triangles_center
    t=cKDTree(cen)
    _,idx=t.query(cen,k=80,workers=-1)
    sl=lum[idx].mean(1)
    thr=float(np.percentile(sl,float(__import__("os").environ.get("CHAIR_P","62"))))
    print("chair smoothed lum thr",thr)
    lab=np.zeros(len(col),int)          # 0 tweed
    lab[sl<thr]=1                        # leatherette wings
    lab[g.face_normals[:,2]<-0.2]=1      # rear-facing exterior is always leatherette
    brass=(nd(col,[[187,159,125]])<0.12)&(hy<0.22)
    lab[brass|(hy<0.07)]=2              # brass base
    return lab
def lab_sideboard(col,hy,g):
    straw=nd(col,[[201,153,89],[135,100,65]]); wood=nd(col,[[101,56,25],[60,30,10],[88,46,17]])
    lab=np.zeros(len(col),int)          # 0 walnut
    lab[(straw<wood)&(hy<0.95)]=1       # cane
    return lab
def lab_table(col,hy,g):
    lab=np.zeros(len(col),int)          # 0 travertine top
    lab[hy<0.84]=1                       # oak base
    return lab
def lab_armchair(col,hy,g):
    lab=np.zeros(len(col),int)          # 0 leather
    r,gc=col[:,0],col[:,1]
    lab[(hy<0.28)&(r>gc*1.25)]=1        # walnut legs
    return lab

CFG={
 'sofa':     dict(f=lab_sofa,     names=['fabric','wood','pillow'],    scale=3.1/1.046, target=90000, dbg=[[215,200,170,255],[110,70,40,255],[190,70,30,255]]),
 'chair':    dict(f=lab_chair,    names=['tweed','leather','brass'],   scale=0.80/0.915,target=90000, dbg=[[200,200,200,255],[40,40,40,255],[200,160,60,255]]),
 'sideboard':dict(f=lab_sideboard,names=['wood','cane'],               scale=1.6/1.032, target=90000, dbg=[[110,70,40,255],[230,190,110,255]]),
 'table':    dict(f=lab_table,    names=['stone','wood'],              scale=0.9/1.094, target=80000, dbg=[[225,210,185,255],[200,150,90,255]]),
 'armchair': dict(f=lab_armchair, names=['leather','wood'],            scale=0.85/0.755,target=90000, dbg=[[110,120,60,255],[110,70,40,255]]),
}
for name in sys.argv[1:]:
    c=CFG[name]
    src={'sofa':'hunyuan'}.get(name,name)
    g=load(f'../glb/{src}.glb')
    col=face_colors(g); cen=g.triangles_center; b=g.bounds
    hy=(cen[:,1]-b[0,1])/(b[1,1]-b[0,1])
    lab=c['f'](col,hy,g); n=len(c['names'])
    lab=smooth_labels(g,lab,n,6)
    d=decimate(g,c['target'])
    if name=='sideboard':
        import trimesh.smoothing as ts
        ts.filter_taubin(d,lamb=0.5,nu=-0.53,iterations=18)
    dl=smooth_labels(d,transfer(g,lab,d),n,3)
    if name in ('chair','sideboard'): dl=knn_smooth(d,dl,n,k=90,iters=4)
    fn=d.face_normals; dc=d.triangles_center
    if name=='chair':
        keepbrass=(dl==2)
        dl=close_label(d,dl,0,14)                       # fill leather blobs inside the tweed
        dl,_,_,_=keep_largest(d,dl,0,2,1)               # only seat + back cushion stay tweed
        dl[fn[:,2]<-0.2]=np.where(dl[fn[:,2]<-0.2]==2,2,1)
        dl[keepbrass]=2
    if name=='sideboard':
        dl,idx,cl,keep=keep_largest(d,dl,1,2,0)         # two cane doors
        # snap each door's cane to a clean rectangle on the front face
        for ci in keep:
            fi=idx[cl==ci]; cc=dc[fi]
            lo=np.percentile(cc[:,:2],4,axis=0)-0.004; hi=np.percentile(cc[:,:2],96,axis=0)+0.004; zmin=np.percentile(cc[:,2],5)-0.02
            inside=(dc[:,0]>=lo[0])&(dc[:,0]<=hi[0])&(dc[:,1]>=lo[1])&(dc[:,1]<=hi[1])&(dc[:,2]>=zmin)
            dl[inside]=1
    print(name,'faces',len(d.faces),dict(zip(c['names'],(np.bincount(dl,minlength=n)/len(dl)).round(3))))
    sc=split_and_uv(d.vertices,d.faces,dl,c['names'],[1.0]*n,c['scale'],debug_cols=c['dbg'])
    sc.export(f'../glb/{name}_split.glb')
