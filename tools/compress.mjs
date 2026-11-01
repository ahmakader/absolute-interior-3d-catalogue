import {NodeIO} from '@gltf-transform/core';
import {ALL_EXTENSIONS} from '@gltf-transform/extensions';
import {weld, quantize, meshopt, prune, dedup} from '@gltf-transform/functions';
import {MeshoptEncoder, MeshoptDecoder} from 'meshoptimizer';
await MeshoptEncoder.ready; await MeshoptDecoder.ready;
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({'meshopt.encoder':MeshoptEncoder,'meshopt.decoder':MeshoptDecoder});
{const [inp,out]=process.argv.slice(2);
  const doc=await io.read(inp);
  await doc.transform(prune({keepAttributes:true}),weld({tolerance:1e-5}),quantize({exclude:/^TEXCOORD/,quantizePosition:14,quantizeNormal:10}),meshopt({encoder:MeshoptEncoder,level:'high'}));
  await io.write(out,doc);const n=out;
  const root=doc.getRoot();
  console.log(n,'meshes',root.listMeshes().map(m=>m.getName()+':'+m.listPrimitives().reduce((a,p)=>a+p.getIndices().getCount()/3,0)).join(','));
}
