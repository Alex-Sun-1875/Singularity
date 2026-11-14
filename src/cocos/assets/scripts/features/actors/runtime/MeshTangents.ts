import {BufferGeometry,Float32BufferAttribute} from 'three';

type Geometry={positions:number[];normals?:number[];uvs?:number[];indices?:number[];tangents?:number[]};

/** Adapt Cocos geometry to Three.js's maintained tangent calculation. */
export function withTangents<T extends Geometry>(geometry:T):T {
 if(geometry.tangents?.length||!geometry.normals||!geometry.uvs)return geometry;
 const buffer=new BufferGeometry();
 try{
  buffer.setAttribute('position',new Float32BufferAttribute(geometry.positions,3));
  buffer.setAttribute('normal',new Float32BufferAttribute(geometry.normals,3));
  buffer.setAttribute('uv',new Float32BufferAttribute(geometry.uvs,2));
  buffer.setIndex(geometry.indices??Array.from({length:geometry.positions.length/3},(_,i)=>i));
  buffer.computeTangents();
  geometry.tangents=Array.from(buffer.getAttribute('tangent').array);
  return geometry;
 }finally{buffer.dispose();}
}
