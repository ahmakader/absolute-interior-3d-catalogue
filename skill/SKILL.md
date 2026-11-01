---
name: furniture-3d-catalogue
description: Turn ordinary furniture product photos into an interactive 3D web catalogue (an open book where each piece rises out of the page, rotates freely and swaps materials live). Use when someone uploads furniture/product images and wants a 3D catalogue, 3D product viewer, or material configurator built from them.
---

# Furniture 3D Catalogue

Turns product photos into the "Absolute Interior" style catalogue in this repository:
`index.html` (three.js book) + `models/*.glb` + `tex/` texture sets.

## What you need
- The user's product photos: one clean image per piece, ideally on a plain background.
- **An image-to-3D tool.** This repo does not include one. Use whatever is connected or installed:
  a Higgsfield `generate_3d` (Hunyuan3D) connector, Meshy, Rodin, Tripo, or a local Hunyuan3D-2 / TRELLIS install.
  If none is available, say so and stop. Don't invent models.
- Python 3 (`pip install -r tools/requirements.txt`) and Node (`cd tools && npm install`).

## Steps

1. **Collect the pieces.** For each photo, ask for (or infer and confirm) the name, category, real dimensions,
   and the **material zones** the client should be able to change, for example
   sofa = fabric / plinth wood / pillows; chair = upholstery / frame / base.

2. **Image → 3D.** Generate one GLB per photo with the image-to-3D tool. Save it as `work/raw/<id>.glb`.
   Expect a heavy single mesh (around 500k triangles, tens of MB) with one baked texture.

3. **Split into material zones** (`tools/zones.py`, see `tools/example_zones_per_piece.py`):
   - Read each face's colour from the baked texture (`face_colors`).
   - Classify the faces into zones. Use **local contrast** (patterned fabric versus smooth leather),
     **chromaticity** ((R−B)/sum separates coloured fabric from shaded beige) and **height** (plinths, legs).
     Raw colour distance alone gets fooled by baked shadows.
   - Smooth the labels (`smooth_labels`, `close_label`, `keep_largest`) and decimate to about 90k triangles (`decimate`).
   - Cut clean borders along smooth curves: `tools/iso.py` → `clean_cut(v, f, labels, n_zones)`.
   - Rebuild simple parts as clean solids where the AI mesh is lumpy: plinths with `tools/plinth.py`
     (`outline` + `prism` + `hard_caps`), cylinders for swivel bases.
   - **Render a colour-coded preview of every piece and look at it** before moving on.

4. **UVs + export.** Use `tools/build.py` → `split_and_uv(...)` for one mesh per zone (mesh/material name = zone key)
   with box-projected UVs in metres. Then `node tools/compress.mjs in.glb models/<id>.glb`
   (meshopt plus quantisation; usually 0.5–0.9 MB per piece).

5. **Materials.** Reuse the sets in `tex/` or generate new ones with `tools/textures.py`.
   Store normal maps as **JPEG 4:4:4 or PNG, never lossy WebP**, because chroma subsampling corrupts them.

6. **Catalogue data.** Edit the `PIECES` array in `index.html`: id, title, dimensions, specs, `model`,
   `img` (the original photo) and `zones` with their material options.
   Zone keys must match the mesh names in the GLB.

7. **Verify.** Serve the folder (`python3 -m http.server`). Then open every spread, pop each piece,
   rotate it, and click every swatch. Screenshot them and look for speckles, seams or wrong zones.
   Fix the cause in the data (labels, UV tile, normal strength) rather than hiding it.

8. **Publish.** Push to GitHub and enable Pages (Settings → Pages → main / root).

## Be honest about
- The 3D models are AI reconstructions of the photo, so hidden sides are guessed.
- Real dimensions come from the user. Scale each model to them.
- Procedural textures stand in for real fabric scans. Swap in the manufacturer's real materials when available.
