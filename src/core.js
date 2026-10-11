// Pure image/layout and ZIP utilities. No dependencies or network access.
export function safeName(value, fallback = 'product') {
  return String(value).normalize('NFKC').replace(/[\\/:*?"<>|\x00-\x1f]/g, '-').replace(/\.{2,}/g, '-').replace(/-+/g, '-').replace(/^[. -]+|[. -]+$/g, '').trim().slice(0, 80) || fallback;
}
export function contain(bounds, width, height, margin) {
  const scale = Math.min(width * (1 - margin * 2) / bounds.width, height * (1 - margin * 2) / bounds.height);
  return {x:(width - bounds.width * scale)/2,y:(height - bounds.height * scale)/2,width:bounds.width*scale,height:bounds.height*scale};
}
export function alphaBounds(data, width, height) {
  let left=width,top=height,right=-1,bottom=-1;
  for(let y=0;y<height;y++) for(let x=0;x<width;x++) if(data[(y*width+x)*4+3]>16) {left=Math.min(left,x);top=Math.min(top,y);right=Math.max(right,x);bottom=Math.max(bottom,y);}
  return right<0 ? null : {x:left,y:top,width:right-left+1,height:bottom-top+1};
}
// Only remove colors connected to the outer edge. Internal matching colors survive.
export function removeBackdrop(data,width,height,tolerance=24) {
  const out = new Uint8ClampedArray(data), seen=new Uint8Array(width*height), queue=new Int32Array(width*height);
  const corners=[0,width-1,(height-1)*width,width*height-1].map(i=>Array.from(data.slice(i*4,i*4+3)));
  const color=[0,1,2].map(c=>corners.map(p=>p[c]).sort((a,b)=>a-b).slice(1,3).reduce((a,b)=>a+b)/2);
  const matches=i=>data[i*4+3]===0 || Math.sqrt([0,1,2].reduce((s,c)=>s+(data[i*4+c]-color[c])**2,0))<=tolerance;
  let head=0,tail=0;
  const add=i=>{if(!seen[i]) {seen[i]=1;if(matches(i))queue[tail++]=i;}};
  for(let x=0;x<width;x++){add(x);add((height-1)*width+x);}for(let y=0;y<height;y++){add(y*width);add(y*width+width-1);}
  while(head<tail){const i=queue[head++];out[i*4+3]=0;const x=i%width,y=Math.floor(i/width);if(x)add(i-1);if(x<width-1)add(i+1);if(y)add(i-width);if(y<height-1)add(i+width);}
  return {data:out, removed:tail/(width*height), uneven:corners.some(p=>Math.sqrt(p.reduce((s,v,c)=>s+(v-color[c])**2,0))>tolerance)};
}
const crcTable=Uint32Array.from({length:256},(_,n)=>{for(let k=0;k<8;k++)n=(n&1)?0xedb88320^(n>>>1):n>>>1;return n>>>0;});
export function crc32(bytes){let c=0xffffffff;for(const b of bytes)c=crcTable[(c^b)&255]^(c>>>8);return(c^0xffffffff)>>>0;}
export function zipStore(files) {
  const chunks=[],central=[];let offset=0;
  function header(size){const a=new Uint8Array(size);return[a,new DataView(a.buffer)];}
  for(const file of files){const name=new TextEncoder().encode(file.name),data=file.data,crc=crc32(data);const[h,v]=header(30);v.setUint32(0,0x04034b50,true);v.setUint16(4,20,true);v.setUint16(6,0x800,true);v.setUint16(12,33,true);v.setUint32(14,crc,true);v.setUint32(18,data.length,true);v.setUint32(22,data.length,true);v.setUint16(26,name.length,true);chunks.push(h,name,data);const[c,d]=header(46);d.setUint32(0,0x02014b50,true);d.setUint16(4,20,true);d.setUint16(6,20,true);d.setUint16(8,0x800,true);d.setUint16(14,33,true);d.setUint32(16,crc,true);d.setUint32(20,data.length,true);d.setUint32(24,data.length,true);d.setUint16(28,name.length,true);d.setUint32(42,offset,true);central.push(c,name);offset+=30+name.length+data.length;}
  const centralSize=central.reduce((s,c)=>s+c.length,0),[end,e]=header(22);e.setUint32(0,0x06054b50,true);e.setUint16(8,files.length,true);e.setUint16(10,files.length,true);e.setUint32(12,centralSize,true);e.setUint32(16,offset,true);return new Blob([...chunks,...central,end],{type:'application/zip'});
}
