extends RefCounted
# Wait for persistence rather than assuming a fixed number of render frames.
# Controlled preview-gate tests opt out so they can inspect an in-flight writer.
static func checkpoint(app,include_preview:=true) -> void:
 # Guard assertions must stay immediate when a gesture prevented any work.
 if not app.recovery_writer.busy() and not (include_preview and app.recovery_preview.busy()):return
 var idle:=0
 while idle<2:
  app.poll_recovery_preview()
  if app.recovery_writer.busy() or include_preview and app.recovery_preview.busy():idle=0
  else:
   # A normal schedule tick deferred behind a preview is retried with the same
   # ordinary guards/thresholds, never forced through a gesture or disabled mode.
   if include_preview:app.autosave_tick()
   idle=0 if app.recovery_writer.busy() or include_preview and app.recovery_preview.busy() else idle+1
  await app.get_tree().process_frame
