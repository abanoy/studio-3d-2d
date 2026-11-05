"use strict";
window.HASFiles = {
  pick(title,accept,directory,callback) {
    window.HAS_LAST_PICK={active:navigator.userActivation.isActive,at:performance.now()};
    const input=document.createElement("input");input.type="file";input.accept=accept;
    input.setAttribute("aria-label",title);input.style.display="none";document.body.append(input);
    let done=false;
    const finish=(path,error)=>{if(done)return;done=true;input.remove();callback(path,error);};
    input.addEventListener("cancel",()=>finish("",""),{once:true});
    input.addEventListener("change",async()=>{
      try {
        if(!input.files || input.files.length!==1){finish("","");return;}
        const file=input.files[0],extension=file.name.split(".").pop().toLowerCase();
        if(!["has","glb","wav"].includes(extension) || !accept.split(",").includes("."+extension))throw new Error("Choose a supported file for this action.");
        if(file.size>134217728 || extension==="wav" && file.size>33554432)throw new Error("File exceeds this browser preview's size limit.");
        const forbidden=["/",String.fromCharCode(92),":","<",">",String.fromCharCode(34),"|","?","*"];
        const safe=Array.from(file.name,c=>c.charCodeAt(0)<32||forbidden.includes(c)?"_":c).join("").slice(-100);
        const path=directory+"/"+safe;
        window.HASEngine.copyToFS(path,await file.arrayBuffer());
        finish(path,"");
      } catch(error) {finish("",String(error.message||error));}
    },{once:true});
    input.click();
  }
};
