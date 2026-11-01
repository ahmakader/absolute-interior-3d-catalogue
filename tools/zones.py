import numpy as np, trimesh, fast_simplification
from scipy.spatial import cKDTree
import scipy.sparse as sp

def load(path):
    sc=trimesh.load(path,force='scene')
    g=sc.to_geometry() if hasattr(sc,'to_geometry') else sc.dump(concatenate=True)
    return g

def face_colors(g):
    img=np.asarray(g.visual.material.baseColorTexture.convert('RGB')).astype(np.float32)/255
    H,W,_=img.shape
    fc=g.visual.uv[g.faces].mean(1)
    x=np.clip((fc[:,0]*(W-1)).astype(int),0,W-1); y=np.clip(((1-fc[:,1])*(H-1)).astype(int),0,H-1)
    return img[y,x]

def smooth_labels(g,lab,n,iters=4):
    adj=g.face_adjacency
    nf=len(g.faces)
    A=sp.coo_matrix((np.ones(len(adj)),(adj[:,0],adj[:,1])),shape=(nf,nf))
    A=(A+A.T).tocsr()
    for _ in range(iters):
        oh=np.eye(n,dtype=np.float32)[lab]
        votes=A@oh+oh*0.5
        lab=votes.argmax(1)
    return lab

def weld(g):
    m=trimesh.Trimesh(np.asarray(g.vertices).copy(),np.asarray(g.faces).copy(),process=False)
    m.merge_vertices(digits_vertex=5)
    return m

def decimate(g,target):
    g=weld(g)
    v,f=fast_simplification.simplify(np.asarray(g.vertices,dtype=np.float64),np.asarray(g.faces,dtype=np.int32),target_count=target,agg=7)
    return trimesh.Trimesh(v,f,process=False)

def transfer(src,lab,dst):
    t=cKDTree(src.triangles_center)
    _,i=t.query(dst.triangles_center)
    return lab[i]

def knn_smooth(d,lab,n,k=70,iters=3):
    cen=d.triangles_center
    t=cKDTree(cen)
    _,idx=t.query(cen,k=k,workers=-1)
    for _ in range(iters):
        oh=np.eye(n,dtype=np.float32)[lab]
        votes=oh[idx].sum(1)
        lab=votes.argmax(1)
    return lab

from scipy.sparse.csgraph import connected_components
def adj_matrix(d):
    a=d.face_adjacency; n=len(d.faces)
    A=sp.coo_matrix((np.ones(len(a)),(a[:,0],a[:,1])),shape=(n,n)); return (A+A.T).tocsr()

def close_label(d,lab,k,rings):
    """morphological closing of zone k on the face graph: fills holes, removes speckle"""
    A=adj_matrix(d); x=(lab==k)
    for _ in range(rings): x=x|((A@x.astype(np.float32))>0)
    for _ in range(rings): x=x&~((A@(~x).astype(np.float32))>0)
    out=lab.copy(); out[x]=k; return out

def keep_largest(d,lab,k,n_keep,fallback):
    """keep only the n largest connected components of zone k; others become fallback"""
    A=adj_matrix(d); m=(lab==k); idx=np.where(m)[0]
    sub=A[idx][:,idx]
    nc,cl=connected_components(sub)
    sizes=np.bincount(cl); keep=set(np.argsort(sizes)[::-1][:n_keep])
    out=lab.copy()
    for ci in range(nc):
        if ci not in keep: out[idx[cl==ci]]=fallback
    return out,idx,cl,keep
