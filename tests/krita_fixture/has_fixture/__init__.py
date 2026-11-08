from krita import Extension,Krita
from PyQt5.QtCore import QTimer,QByteArray
from pathlib import Path
import json,traceback
class Fixture(Extension):
 def setup(self):pass
 def createActions(self,window):
  self.action=window.createAction('has_fixture_author','Author HAS fixture')
  self.action.triggered.connect(self.run);QTimer.singleShot(2000,self.action.trigger)
 def run(self):
  try:
   app=Krita.instance();self.doc=app.createDocument(256,144,'HAS original animation','RGBA','U8','',72);doc=self.doc
   app.activeWindow().addView(doc)
   for node in doc.rootNode().childNodes():node.remove()
   background=doc.createNode('Optional green background','paintlayer');doc.rootNode().addChildNode(background,None)
   background.setPixelData(QByteArray(bytes([0,255,0,255])*256*144),0,0,256,144);background.setVisible(False)
   ink=doc.createNode('Moving ink','paintlayer');doc.rootNode().addChildNode(ink,None);doc.setActiveNode(ink)
   assert doc.importAnimation([f'/fixture-input/frame{i:03d}.png' for i in range(40)],0,1)
   doc.setFramesPerSecond(24);doc.setFullClipRangeStartTime(0);doc.setFullClipRangeEndTime(39);doc.setCurrentTime(0);doc.refreshProjection();doc.waitForDone()
   assert doc.saveAs('/output/Original animation.kra');doc.waitForDone()
   Path('/output/fixture.json').write_text(json.dumps({'frames':40,'fps':24,'source':'Original animation.kra','nodes':[{'name':n.name(),'type':n.type(),'visible':n.visible(),'uuid':n.uniqueId().toString()} for n in doc.rootNode().childNodes()]},indent=2))
  except Exception:Path('/output/fixture-error.txt').write_text(traceback.format_exc())
  QTimer.singleShot(1000,lambda:Krita.instance().action('file_quit').trigger())
Krita.instance().addExtension(Fixture(Krita.instance()))
