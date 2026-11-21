var verifyFs=await import('node:fs/promises');var verifyCrypto=await import('node:crypto');var verifyPath=await import('node:path');
var verifyRoot='C:/a/Programming/cloudflare/has-body-addition-20261120';
var verifyRaw=await verifyFs.readFile("C:/a/Programming/cloudflare/has-body-addition-20261120/output/source-carrier-checkpoint-remote-expected.json");
if(verifyCrypto.createHash('sha256').update(verifyRaw).digest('hex')!=="a7751c9d728a10291129b297f4ddb563dde6df96260b21fb1e276f9534ffa15a")throw new Error('Expected inventory changed');
var verifyExpected=JSON.parse(verifyRaw);
if(verifyExpected.commit!=="ffed3fc2fe4f078a4c6cd506c5c757b7f46db82b"||verifyExpected.count!==529||verifyExpected.total_bytes!==13503036)throw new Error('Inventory schema changed');
var verifyInventory=verifyCrypto.createHash('sha256').update(JSON.stringify(verifyExpected.files.map(r=>[r.path,r.bytes,r.sha256,r.git_sha1]))).digest('hex');
if(verifyInventory!=="6070706cc3074bcfa78f8f06536e23958d2f61ec9f3077dbf9e3ba043bed2ba6")throw new Error('Remote inventory binding differs');
var verifyRows=[];var verifyTotal=0;
for(var row of verifyExpected.files){
 var file=verifyPath.resolve(verifyRoot,row.path);if(!file.startsWith(verifyPath.resolve(verifyRoot)+verifyPath.sep))throw new Error('Path escapes root');
 var before=await verifyFs.lstat(file,{bigint:true});if(!before.isFile()||before.isSymbolicLink()||before.nlink!==1n||before.size!==BigInt(row.bytes))throw new Error('File identity refused');
 var bytes=await verifyFs.readFile(file);var after=await verifyFs.lstat(file,{bigint:true});
 if(before.dev!==after.dev||before.ino!==after.ino||before.size!==after.size||before.mtimeNs!==after.mtimeNs||after.nlink!==1n)throw new Error('File changed');
 var sha256=verifyCrypto.createHash('sha256').update(bytes).digest('hex');
 var gitSha=verifyCrypto.createHash('sha1').update(Buffer.from('blob '+bytes.length+String.fromCharCode(0))).update(bytes).digest('hex');
 if(bytes.length!==row.bytes||sha256!==row.sha256||gitSha!==row.git_sha1)throw new Error('Independent local bytes differ: '+row.path);
 verifyRows.push({path:row.path,bytes:bytes.length,sha256,git_sha1:gitSha});verifyTotal+=bytes.length;
}
var verifyMain={"ref":"refs/heads/main","node_id":"REF_kwDOVjZV7a9yZWZzL2hlYWRzL21haW4","url":"https://api.github.com/repos/abanoy/studio-3d-2d/git/refs/heads/main","object":{"sha":"ffed3fc2fe4f078a4c6cd506c5c757b7f46db82b","type":"commit","url":"https://api.github.com/repos/abanoy/studio-3d-2d/git/commits/ffed3fc2fe4f078a4c6cd506c5c757b7f46db82b"}};if(verifyMain.object.sha!==verifyExpected.commit)throw new Error('Main reference differs');
var verifyReceipt={format:'has_source_carrier_checkpoint_independent_remote_readback_1',commit:verifyExpected.commit,parent:verifyExpected.parent,files:verifyRows.length,total_bytes:verifyTotal,remote_raw_SHA256_GitSHA1_length_all_exact:true,remote_path_blob_bindings_all_exact:true,independent_V8_hashes_and_golden_empty_check:true,independent_Node_crypto_local_raw_readback_all_exact:true,working_file_identities_stable_during_Node_read:true,main_ref_exact:true,inventory_sha256:verifyInventory,expected_file_sha256:"a7751c9d728a10291129b297f4ddb563dde6df96260b21fb1e276f9534ffa15a",routes:{"file_base64":528,"blob_utf8":1},entries:verifyRows};
var verifyReceiptRaw=Buffer.from(JSON.stringify(verifyReceipt,null,2)+'\n');await verifyFs.writeFile(verifyRoot+'/output/source-carrier-checkpoint-remote-receipt.json',verifyReceiptRaw,{flag:'wx'});await verifyFs.writeFile(verifyRoot+'/output/source-carrier-checkpoint-main-ref.json',JSON.stringify(verifyMain,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({commit:verifyReceipt.commit,files:verifyRows.length,total_bytes:verifyTotal,all_exact:true,receipt_bytes:verifyReceiptRaw.length,receipt_sha256:verifyCrypto.createHash('sha256').update(verifyReceiptRaw).digest('hex')}));
