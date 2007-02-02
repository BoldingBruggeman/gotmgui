#!/usr/bin/python

#$Id: simulator.py,v 1.7 2007-02-02 11:20:45 jorn Exp $

from PyQt4 import QtGui,QtCore
import common,commonqt
import os, tempfile, sys, math, shutil
import gotm

gotmversion = gotm.gui_util.getversion().rstrip()
gotmscenarioversion = 'gotm-%s' % gotmversion
print 'GOTM library reports version %s; will use scenario template %s.xml.' % (gotmversion,gotmscenarioversion)

# Here we can set the stack size for GOTM (in bytes). Note: bio modules sometimes
# need a very high stack size (in particular if Lagrangian variables are used)
stacksize = 16000000

class GOTMThread(QtCore.QThread):

  def __init__(self, parent, scenariodir, receiver):
    QtCore.QThread.__init__(self,parent)
    self.setStackSize(stacksize)
    
    self.scenariodir = scenariodir
    self.receiver = receiver
    self.rwlock = QtCore.QReadWriteLock()
    self.stopped = False
    self.result = 0
    self.stderr = ''
    self.stdout = ''
    
  def rungotm(self):
    self.start(QtCore.QThread.LowPriority)
    
  def run(self):
    # Result can be 0 (success), 1 (error occurred), or 2 (cancelled)
    self.result = 0
      
    # Save old working directory
    olddir = os.getcwdu()
    
    # Change to directory with GOTM scenario (catch exceptions that can occur,
    # for instance, if the specified directory does not exist).
    try:
        os.chdir(self.scenariodir)
    except Exception,e:
        self.error = 'Failed to enter scenario directory "%s". %s' % (self.scenariodir,str(e))
        self.result = 1
        os.chdir(olddir)
        return
    
    # Redirect FORTRAN output to (temporary) files.
    (h,outfile) = tempfile.mkstemp('.txt','gotm')
    os.close(h)
    (h,errfile) = tempfile.mkstemp('.txt','gotm')
    os.close(h)
    gotm.gui_util.redirectoutput(outfile,errfile)
    
    # Initialize GOTM
    try:
        gotm.gotm.init_gotm()
    except Exception,e:
        self.error = 'Exception thrown while initializing GOTM: %s' % str(e)
        self.result = 1
        
    # Only enter the time loop if we succeeded so far.
    if self.result==0:
        # Calculate the size of time batches (small enough to respond rapidly to requests
        # for cancellation, and to show sufficiently detailed progress - e.g. in % -
        # but not so small that GUI slows down due to the avalanche of progress notifications)
        visualres = 0.01

        # Get # of first step, last step, number of steps for whole GOTM run.
        start = gotm.time.minn*1    # Multiply by 1 to ensure we have the integer value, not a reference to the attribute
        stop  = gotm.time.maxn*1    # Multiply by 1 to ensure we have the integer value, not a reference to the attribute
        stepcount = stop-start+1

        minslicesize = 1
        maxslicesize = int(round(stepcount/20.))
        if maxslicesize<minslicesize: maxslicesize = minslicesize
        
        timer = QtCore.QTime()

        islicestart = start
        islicesize = 100
        
        timer.start()
        while islicestart<=stop:
            # Check if we have to cancel
            rl = QtCore.QReadLocker(self.rwlock)
            if self.stopped:
                print 'GOTM run was cancelled; exiting thread...'
                self.result = 2
                break
            rl.unlock()
            
            # Configure GOTM for new slice.
            gotm.time.minn = islicestart
            islicestop = islicestart + islicesize - 1
            if islicestop>stop: islicestop = stop
            gotm.time.maxn = islicestop
            
            # Process time batch
            try:
                gotm.gotm.time_loop()
            except Exception,e:
                self.error = 'Exception thrown in GOTM time loop: %s' % str(e)
                self.result = 1
                break

            # Send 'progress' event
            prog = (islicestop-start+1)/float(stepcount)
            self.emit(QtCore.SIGNAL("progressed(double)"), prog)

            # Adjust slice size
            elapsed = timer.restart()
            if elapsed==0:
                islicesize = maxslicesize
            else:
                islicesize = int(round(islicesize * 400./elapsed))
                if islicesize<minslicesize: islicesize = minslicesize
                if islicesize>maxslicesize: islicesize = maxslicesize

            islicestart = islicestop + 1
            
    # GOTM clean-up
    try:
        gotm.gotm.clean_up()
    except Exception,e:
        self.error = 'Exception thrown during GOTM clean-up: '+str(e)
        if self.result==0: self.result = 1
        
    # Reset FORTRAN output
    gotm.gui_util.resetoutput()
    
    # Read GOTM output from temporary files, then delete these files.
    f = open(errfile,'r')
    self.stderr = f.read()
    f.close()
    os.remove(errfile)
    f = open(outfile,'r')
    self.stdout = f.read()
    f.close()
    os.remove(outfile)
    
    # Return to previous working directory.
    os.chdir(olddir)
    
  def stop(self):
    wl = QtCore.QWriteLocker(self.rwlock)
    self.stopped = True
    
class PageProgress(commonqt.WizardPage):
    def __init__(self, parent):
        commonqt.WizardPage.__init__(self, parent)
        self.scenario = parent.shared['scenario']
        layout = QtGui.QVBoxLayout()

        self.busylabel = QtGui.QLabel('Please wait while the simulation runs...',self)
        layout.addWidget(self.busylabel)
        
        # Progress bar
        self.bar = QtGui.QProgressBar(self)
        self.bar.setRange(0,1000)
        layout.addWidget(self.bar)
        
        # Add label for time remaining.
        self.labelRemaining = QtGui.QLabel(self)
        layout.addWidget(self.labelRemaining)

        # Add (initially hidden) label for result.
        self.resultlabel = QtGui.QLabel('',self)
        self.resultlabel.hide()
        layout.addWidget(self.resultlabel)

        # Add (initially hidden) show/hide output button.
        self.showhidebutton = QtGui.QPushButton('Show diagnostic output',self)
        self.showhidebutton.setSizePolicy(QtGui.QSizePolicy.Fixed,QtGui.QSizePolicy.Fixed)
        self.showhidebutton.hide()
        layout.addWidget(self.showhidebutton)
        self.connect(self.showhidebutton, QtCore.SIGNAL('clicked()'),self.onShowHideOutput)

        # Add (initially hidden) text box for GOTM output.
        self.text = QtGui.QTextEdit(self)
        self.text.setLineWrapMode(QtGui.QTextEdit.NoWrap)
        self.text.setReadOnly(True)
        self.text.hide()
        layout.addWidget(self.text)
        layout.setStretchFactor(self.text,1)

        # Add (initially hidden) save-output button.
        self.savebutton = QtGui.QPushButton('Save output to file',self)
        self.savebutton.setSizePolicy(QtGui.QSizePolicy.Fixed,QtGui.QSizePolicy.Fixed)
        self.savebutton.hide()
        layout.addWidget(self.savebutton)
        self.connect(self.savebutton, QtCore.SIGNAL('clicked()'),self.onSaveOutput)

        layout.addStretch()
        
        self.setLayout(layout)
        
        # Initialize GOTM run variables.
        self.gotmthread = None
        self.runcount = 1
        self.bar.setValue(0)
        self.result = None
        
    def showEvent(self,event):
        self.startRun()

    def startRun(self):
        namelistscenario = self.scenario.convert(gotmscenarioversion,targetownstemp=False)
        self.tempdir = tempfile.mkdtemp('','gotm-')
        namelistscenario.setProperty(['gotmrun','output','out_fmt'],2)
        namelistscenario.setProperty(['gotmrun','output','out_dir'],'.')
        namelistscenario.setProperty(['gotmrun','output','out_fn'],'result')
        namelistscenario.writeAsNamelists(self.tempdir)
        namelistscenario.unlink()
        self.timer = QtCore.QTime()
        self.timer.start()
        self.gotmthread = GOTMThread(self,self.tempdir,self)
        self.connect(self.gotmthread, QtCore.SIGNAL('progressed(double)'), self.progressed, QtCore.Qt.QueuedConnection)
        self.connect(self.gotmthread, QtCore.SIGNAL('finished()'), self.done, QtCore.Qt.QueuedConnection)
        self.gotmthread.rungotm()
        
    def progressed(self,progress):
        self.bar.setValue(int(round(self.bar.maximum()*progress)))
        remaining = (1-progress)*self.timer.elapsed()/1000/progress
        if remaining<60:
            self.labelRemaining.setText('%i seconds remaining' % round(remaining))
        else:
            self.labelRemaining.setText('%i minutes %i seconds remaining' % (math.floor(remaining/60),round(remaining % 60)))
            
    def done(self):
        result = self.gotmthread.result
        print 'GOTM thread shut-down; return code = %s' % str(result)

        layout = self.layout()

        # Hide progress bar and remaining time.
        self.busylabel.hide()
        self.bar.hide()
        self.labelRemaining.hide()

        # Add label for result.
        if result==0:
            self.resultlabel.setText('The simulation is complete.')
        elif result==1:
            self.resultlabel.setText('The simulation failed:')
        elif result==2:
            self.resultlabel.setText('The simulation was cancelled')
        self.resultlabel.show()

        if result!=1:
            self.showhidebutton.show()
        else:
            self.text.show()
            self.savebutton.show()

        # Set text with GOTM output (append error message if an error occurred)
        restext = ''
        if result==1:
            restext += 'Error: %s\n' % self.gotmthread.error
        elif result==2:
            restext += 'GOTM run was cancelled.\n\n'
        if len(self.gotmthread.stderr)>0: restext += 'GOTM output:\n%s' % self.gotmthread.stderr
        self.text.setPlainText(restext)
        
        # Create result object
        if result==0:
            self.result = common.Result()
            respath = os.path.join(self.tempdir,'result.nc')
            self.result.tempdir = self.tempdir
            self.tempdir = None
            self.result.attach(respath,self.scenario,copy=False)
            self.result.changed = True
            self.completeStateChanged()
            
        # For debugging purposes only: start GOTM again.
        self.runcount -= 1
        if self.runcount>0: self.startGotm(self.scendir)
        
    def isComplete(self):
        return (self.result!=None)
    
    def saveData(self,mustbevalid):
        # Stop worker thread
        if self.gotmthread!=None:
            self.gotmthread.stop()
            if not self.gotmthread.isFinished(): self.gotmthread.wait()
        # Store result (if needed and available)
        if (mustbevalid and self.result!=None):
            self.parent().shared['result'] = self.result
        # Remove temporary directory
        if self.tempdir!=None:
            try:
                shutil.rmtree(self.tempdir)
            except Exception,e:
                print 'Unable to completely remove GOTM temporary directory "'+self.tempdir+'".\nError: '+str(e)
            self.tempdir = None
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
        path = unicode(QtGui.QFileDialog.getSaveFileName(self,'','','Text files (*.txt);;All files (*.*)'))
        if path=='': return
        f = open(path,'w')
        f.write(self.text.toPlainText())
        f.close()
