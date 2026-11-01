import numpy as np, trimesh
from build import *
W,D=1.6,0.45
parts=[]   # (mesh, zone) zone: 0 wood, 1 cane, 2 brass
def box(w,h,d,cx,cy,cz,zone):
    m=trimesh.creation.box(extents=(w,h,d)); m.apply_translation((cx,cy,cz)); parts.append((m,zone))
FZ=D/2                       # front plane z
# carcass + top
box(W,0.56,D-0.02,0,0.50,-0.01,0)
box(W+0.02,0.02,D+0.02,0,0.79,0,0)
# front layout
y0,y1=0.23,0.77
def door(x0,x1):
    fw=0.05; t=0.02
    cx=(x0+x1)/2; w=x1-x0; h=y1-y0; cy=(y0+y1)/2
    box(w,fw,t,cx,y1-fw/2,FZ-t/2,0); box(w,fw,t,cx,y0+fw/2,FZ-t/2,0)
    box(fw,h-2*fw,t,x0+fw/2,cy,FZ-t/2,0); box(fw,h-2*fw,t,x1-fw/2,cy,FZ-t/2,0)
    box(w-2*fw+0.004,h-2*fw+0.004,0.007,cx,cy,FZ-t+0.0035+0.004,1)   # recessed cane
door(-0.79,-0.34); door(-0.335,0.115)
# drawers
dx0,dx1=0.125,0.79; gap=0.006; n=3; hh=((y1-y0)-gap*(n-1))/n
for i in range(n):
    yb=y0+i*(hh+gap)
    box(dx1-dx0,hh,0.02,(dx0+dx1)/2,yb+hh/2,FZ-0.01,0)
    k=trimesh.creation.cylinder(radius=0.014,height=0.018,sections=28)
    k.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2,(1,0,0)))
    k.apply_translation(((dx0+dx1)/2,yb+hh/2,FZ+0.009)); parts.append((k,2))
for kx in (-0.372,-0.298):
    k=trimesh.creation.cylinder(radius=0.012,height=0.016,sections=24)
    k.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2,(1,0,0)))
    k.apply_translation((kx,0.50,FZ+0.008)); parts.append((k,2))
# tapered, splayed legs
for sx in (-1,1):
    for sz in (-1,1):
        tx,tz=sx*0.70,sz*0.15; top=0.026; bot=0.016; spl=0.03
        pts=[]
        for dx,dz in [(-1,-1),(1,-1),(1,1),(-1,1)]:
            pts.append((tx+dx*top,0.23,tz+dz*top))
            pts.append((tx+sx*spl+dx*bot,0.0,tz+sz*spl*0.5+dz*bot))
        parts.append((trimesh.convex.convex_hull(np.array(pts)),0))
V=[];F=[];L=[];o=0
for m,z in parts:
    V.append(m.vertices);F.append(m.faces+o);L.append(np.full(len(m.faces),z));o+=len(m.vertices)
V=np.vstack(V);F=np.vstack(F);L=np.concatenate(L)
sc=split_and_uv(V,F,L,['wood','cane','brass'],[1,1,1],1.0,debug_cols=[[110,70,40,255],[230,190,110,255],[210,170,70,255]],flat=True)
sc.export('../glb/sideboard_split.glb')
print('faces',len(F),np.bincount(L)/len(L))
