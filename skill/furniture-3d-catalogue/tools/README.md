# Asset pipeline

These scripts prepared the models and textures in this repo. They're published as a reference for building your own catalogue, not as a one-click tool.

| Script | What it does |
|---|---|
| `zones.py` | Loads an image-to-3D GLB, reads the colour of each face from its baked texture, decimates the mesh and transfers zone labels. It also has label smoothing, morphological closing and helpers that keep the largest component. |
| `iso.py` | **Clean zone borders.** It smooths a per-vertex field for each zone and splits triangles exactly along the 0.5 iso-line, so material borders follow smooth curves instead of jagged triangle edges (`clean_cut`). `masked_taubin` smooths only selected vertices. |
| `plinth.py` | Takes a cross-section of a mesh at a given height and extrudes it into a clean solid. It's used to rebuild the sofa plinth. `hard_caps` keeps crisp edges between caps and sides. |
| `build.py` | Splits a labelled mesh into one mesh per zone and adds box-projected UVs in metres (`split_and_uv`). |
| `export.py` | Writes the zones to GLB and compresses them with `compress.mjs`. |
| `compress.mjs` | glTF-Transform: prune, weld, quantize (except UVs) and meshopt. |
| `sideboard_proc.py` | Builds the sideboard procedurally (box carcass, cane doors, drawers, tapered legs). |
| `textures.py` | Procedural PBR sets: leather, wood (walnut, oak, ash, ebony), travertine, boucle and marble. |

```bash
pip install -r requirements.txt
npm install            # for compress.mjs
python textures.py boucle marble
node compress.mjs in.glb out.glb
```

## Lessons learned

- **Never store normal maps as lossy WebP.** Chroma subsampling destroys them and the furniture looks speckled and fuzzy. Use JPEG with `subsampling=0`, or PNG.
- **Normalise normal-map strength.** `to_normal()` scales the gradients so the 98th-percentile slope matches a target. You then tune intensity with `normalScale` in the page instead of regenerating.
- **Image-to-3D meshes are noisy.** Smooth the shading rather than adding bump detail. Rebuild simple primitives (cylinders, plinths) as clean solids.
- **Zones from texture colour.** Separate them by local contrast and chromaticity rather than raw colour, because shading on the baked texture fools colour distance. Example: tweed has high local variance, leather has low variance, rust is high (R−B)/sum.
