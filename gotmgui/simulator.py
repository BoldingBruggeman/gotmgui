#!/usr/bin/python

#$Id: simulator.py,v 1.22 2009-10-14 09:22:51 jorn Exp $

from xmlstore.qt_compat import QtGui, QtCore, QtWidgets

import commonqt, core.common

# Here we can set the stack size for GOTM (in bytes). Note: bio modules sometimes
# need a very high stack size (in particular if Lagrangian variables are used)
stacksize = 16*1024*1024

class GOTMThread(QtCore.QThread):

  progressed = QtCore.Signal(float,float)

  def __init__(self, parent):
    QtCore.QThread.__init__(self,parent)
    self.setStackSize(stacksize)
    
    self.scenario = None
    self.rwlock = QtCore.QReadWriteLock()
    self.stopped = False
    self.result = 0
    self.stderr = ''
    self.stdout = ''
    
  def rungotm(self,scen):
    self.scenario = scen
    self.start(QtCore.QThread.LowPriority)
    
  def canContinue(self):
    self.rwlock.lockForRead()
    ret = not self.stopped
    self.rwlock.unlock()
    return ret
    
  def run(self):
    assert self.scenario is not None, 'No scenario specified.'
    try:
        import core.simulator
    except ImportError,e:
        import core.result
        self.res = core.result.Result()
        self.res.errormessage = str(e)
        self.res.returncode = 1
        raise
    self.res = core.simulator.simulate(self.scenario,continuecallback=self.canContinue,progresscallback=self.progressed.emit)
    
  def stop(self):
    self.rwlock.lockForWrite()
    self.stopped = True
    self.rwlock.unlock()
    #self.scenario.release()
    
class PageProgress(commonqt.WizardPage):
    def __init__(self, parent):
        commonqt.WizardPage.__init__(self, parent)
        
        self.scenario = parent.getProperty('scenario')
        assert self.scenario is not None, 'No scenario available.'

        oldresult = parent.getProperty('result')
        
        layout = QtWidgets.QVBoxLayout()

        # Add label that asks user to wait
        self.busylabel = QtWidgets.QLabel('Please wait while the simulation runs...',self)
        self.busylabel.setVisible(oldresult is None)
        layout.addWidget(self.busylabel)
        
        # Add progress bar
        self.bar = QtWidgets.QProgressBar(self)
        self.bar.setRange(0,1000)
        self.bar.setVisible(oldresult is None)
        layout.addWidget(self.bar)
        
        # Add label for time remaining.
        self.labelRemaining = QtWidgets.QLabel(self)
        self.labelRemaining.setVisible(oldresult is None)
        layout.addWidget(self.labelRemaining)

        # Add (initially hidden) label for result.
        self.resultlabel = QtWidgets.QLabel('The simulation is complete.',self)
        self.resultlabel.setVisible(oldresult is not None)
        layout.addWidget(self.resultlabel)

        # Add (initially hidden) show/hide output button.
        self.showhidebutton = QtWidgets.QPushButton('Show diagnostic output',self)
        self.showhidebutton.setSizePolicy(QtWidgets.QSizePolicy.Fixed,QtWidgets.QSizePolicy.Fixed)
        self.showhidebutton.setVisible(oldresult is not None)
        layout.addWidget(self.showhidebutton)
        self.showhidebutton.clicked.connect(self.onShowHideOutput)

        # Add (initially hidden) text box for GOTM output.
        self.text = QtWidgets.QTextEdit(self)
        self.text.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        self.text.setReadOnly(True)
        font = QtGui.QFont('Courier')
        font.setStyleHint(QtGui.QFont.TypeWriter)
        self.text.setFont(font)
        if oldresult is not None: self.text.setPlainText(oldresult.stderr)
        self.text.hide()
        layout.addWidget(self.text)
        layout.setStretchFactor(self.text,1)

        # Add (initially hidden) save-output button.
        self.savebutton = QtWidgets.QPushButton('Save output to file',self)
        self.savebutton.setSizePolicy(QtWidgets.QSizePolicy.Fixed,QtWidgets.QSizePolicy.Fixed)
        self.savebutton.hide()
        layout.addWidget(self.savebutton)
        self.savebutton.clicked.connect(self.onSaveOutput)

        layout.addStretch()
        
        self.setLayout(layout)
        
        # Initialize GOTM run variables.
        self.gotmthread = None
        self.tempdir = None
        self.bar.setValue(0)
       
    def showEvent(self,event):
        if self.owner.getProperty('result') is None: self.startRun()

    def startRun(self):
        self.gotmthread = GOTMThread(self)
        self.gotmthread.progressed.connect(self.progressed)
        self.gotmthread.finished.connect(self.done)
        self.gotmthread.rungotm(self.scenario)
        
    def progressed(self,progress,remaining):
        self.bar.setValue(int(round(self.bar.maximum()*progress)))
        remaining = round(remaining)
        if remaining<60:
            self.labelRemaining.setText('%i seconds remaining' % remaining)
        else:
            self.labelRemaining.setText('%i minutes %i seconds remaining' % divmod(remaining,60))
            
    def done(self):
        res = self.gotmthread.res
        if core.common.verbose: print 'GOTM thread shut-down; return code = %i' % res.returncode

        layout = self.layout()

        # Hide progress bar and remaining time.
        self.busylabel.hide()
        self.bar.hide()
        self.labelRemaining.hide()

        # Show label for result; change text if not successfull.
        if res.returncode==1:
            self.resultlabel.setText('The simulation failed: %s' % res.errormessage)
        elif res.returncode==2:
            self.resultlabel.setText('The simulation was cancelled')
        self.resultlabel.show()

        if res.returncode!=1:
            self.showhidebutton.show()
        else:
            self.text.show()
            self.savebutton.show()

        # Set text with GOTM output
        if res.stderr is not None: self.text.setPlainText(res.stderr)
        
        # Save result object
        if res.returncode==0:
            self.owner.setProperty('result',res)
            self.completeStateChanged()
        else:
            res.release()
        
    def isComplete(self):
        return (self.owner.getProperty('result') is not None)
    
    def saveData(self,mustbevalid):
        # Stop worker thread
        if self.gotmthread is not None:
            self.gotmthread.progressed.disconnect(self.progressed)
            self.gotmthread.finished.disconnect(self.done)
            self.gotmthread.stop()
            if not self.gotmthread.isFinished(): self.gotmthread.wait()
            self.gotmthread = None
            
        if not mustbevalid:
            # Remove any currently stored result.
            self.owner.setProperty('result',None)

        return True

    def onShowHideOutput(self):
        makevisible = self.text.isHidden()
        self.text.setVisible(makevisible)
        self.savebutton.setVisible(makevisible)
        curtext = unicode(self.showhidebutton.text())
        if makevisible:
            self.showhidebutton.setText(curtext.replace('Show','Hide'))
        else:
            self.showhidebutton.setText(curtext.replace('Hide','Show'))

    def onSaveOutput(self):
        path,selectedFilter = map(unicode,QtWidgets.QFileDialog.getSaveFileNameAndFilter(self,'','','Text files (*.txt);;All files (*.*)'))
        if path=='': return
        f = open(path,'w')
        f.write(self.text.toPlainText())
        f.close()
