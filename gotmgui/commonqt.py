#!/usr/bin/python

#$Id: commonqt.py,v 1.69 2011-02-12 14:58:31 jorn Exp $

# Import modules from standard Python (>= 2.4) library
import re, os.path

# Import third-party modules
from xmlstore.qt_compat import QtGui, QtCore, QtWidgets

# Import our own custom modules
import xmlstore.util
import core.common

radiowidth = None
def getRadioWidth():
    """Get the width of a radio button without text.
    Used to left align object below radio buttons to the position of the
    text associated with the radio button.
    """
    global radiowidth
    if radiowidth is None:
        radiowidth = QtWidgets.qApp.style().pixelMetric(QtWidgets.QStyle.PM_ExclusiveIndicatorWidth)
    return radiowidth
    
def getIcon(name):
    path = os.path.join(core.common.getDataRoot(),'icons',name)
    return QtGui.QIcon(path)
        
# =======================================================================
# Function for showing a Qt-based file/directory browse dialog
# =======================================================================

def browseForPath(parent=None,curpath=None,getdirectory=False,save=False,filter='',dlgoptions=None):
    """Shows browse dialog for opening/saving a file, or selecting a directory.
    Supports automatic append of file extension based on chosen file type.
    """
    if curpath is None: curpath=''
    if dlgoptions is None: dlgoptions = QtWidgets.QFileDialog.Option()
    if getdirectory:
        path = unicode(QtWidgets.QFileDialog.getExistingDirectory(parent,'',curpath))
    elif save:
        path,selfilt = map(unicode,QtWidgets.QFileDialog.getSaveFileNameAndFilter(parent,'',curpath,filter,None,dlgoptions))
    else:
        path,selfilt = map(unicode,QtWidgets.QFileDialog.getOpenFileNameAndFilter(parent,'',curpath,filter))
        
    # If the browse dialog was cancelled, just return.
    if path=='': return None

    # if we are saving, make sure that the extension matches the filter selected.
    if save:
        re_ext = re.compile('\*\.(.+?)[\s)]')
        exts = []
        pos = 0
        match = re_ext.search(selfilt,pos)
        goodextension = False
        while match is not None:
            ext = match.group(1)
            if ext!='*':
                exts.append(ext)
                if path.endswith(ext): goodextension = True
            pos = match.end(0)
            match = re_ext.search(selfilt,pos)

        # Append first imposed extension
        if not goodextension and len(exts)>0: path += '.'+exts[0]
    
    return os.path.normpath(path)

# =======================================================================
# PathEditor: a Qt widget for editing paths, combines line-edit widget
# for path name, and a browse button.
# =======================================================================

class PathEditor(QtWidgets.QWidget):
    onChanged = QtCore.Signal()
    editingFinished = QtCore.Signal()

    def __init__(self,parent=None,compact=False,header=None,getdirectory=False,save=False,mrupaths=[]):
        QtWidgets.QWidget.__init__(self, parent)

        if compact:
            text = '...'
        else:
            text = 'Browse...'

        lo = QtWidgets.QHBoxLayout()

        if header is not None:
            self.header = QtWidgets.QLabel(header,self)
            lo.addWidget(self.header)

        if len(mrupaths)>0:
            # One or more recently used paths: use a combobox for the path.
            self.editor = QtWidgets.QComboBox(self)
            lo.addWidget(self.editor)
            self.editor.setEditable(True)
            self.editor.setSizePolicy(QtWidgets.QSizePolicy.Expanding,QtWidgets.QSizePolicy.Fixed)
            for p in mrupaths: self.editor.addItem(p)
            self.editor.setEditText('')
            self.defaultpath = os.path.dirname(mrupaths[0])
            self.lineedit = self.editor.lineEdit()
        else:
            # No recently used paths: use a line edit control for the path.
            self.lineedit = QtWidgets.QLineEdit(self)
            lo.addWidget(self.lineedit)
            self.defaultpath = None

        self.browsebutton = QtWidgets.QPushButton(text,self)
        lo.addWidget(self.browsebutton)
        lo.setContentsMargins(0,0,0,0)

        self.setLayout(lo)

        self.lineedit.textChanged.connect(self.onChanged)
        self.lineedit.editingFinished.connect(self.editingFinished)
        self.browsebutton.clicked.connect(self.onBrowse)

        self.getdirectory = getdirectory
        self.save = save

        self.filter=''

        self.dlgoptions = QtWidgets.QFileDialog.DontConfirmOverwrite

    def setPath(self,path):
        return self.lineedit.setText(path)
        #return self.editor.setEditText(path)

    def path(self):
        return unicode(self.lineedit.text())
        #return unicode(self.editor.currentText())

    @QtCore.Slot()
    def onBrowse(self):
        curpath = self.path()
        if curpath=='' and self.defaultpath != None: curpath=self.defaultpath
        path = browseForPath(self,curpath=curpath,getdirectory=self.getdirectory,save=self.save,filter=self.filter,dlgoptions=self.dlgoptions)
        if path is not None: self.setPath(path)

    def hasPath(self):
        return (len(self.path())>0)

    #def onChanged(self,text):
    #    self.onChanged.emit()

    #def onEditingFinished(self):
    #    self.editingFinished.emit()

# =======================================================================
# Wizard: dialog for hosting series of 'wizard' pages
#   based on Qt example of a complex wizard
#   pages must inherit from class WizardPage below.
# =======================================================================

class Wizard(QtWidgets.QDialog):
    
    def __init__(self,parent=None,sequence=None,closebutton=False,headerlogo=None,allowfinish=False):
        QtWidgets.QDialog.__init__(self, parent, QtCore.Qt.Window|QtCore.Qt.WindowContextHelpButtonHint|QtCore.Qt.WindowMinMaxButtonsHint)

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        
        if headerlogo is not None:
            self.pm = QtGui.QPixmap(headerlogo,'PNG')
            self.piclabel = QtWidgets.QLabel(self)
            self.piclabel.setPixmap(self.pm)
            #self.piclabel.setScaledContents(True)
            self.piclabel.setMinimumWidth(20)
            layout.addWidget(self.piclabel)

        self.bnlayout = QtWidgets.QHBoxLayout()
        self.bnlayout.addStretch()

        self.bnHome = QtWidgets.QPushButton(getIcon('gohome.png'),'&Home',self)
        self.bnHome.clicked.connect(self.onHome)
        self.bnlayout.addWidget(self.bnHome)

        self.bnBack = QtWidgets.QPushButton(getIcon('back.png'),'&Back',self)
        self.bnBack.clicked.connect(self.onBack)
        self.bnlayout.addWidget(self.bnBack)

        self.bnNext = QtWidgets.QPushButton(getIcon('next.png'),'&Next',self)
        self.bnNext.clicked.connect(self.onNext)
        self.bnlayout.addWidget(self.bnNext)

        if closebutton:
            import xmlplot.gui_qt4
            self.bnClose = QtWidgets.QPushButton(xmlplot.gui_qt4.getIcon('exit.png'),'&Close',self)
            self.bnClose.clicked.connect(self.accept)
            self.bnlayout.addWidget(self.bnClose)

        self.bnlayout.setContentsMargins(11,11,11,11)
        layout.addLayout(self.bnlayout)

        self.setLayout(layout)

        self.shared = {}

        self.settings = None

        self.sequence = sequence
        self.currentpage = None
        
        self.allowfinish = allowfinish
        
        self.busy = False

    def getSettings(self):
        if self.settings is None:
            import core.settings
            self.settings = core.settings.SettingsStore()
            try:
                self.settings.load()
            except core.settings.LoadException,e:
                QtWidgets.QMessageBox.warning(self, 'Unable to load settings', str(e))
        return self.settings

    def getProperty(self,propertyname):
        if propertyname not in self.shared: return None
        return self.shared[propertyname]

    def setProperty(self,propertyname,value):
        if propertyname in self.shared and isinstance(self.shared[propertyname],xmlstore.util.referencedobject):
            self.shared[propertyname].release()
        self.shared[propertyname] = value
        self.onPropertyChange(propertyname)
        
    def onPropertyChange(self,propertyname):
        pass
        
    def clearProperties(self):
        for propertyname in self.shared.keys():
            self.setProperty(propertyname,None)

    def destroy(self, destroyWindow = True, destroySubWindows = True):
        if self.settings is not None:
            self.settings.save()
            self.settings.release()
            self.settings = None
        for v in self.shared.values():
            try:
                v.release()
            except:
                pass
        if self.currentpage is not None:
            self.currentpage.destroy()
        QtWidgets.QDialog.destroy(self,destroyWindow,destroySubWindows)

    def setSequence(self,sequence):
        self.sequence = sequence
        cls = self.sequence.getNextPage()
        self.switchPage(cls(self))

    @QtCore.Slot()
    def onNext(self,askoldpage=True):
        if self.busy: return
        self.busy = True
        cancelled = False
        if askoldpage:
            cancelled = not self.currentpage.saveData(mustbevalid=True)
        if not cancelled:
            ready = False
            while not ready:
                cls = self.sequence.getNextPage()
                if self.allowfinish and cls is None:
                    self.close()
                    return
                assert cls is not None, 'No next page available to show; the next button should have been disabled.'
                newpage = cls(self)
                ready = (not newpage.doNotShow())
            self.switchPage(newpage)
        self.busy = False

    @QtCore.Slot()
    def onBack(self):
        if self.busy: return
        self.busy = True
        if self.currentpage.saveData(mustbevalid=False):
            ready = False
            while not ready:
                cls = self.sequence.getPreviousPage()
                assert cls is not None, 'No previous page available to show; the back button should have been disabled.'
                newpage = cls(self)
                ready = (not newpage.doNotShow())
            self.switchPage(newpage)
        self.busy = False

    @QtCore.Slot()
    def onHome(self):
        if self.busy: return
        self.busy = True
        if self.currentpage.saveData(mustbevalid=False):
            cls = self.sequence.getPreviousPage()
            assert cls is not None, 'No previous page available to show; the home button should have been disabled.'
            while cls is not None:
                prevcls = cls
                cls = self.sequence.getPreviousPage()
            newpage = prevcls(self)
            self.switchPage(newpage)
        self.busy = False

    def switchPage(self,newpage):
        QtWidgets.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))
        layout = self.layout()
        if self.currentpage is not None:
            self.currentpage.hide()
            layout.removeWidget(self.currentpage)
            self.currentpage.onCompleteStateChanged.disconnect(self.onCompleteStateChanged)
            self.currentpage.destroy()
        self.currentpage = newpage
        layout.insertWidget(1,self.currentpage)
        self.currentpage.show()
        self.currentpage.onCompleteStateChanged.connect(self.onCompleteStateChanged)
        cangoback = (self.sequence.getPreviousPage(stay=True) is not None)
        self.bnHome.setEnabled(cangoback)
        self.bnBack.setEnabled(cangoback)
        self.onCompleteStateChanged()
        QtWidgets.QApplication.restoreOverrideCursor()

    def onCompleteStateChanged(self):
        curpage = self.currentpage
        enable = curpage.isComplete() and (self.allowfinish or self.sequence.getNextPage(stay=True) is not None)
        self.bnNext.setEnabled(enable)

# =======================================================================
# WizardPage: single page for the above Wizard class
#   based on Qt example of a complex wizard
# =======================================================================

class WizardPage(QtWidgets.QWidget):
    onCompleteStateChanged = QtCore.Signal()

    def __init__(self,parent=None):
        QtWidgets.QWidget.__init__(self,parent)
        self.owner = parent
        self.hide()

    def isComplete(self):
        return False

    def completeStateChanged(self):
        self.onCompleteStateChanged.emit()

    def saveData(self,mustbevalid):
        return True

    def doNotShow(self):
        return False

    def createHeader(self,title,description):
        label = QtWidgets.QLabel('<span style="font-size:large;font-weight:bold;">%s</span><hr>%s' % (title,description),self)
        label.setWordWrap(True)
        return label
        
    def destroy(self,destroyWindow = True,destroySubWindows = True):
        QtWidgets.QWidget.destroy(self,destroyWindow,destroySubWindows)

class WizardDummyPage(WizardPage):
    def doNotShow(self):
        return True

class WizardSequence(object):

    def __init__(self,items=[]):
        self.items = items
        self.index = -1

    def getCurrentPage(self):
        if self.index==-1: return None
        cur = self.items[self.index]
        if isinstance(cur,WizardSequence):
            return cur.getCurrentPage()
        else:
            return cur

    def getNextPage(self,stay=False):
        if self.index==-1:
            if len(self.items)==0: raise Exception('WizardSequence contains no items')
        elif isinstance(self.items[self.index],WizardSequence):
            new = self.items[self.index].getNextPage(stay=stay)
            if new is not None:
                return new
            elif not stay:
                self.items[self.index].reset()
        if self.index>=(len(self.items)-1): return None
        ind = self.index + 1
        if not stay: self.index = ind
        new = self.items[ind]
        if isinstance(new,WizardSequence):
            return new.getNextPage(stay=stay)
        else:
            return new

    def getPreviousPage(self,stay=False):
        if self.index==-1:
            if len(self.items)==0: raise Exception('WizardSequence contains no items')
        elif isinstance(self.items[self.index],WizardSequence):
            new = self.items[self.index].getPreviousPage(stay=stay)
            if new is not None:
                return new
            elif not stay:
                self.items[self.index].reset()
        if self.index==0: return None
        
        if self.index==-1:
            ind = len(self.items)-1
        else:
            ind = self.index - 1
        if not stay: self.index = ind
        new = self.items[ind]
        if isinstance(new,WizardSequence):
            return new.getPreviousPage(stay=stay)
        else:
            return new
        
    def reset(self):
        self.index = -1

class WizardFork(WizardSequence):
    def __init__(self,wiz):
        WizardSequence.__init__(self,[])
        self.wizard = wiz

    def getNextPage(self,stay=False):
        if self.index==-1:
            seq = self.getSequence()
            assert seq is not None, 'Fork did not return a new sequence'
            if stay: return seq.getNextPage(stay=stay)
            self.items = [seq]
        return WizardSequence.getNextPage(self,stay=stay)

    def getSequence(self):
        return None
        
# =======================================================================
# ProgressDialog: generic progress dialog that receives progress messages
# via a callback with 2 arguments: (1) progress as float between 0 and 1,
# (2) a string describing the task currently being performed.
# =======================================================================

class ProgressDialog(QtWidgets.QProgressDialog):
    def __init__(self,parent=None,minimumduration=500,title=None,suppressstatus=False):
        QtWidgets.QProgressDialog.__init__(self,'',None,0,0,parent,QtCore.Qt.Dialog|QtCore.Qt.CustomizeWindowHint|QtCore.Qt.WindowTitleHint|QtCore.Qt.MSWindowsFixedSizeDialogHint)
        self.setModal(True)
        self.setMinimumDuration(minimumduration)
        self.setRange(0,0)
        self.suppressstatus = suppressstatus
        if title is not None: self.setWindowTitle(title)
        QtWidgets.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))
            
    def onProgressed(self,progress,status):
        if progress is not None:
            if self.maximum()==0: self.setMaximum(100)
            self.setValue(int(100*progress))
        elif progressdialog.maximum()!=0:
            self.setValue(0)
        if not self.suppressstatus: self.setLabelText(status)
        QtWidgets.qApp.processEvents()

    def close(self):
        QtWidgets.QApplication.restoreOverrideCursor()
        QtWidgets.QProgressDialog.close(self)
        