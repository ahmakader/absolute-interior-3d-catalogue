import numpy as np, scipy.sparse as sp
def vert_adj(nv,f):
    e=np.vstack([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]])
    A=sp.coo_matrix((np.ones(len(e)),(e[:,0],e[:,1])),shape=(nv,nv));A=((A+A.T)>0).astype(float).tocsr()
    d=np.asarray(A.sum(1)).ravel();return sp.diags(1/np.maximum(d,1))@A
def fields(nv,f,lab,L,iters=12):
    F=np.zeros((nv,L))
    for k in range(L): F[:,k]=np.bincount(f.ravel(),weights=np.repeat((lab==k).astype(float),3),minlength=nv)
    F/=np.maximum(F.sum(1,keepdims=True),1e-9)
    W=vert_adj(nv,f)
    for _ in range(iters): F=0.5*F+0.5*(W@F)
    return F
def iso_cut(v,f,Fv,s):
    """split triangles along s=0 (s per vertex). Fv per-vertex fields are interpolated for new verts."""
    V=[v];FF=[Fv];SS=[s];nv=len(v);cache={}
    def mid(a,b):
        nonlocal nv
        k=(min(a,b),max(a,b))
        if k in cache: return cache[k]
        t=s[a]/(s[a]-s[b]);V.append((v[a]+(v[b]-v[a])*t)[None]);FF.append((Fv[a]+(Fv[b]-Fv[a])*t)[None]);SS.append(np.zeros(1))
        cache[k]=nv;nv+=1;return cache[k]
    up=s>0;cnt=up[f].sum(1);out=[]
    for fi in range(len(f)):
        a,b,c=f[fi];n=cnt[fi]
        if n==0 or n==3: out.append((a,b,c));continue
        tri=[a,b,c];u=[up[a],up[b],up[c]]
        lone=u.index(True) if n==1 else u.index(False)
        x,y,z=tri[lone],tri[(lone+1)%3],tri[(lone+2)%3]
        m1=mid(x,y);m2=mid(x,z)
        out+= [(x,m1,m2),(m1,y,z),(m1,z,m2)]
    return np.vstack(V),np.array(out),np.vstack(FF),np.concatenate(SS)
def clean_cut(v,f,lab,L,iters=12,order=None):
    Fv=fields(len(v),f,lab,L,iters)
    for k in (order or range(L-1)):
        oth=np.delete(Fv,k,1).max(1);s=Fv[:,k]-oth
        s[np.abs(s)<1e-6]=1e-6
        v,f,Fv,_=iso_cut(v,f,Fv,s)
    # face label: argmax of mean vertex fields, but exact-on-boundary verts are ties -> use centroid avg
    lab=Fv[f].mean(1).argmax(1)
    return v,f,lab
def masked_taubin(v,f,mask,it=20,lam=.5,mu=-.53):
    W=vert_adj(len(v),f);v=v.copy()
    for _ in range(it):
        for k in (lam,mu):
            d=W@v-v; v[mask]+=k*d[mask]
    return v
