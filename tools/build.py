import numpy as np, trimesh
from trimesh.visual.material import PBRMaterial
from trimesh.visual import TextureVisuals

def split_and_uv(v,f,lab,names,tile_m,real_scale,debug_cols=None,flat=False):
    """v,f: decimated mesh (Y up). lab: zone index per face. tile_m: tile size in metres per zone.
    real_scale: metres per model unit. Returns trimesh.Scene with one mesh per zone, box-projected UVs."""
    m=trimesh.Trimesh(v,f,process=False)
    vn=m.vertex_normals                      # smooth normals from welded mesh
    fn=m.face_normals
    ax=np.abs(fn).argmax(1)                   # dominant axis per face
    sc=trimesh.Scene()
    for zi,name in enumerate(names):
        idx=np.where(lab==zi)[0]
        if len(idx)==0: continue
        tri=f[idx]                            # (n,3)
        pos=v[tri].reshape(-1,3)*real_scale/ tile_m[zi]
        nrm=np.repeat(fn[idx],3,axis=0) if flat else vn[tri].reshape(-1,3)
        a=np.repeat(ax[idx],3)
        uv=np.zeros((len(pos),2))
        # axis 0 (x): uv=(z,y); axis1 (y): uv=(x,z); axis2 (z): uv=(x,y)
        for k,(ua,va) in enumerate([(2,1),(0,2),(0,1)]):
            s=a==k
            uv[s,0]=pos[s,ua]; uv[s,1]=pos[s,va]
        faces=np.arange(len(pos)).reshape(-1,3)
        mat=PBRMaterial(name=name,baseColorFactor=(debug_cols[zi] if debug_cols else [200,200,200,255]),roughnessFactor=0.8,metallicFactor=0.0)
        mesh=trimesh.Trimesh(vertices=v[tri].reshape(-1,3),faces=faces,vertex_normals=nrm,process=False)
        mesh.visual=TextureVisuals(uv=uv,material=mat)
        sc.add_geometry(mesh,geom_name=name,node_name=name)
    return sc
