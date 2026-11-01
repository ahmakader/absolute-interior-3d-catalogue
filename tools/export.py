import numpy as np, subprocess, base64, os
from build import split_and_uv
CFG={'sofa':(['fabric','wood','pillow'],3.1/1.046,[.35,.45,.35]),
     'chair':(['tweed','leather','brass'],0.80/0.915,[1,1,1]),
     'table':(['stone','wood'],0.9/1.094,[1,1]),
     'armchair':(['leather','wood'],0.85/0.755,[1,1])}
def export(name,v,f,lab,tag):
    names,scale,tile=CFG[name]
    sc=split_and_uv(v,f,lab,names,tile,scale)
    p=f'../work/{name}_{tag}.glb'
    sc.export(p); o=p.replace('.glb','_c.glb')
    subprocess.run(['node','c2.mjs',p,o],cwd='../gt',check=True,capture_output=True)
    d=f'../work/{tag}'; os.makedirs(d,exist_ok=True)
    open(f'{d}/{name}.glb.txt','w').write(base64.b64encode(open(o,'rb').read()).decode())
    print('exported',name,tag,os.path.getsize(o)//1024,'KB')
def load_split(name,path=None):
    import trimesh
    names=CFG[name][0]
    sc=trimesh.load(path or f'../glb/{name}_split.bak.glb',force='scene')
    V=[];F=[];L=[];off=0
    for gname,g in sc.geometry.items():
        zi=[i for i,nm in enumerate(names) if nm in gname][0]
        V.append(np.asarray(g.vertices));F.append(np.asarray(g.faces)+off);L.append(np.full(len(g.faces),zi));off+=len(g.vertices)
    m=trimesh.Trimesh(np.concatenate(V),np.concatenate(F),process=False);lab=np.concatenate(L)
    m.merge_vertices(digits_vertex=5)
    return np.asarray(m.vertices),np.asarray(m.faces),lab
