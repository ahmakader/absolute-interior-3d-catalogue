---
name: furniture-3d-catalogue
description: Turn furniture product photos (or ready-made 3D models) into an interactive 3D web catalogue - an open book where each piece rises out of the page, rotates freely and swaps materials live. Use when someone shares furniture or product images or GLB files and wants a 3D catalogue, 3D product viewer or material configurator.
---

# Furniture 3D Catalogue

Builds the "Absolute Interior" style catalogue: a three.js book (`index.html`) plus one compressed GLB per piece
(`models/<id>.glb`) and PBR texture sets (`tex/`). Live example and full source:
https://github.com/ahmakader/absolute-interior-3d-catalogue

This skill folder contains everything needed:
- `template/index.html` - the catalogue page. All content lives in the `PIECES` array near the top of the script.
- `tools/` - the asset pipeline (zones, clean borders, plinths, UVs, compression, procedural textures). See `tools/README.md`.

## 0. Check what you have before starting
- **Photos:** one clean image per piece, ideally on a plain background at a three-quarter angle.
- **3D models.** This skill does not invent geometry. Use the first route that is available:
  1. GLB files the user uploaded (made in Meshy, Tripo, Hunyuan3D, Rodin, or downloaded from a library) -> use them.
  2. An image-to-3D tool connected in this session (for example a Higgsfield `generate_3d` / Hunyuan3D connector) -> generate one GLB per photo.
  3. Neither -> stop and tell the user. Point them to the free/paid image-to-3D tools and free model libraries in the repo README. Never fake a model from primitives and present it as their product.
- **Per piece, ask for (or infer and confirm):** name, category, real size in cm (W x D x H), and the material zones the client should be able to change, e.g. sofa = fabric / plinth wood / pillows; chair = upholstery / frame / legs.
- Setup: `pip install -r tools/requirements.txt` and `cd tools && npm install`.

## 1. Image -> 3D (only if generating)
Save each result as `work/raw/<id>.glb`. Expect a heavy single mesh (about 500k triangles, tens of MB) with one baked texture.

## 2. Split into material zones (`tools/zones.py`, example in `tools/example_zones_per_piece.py`)
- Read each face's colour from the baked texture (`face_colors`).
- Classify faces into zones using **local contrast** (patterned fabric vs smooth leather), **chromaticity** ((R-B)/sum separates coloured fabric from shaded beige) and **height** (plinths, legs). Raw colour distance alone is fooled by baked shadows.
- Smooth labels (`smooth_labels`, `close_label`, `keep_largest`) and decimate to about 90k triangles (`decimate`).
- Cut clean borders along smooth curves: `tools/iso.py` -> `clean_cut(v, f, labels, n_zones)`.
- Rebuild simple parts the AI made lumpy as clean solids: plinths with `tools/plinth.py` (`outline` + `prism` + `hard_caps`), cylinders for swivel bases.
- **Render a colour-coded preview of every piece and look at it** before moving on. For uploaded models that already have separate parts, skip the classification and map their existing meshes/materials to zones.

## 3. UVs + export
`tools/build.py` -> `split_and_uv(...)` gives one mesh per zone (mesh/material name = zone key) with box-projected UVs in metres.
Scale each piece to the real size. Then `node tools/compress.mjs in.glb models/<id>.glb` (meshopt + quantisation, usually 0.5-0.9 MB per piece).

## 4. Materials
Generate texture sets with `python tools/textures.py <sets...>` (leather, wood, travertine, boucle, marble) or copy `tex/` from the repo.
Store normal maps as **JPEG 4:4:4 or PNG, never lossy WebP** - chroma subsampling corrupts them and the furniture looks speckled.

## 5. Build the catalogue
Copy `template/index.html` into the output folder next to `models/`, `tex/` and `img/` (the original photos).
Replace the `PIECES` array: `id, no, cat, title, dims, specs, model, img, zones[]`. Each zone has `key` (must equal the GLB mesh name), `label`, `def` and `opts` (material options: `{id, name, set, tint, tile, rough, ns, sheen, clear, metal}`; `tile` is in metres). Update the cover and contents text to the user's brand.

## 6. Verify (do not skip)
Serve the folder (`python3 -m http.server`). Open every spread, let each piece rise, rotate it, and click every swatch. Screenshot and look for speckles, seams, wrong zones or wrong scale. Fix the cause (labels, UV tile, normal strength) rather than hiding it.

## 7. Deliver
Give the user the folder as a ZIP and explain how to open it (local server) and publish it (GitHub: Add file -> Upload files, then Settings -> Pages -> Deploy from a branch -> main / root).

## Be honest about
- AI reconstructions guess the hidden sides of each piece.
- Real dimensions come from the user.
- Procedural textures stand in for real fabric scans; swap in the manufacturer's real materials when available.
