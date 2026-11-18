import numpy as np,trimesh
from shapely.geometry import Polygon
def outline(m,y,n=700,sm=3):
    sec=m.section(plane_origin=[0,y,0],plane_normal=[0,1,0]); loop=max(sec.discrete,key=len)
    P=loop[:,[0,2]]
    seg=np.r_[0,np.cumsum(np.linalg.norm(np.diff(np.vstack([P,P[:1]]),axis=0),axis=1))]
    t=np.linspace(0,seg[-1],n,endpoint=False)
    Q=np.c_[np.interp(t,seg,np.r_[P[:,0],P[0,0]]),np.interp(t,seg,np.r_[P[:,1],P[0,1]])]
    for _ in range(sm): Q=(np.roll(Q,1,0)+2*Q+np.roll(Q,-1,0))/4
    return Q
def prism(Q,h,y0=0.0,bevel=0.0):
    poly=Polygon(Q).buffer(0)
    if bevel: poly=poly.buffer(-bevel).buffer(bevel)
    pr=trimesh.creation.extrude_polygon(poly,h)
    pv=np.asarray(pr.vertices); pv=np.c_[pv[:,0],pv[:,2]+y0,pv[:,1]]; pf=np.asarray(pr.faces)[:,::-1]
    # subdivide tall side faces so vertex normals don't smear across the cap edge
    t=trimesh.Trimesh(pv,pf,process=False)
    return np.asarray(t.vertices),np.asarray(t.faces)
def hard_caps(v,f):
    """re-index so cap faces (|ny|>.5) and side faces don't share vertices -> crisp edges"""
    t=trimesh.Trimesh(v,f,process=False);ny=np.abs(t.face_normals[:,1])
    V=[];F=[];off=0
    for sel in (ny>.5, ny<=.5):
        ff=f[sel];u,inv=np.unique(ff.ravel(),return_inverse=True)
        V.append(v[u]);F.append(inv.reshape(-1,3)+off);off+=len(u)
    return np.vstack(V),np.vstack(F)
