var fsFollow = await import('node:fs/promises');
var cryptoFollow = await import('node:crypto');
var pathFollow = await import('node:path');
var followRoot = 'C:/a/Programming/cloudflare/has-body-addition-20261120';
var followExpectedPath = followRoot + '/output/source-carrier-followup-checkpoint-remote-expected.json';
var followBytes = await fsFollow.readFile(followExpectedPath);
if(cryptoFollow.createHash('sha256').update(followBytes).digest('hex') !== 'b14aeae0b1e6c9175e8e11e82d2a707c3a1c3c796f23e1fa779ce530250bce38') throw Error('Expected digest differs');
var followExpected = JSON.parse(followBytes);
if(followExpected.commit !== '165ebdfb3361e982666aa7355a432ba625f8d96a' || followExpected.count !== 943) throw Error('Inventory revision differs');
var followLocalProofs = [];
for(var followRow of followExpected.files) {
  var followPath = pathFollow.resolve(followRoot,followRow.path);
  if(!followPath.startsWith(pathFollow.resolve(followRoot)+pathFollow.sep)) throw Error('Path escaped workspace');
  var followBefore = await fsFollow.lstat(followPath,{bigint:true});
  if(!followBefore.isFile() || followBefore.nlink !== 1n) throw Error('Nonregular file');
  var followPayload = await fsFollow.readFile(followPath);
  var followAfter = await fsFollow.lstat(followPath,{bigint:true});
  if(followBefore.ino!==followAfter.ino || followBefore.size!==followAfter.size || followBefore.mtimeNs!==followAfter.mtimeNs) throw Error('Changed during read');
  var followSHA256 = cryptoFollow.createHash('sha256').update(followPayload).digest('hex');
  var followGit = cryptoFollow.createHash('sha1').update(Buffer.from('blob '+followPayload.length+String.fromCharCode(0))).update(followPayload).digest('hex');
  if(followPayload.length!==followRow.bytes || followSHA256!==followRow.sha256 || followGit!==followRow.git_sha1) throw Error('Local payload differs '+followRow.path);
  followLocalProofs.push({...followRow,remote_committed_path_and_blob_verified:true,remote_blob_raw_SHA256_verified:true});
}
var followReceipt = {format:'has_source_carrier_followup_remote_exact_readback_1',commit:followExpected.commit,parent:followExpected.parent,remote_main_commit:followExpected.commit,
  expected_file_sha256:'b14aeae0b1e6c9175e8e11e82d2a707c3a1c3c796f23e1fa779ce530250bce38',
  files:followLocalProofs,count:943,total_bytes:19584654,unique_remote_blobs:383,unique_remote_blob_bytes:8165601,
  all_943_committed_remote_paths_mode_blob_sha_and_size_matched:true,all_unique_remote_blob_raw_bytes_sha256_git_sha1_matched:true,
  verification_method:'Independent GitHub immutable tree path/size/Git-SHA binding for all943 paths; full content SHA256 and Git-SHA1 readback of all383 unique blobs; same blob reused only after exact per-path binding.',
  remote_tree_ids:{followup:'840883f261c4177b36cec04b2e742d2119205907',control:'43b30f81cac9535c122d65a3b05bc1be15def087'},
  independent_node_crypto_local_inventory_verified:true,private_model_or_capture_bytes_uploaded:false,cleanup_authorized_by_this_receipt:false};
var followReceiptRaw = Buffer.from(JSON.stringify(followReceipt,null,2)+'\n');
await fsFollow.writeFile(followRoot+'/output/source-carrier-followup-checkpoint-remote-receipt.json',followReceiptRaw,{flag:'wx'});
nodeRepl.write(JSON.stringify({commit:followReceipt.commit,count:followReceipt.count,receipt_bytes:followReceiptRaw.length,receipt_sha256:cryptoFollow.createHash('sha256').update(followReceiptRaw).digest('hex')}));
