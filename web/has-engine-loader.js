"use strict";
// HAS adaptation: assemble the unchanged pinned engine from size-bounded same-origin files.
window.HASLoadEngine = async function(basePath) {
  const root = new URL(basePath, document.baseURI);
  const get = async name => { const r=await fetch(new URL(name,root)); if(!r.ok) throw new Error("Engine download failed: "+r.status); return r; };
  const manifest=await (await get("engine-chunks.json")).json();
  if(manifest.format!=="has_web_engine_chunks_1" || manifest.parts.length!==3 || manifest.bytes!==37686550) throw new Error("Unexpected engine manifest");
  const sha=async bytes=>Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256",bytes)),x=>x.toString(16).padStart(2,"0")).join("");
  const all=new Uint8Array(manifest.bytes);let offset=0;
  for(let i=0;i<manifest.parts.length;i++) {
    const part=manifest.parts[i];
    if(part.path!=="index.wasm.part"+i || part.bytes<=0 || part.bytes>16777216 || offset+part.bytes>all.length) throw new Error("Invalid engine part");
    const bytes=new Uint8Array(await (await get(part.path)).arrayBuffer());
    if(bytes.length!==part.bytes || await sha(bytes)!==part.sha256) throw new Error("Engine part checksum failed");
    all.set(bytes,offset);offset+=bytes.length;
  }
  if(offset!==all.length || await sha(all)!==manifest.sha256) throw new Error("Engine checksum failed");
  window.HAS_ENGINE_VERIFIED={bytes:offset,sha256:manifest.sha256};
  return new Response(all,{headers:{"Content-Type":"application/wasm"}});
};
