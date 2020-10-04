#!/usr/bin/python

#$Id: visualizer.py,v 1.45 2010-07-19 13:45:50 jorn Exp $

from xmlstore.qt_compat import QtGui, QtCore, QtWidgets, qt4_backend, qt4_backend_version

import xmlstore.gui_qt4
from .core import common, result, report
from . import commonqt

import sys,datetime
import xml.sax
import os.path

def loadResult(path):
    res = result.Result()

    try:
        if path.endswith('.gotmresult'):
            res.load(path)
        elif path.endswith('.nc'):
            res.attach(path,copy=False)
        else:
            # We do not recognize this file type; try both GOTM result and NetCDF
            done = True
            try:
                res.attach(path,copy=False)
            except Exception as e:
                done = False
            if not done:
                done = True
                try:
                    res.load(path)
                except Exception as e:
                    done = False
            if (not done):
                raise Exception('The file "%s" is not a GOTM result or a NetCDF file.' % path)
    except:
        res.release()
        res = None
        raise

    return res

class OpenWidget(QtWidgets.QWidget):

    onCompleteStateChanged = QtCore.Signal()
    
    def __init__(self,parent=None,mrupaths=[]):
        QtWidgets.QWidget.__init__(self,parent)

        self.pathOpen = commonqt.PathEditor(self,header='File to open: ',mrupaths=mrupaths)
        self.pathOpen.filter = 'GOTM result files (*.gotmresult);;NetCDF files (*.nc);;All files (*.*)'

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.pathOpen)
        layout.setContentsMargins(0,0,0,0)
        self.setLayout(layout)
        self.pathOpen.onChanged.connect(self.completeStateChanged)
        
    def setPath(self,path):
        self.pathOpen.setPath(path)
        
    def completeStateChanged(self):
        self.onCompleteStateChanged.emit()

    def isComplete(self):
        return self.pathOpen.hasPath()

    def getResult(self):
        return loadResult(self.pathOpen.path())

class PageOpen(commonqt.WizardPage):

    def __init__(self,parent=None):
        commonqt.WizardPage.__init__(self, parent)

        self.label = QtWidgets.QLabel('Specify the location of the result you want to view.',self)
        self.openwidget = OpenWidget(self)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.openwidget)
        layout.addStretch()
        self.setLayout(layout)
        self.openwidget.onCompleteStateChanged.connect(self.completeStateChanged)

    def isComplete(self):
        return self.openwidget.isComplete()

    def saveData(self,mustbevalid):
        if not mustbevalid: return True
        try:
            res = self.openwidget.getResult()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, 'Unable to load result', str(e), QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.NoButton)
            return False
        self.owner.setProperty('result',res)
        self.owner.setProperty('scenario',res.scenario.addref())
        return True

class VisualizeWidget(QtWidgets.QWidget):
    def __init__(self,result,parent=None):
        QtWidgets.QWidget.__init__(self,parent)

        self.varpath = None
        self.varname = None
        self.result = result

        self.treestore = self.result.getVariableTree(plottableonly=True)
        self.model = xmlstore.gui_qt4.TypedStoreModel(self.treestore,nohide=False,novalues=True)

        self.treeVariables = xmlstore.gui_qt4.ExtendedTreeView(self)
        self.treeVariables.header().hide()
        self.treeVariables.setSizePolicy(QtWidgets.QSizePolicy.Minimum,QtWidgets.QSizePolicy.Expanding)
        self.treeVariables.setMaximumWidth(250)
        self.treeVariables.setModel(self.model)
        self.treeVariables.selectionModel().selectionChanged.connect(self.OnVarSelected)

        import xmlplot.gui_qt4
        self.figurepanel = xmlplot.gui_qt4.FigurePanel(self,reportnodata=False)

        self.label = QtWidgets.QLabel('Here you can view the results of the simulation. Please choose a variable to be plotted from the menu.',self)

        layout = QtWidgets.QGridLayout()
        layout.addWidget(self.label,0,0,1,2)
        layout.addWidget(self.treeVariables,1,0)
        layout.addWidget(self.figurepanel,1,1)
        self.setLayout(layout)

        self.figurepanel.figure.addDataSource('result',self.result)

    def saveFigureSettings(self):
        if self.varpath is not None and self.figurepanel.figure.hasChanged():
            self.result.setFigure('result/'+self.varpath,self.figurepanel.figure.properties)

    def OnVarSelected(self,*args):
        selected = self.treeVariables.selectionModel().selectedIndexes()
        if len(selected)==0: return
        node = selected[0].internalPointer()
        if node.hasChildren(): return

        # Show wait cursor
        QtWidgets.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))

        try:
            # Save settings for currently shown figure
            self.saveFigureSettings()

            # Get name and path of variable about to be shown.
            self.varname = node.getId()
            self.varpath = '/'.join(node.location)

            # Disable figure updating while we make changes.
            self.figurepanel.figure.setUpdating(False)

            # Plot; first try stored figures, otherwise plot anew.
            props = self.figurepanel.figure.properties
            if not self.result.getFigure('result/'+self.varpath,props):
                self.figurepanel.plot('result[\'%s\']' % self.varname,'result')

            # Re-enable figure updating (this will force a redraw because things changed)
            self.figurepanel.figure.setUpdating(True)
        finally:
            # Restore original cursor
            QtWidgets.QApplication.restoreOverrideCursor()

    def destroy(self,destroyWindow = True,destroySubWindows = True):
        self.figurepanel.destroy()
        self.figurepanel = None
        self.treestore.release()
        self.treestore = None

class PageVisualize(commonqt.WizardPage):
    
    def __init__(self,parent=None):
        commonqt.WizardPage.__init__(self, parent)
        
        self.result = parent.getProperty('result')
        self.vizwidget = VisualizeWidget(self.result,parent=self)
        
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(self.vizwidget)
        self.setLayout(layout)

    def isComplete(self):
        return True

    def saveData(self,mustbevalid):
        self.vizwidget.saveFigureSettings()
        return True
            
    def onSaveAsDefault(self):
        pass

    def destroy(self,destroyWindow = True,destroySubWindows = True):
        self.vizwidget.destroy()
        commonqt.WizardPage.destroy(self,destroyWindow,destroySubWindows)

class ConfigureReportWidget(QtWidgets.QWidget):
    onCompleteStateChanged = QtCore.Signal()
    onReportProgressed = QtCore.Signal(float,str)

    def __init__(self,parent,result,rep):
        QtWidgets.QWidget.__init__(self,parent)
        
        self.result = result
        self.report = rep

        self.factory = xmlstore.gui_qt4.PropertyEditorFactory(self.report.store)

        reportname2path = report.Report.getTemplates()

        self.labTemplates = QtWidgets.QLabel('Report template:',self)
        self.comboTemplates = QtWidgets.QComboBox(parent)
        for (name,path) in reportname2path.items():
            self.comboTemplates.addItem(name,path)
        
        self.labOutput = QtWidgets.QLabel('Directory to save to:',self)
        self.pathOutput = commonqt.PathEditor(self,getdirectory=True)
        
        # Default report directory: result or scenario directory
        if self.result.path is not None:
            self.pathOutput.defaultpath = os.path.dirname(self.result.path)
        elif self.result.scenario is not None and self.result.scenario.path is not None:
            self.pathOutput.defaultpath = os.path.dirname(self.result.scenario.path)

        self.labVariables = QtWidgets.QLabel('Included variables:',self)
        self.treestore = self.result.getVariableTree(plottableonly=True)
        
        # Prepare selection based on report settings
        selroot = self.report.store['Figures/Selection']
        for node in selroot.children:
            targetnode = self.treestore[node.getValue()]
            if targetnode is not None: targetnode.setValue(True)
        
        self.model = xmlstore.gui_qt4.TypedStoreModel(self.treestore,nohide=False,novalues=True,checkboxes=True)
        self.treeVariables = xmlstore.gui_qt4.ExtendedTreeView(self)
        self.treeVariables.header().hide()
        self.treeVariables.setModel(self.model)
        self.treeVariables.setSizePolicy(QtWidgets.QSizePolicy.Expanding,QtWidgets.QSizePolicy.Expanding)

        # Create labels+editors for figure settings
        editWidth = self.factory.createEditor('Figures/Width',self)
        editHeight = self.factory.createEditor('Figures/Height',self)
        editDpi = self.factory.createEditor('Figures/Resolution',self)
        editFontScaling = self.factory.createEditor('Figures/FontScaling',self)
        
        layout = QtWidgets.QGridLayout()
        layout.addWidget(self.labOutput,     0,0)
        layout.addWidget(self.pathOutput,    0,1)
        layout.addWidget(self.labTemplates,  1,0)
        layout.addWidget(self.comboTemplates,1,1)
        layout.addWidget(self.labVariables,  2,0,QtCore.Qt.AlignTop)
        layout.addWidget(self.treeVariables, 2,1)

        self.figbox = QtWidgets.QGroupBox('Figure settings',self)
        figlayout = QtWidgets.QGridLayout()
        editWidth.addToGridLayout(figlayout,0,0)
        editHeight.addToGridLayout(figlayout)
        editDpi.addToGridLayout(figlayout)
        editFontScaling.addToGridLayout(figlayout)
        figlayout.setColumnStretch(3,1)
        self.figbox.setLayout(figlayout)
        layout.addWidget(self.figbox,3,0,1,2)
        
        layout.setContentsMargins(0,0,0,0)
        self.setLayout(layout)

        self.pathOutput.onChanged.connect(self.completeStateChanged)

    def completeStateChanged(self):
        self.onCompleteStateChanged.emit()

    def isComplete(self):
        return self.pathOutput.hasPath()

    def generate(self):
        # Get path of target directory and template.
        templateindex = self.comboTemplates.currentIndex()
        templatepath = u''.__class__(self.comboTemplates.itemData(templateindex))
        outputpath = self.pathOutput.path()

        # Warn if the target directory is not empty.
        if os.path.isdir(outputpath) and len(os.listdir(outputpath))>0:
            ret = QtWidgets.QMessageBox.warning(self,'Directory is not empty','The specified target directory ("%s") contains one or more files, which may be overwritten. Do you want to continue?' % outputpath,QtWidgets.QMessageBox.Yes,QtWidgets.QMessageBox.No)
            if ret==QtWidgets.QMessageBox.No: return False

        # Update the list of selected variables.
        selroot = self.report.store['Figures/Selection']
        selroot.removeAllChildren()
        for node in self.model.getCheckedNodes():
            if node.canHaveValue():
                ch = selroot.addChild('VariablePath')
                ch.setValue('/'.join(node.location))

        # Make changed report settings persistent
        self.factory.updateStore()

        # Generate the report and display the wait cursor while doing so.
        QtWidgets.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))
        try:
            self.report.generate(self.result,outputpath,templatepath,callback=self.onReportProgressed.emit)
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()

        return True

    def destroy(self,destroyWindow = True,destroySubWindows = True):
        self.factory.unlink()
        self.treeVariables.setModel(None)
        self.model.unlink()
        self.treestore.release()
        QtWidgets.QWidget.destroy(self,destroyWindow,destroySubWindows)
        
class PageReportGenerator(commonqt.WizardPage):
    def __init__(self,parent=None):
        commonqt.WizardPage.__init__(self, parent)

        self.result = parent.getProperty('result')
        
        import xmlplot.gui_qt4
        deffont = xmlplot.gui_qt4.getFontSubstitute(u''.__class__(self.fontInfo().family()))
        self.report = report.Report(defaultfont = deffont)
        
        # Copy report settings from result.
        self.report.store.root.copyFrom(self.result.store['ReportSettings'],replace=True)

        self.label = QtWidgets.QLabel('You can generate a report that describes the scenario and the simulation results. A report consists of an HTML file, associated files (CSS, javascript) and image files for all figures.',self)
        self.label.setWordWrap(True)
        self.checkReport = QtWidgets.QCheckBox('Yes, I want to generate a report.', parent)
        self.reportwidget = ConfigureReportWidget(self,self.result,self.report)

        self.progressbar = QtWidgets.QProgressBar(self)
        self.progressbar.setRange(0,100)
        self.labStatus = QtWidgets.QLabel(self)
        self.progressbar.hide()
        self.labStatus.hide()

        layout = QtWidgets.QGridLayout()
        layout.addWidget(self.label,0,0,1,2)
        layout.addWidget(self.checkReport,1,0,1,2)
        layout.addWidget(self.reportwidget,2,1,1,1)

        layout.addWidget(self.progressbar,3,0,1,2)
        layout.addWidget(self.labStatus,4,0,1,2)

        layout.setRowStretch(5,1)
        layout.setColumnStretch(1,1)
        layout.setColumnMinimumWidth(0,commonqt.getRadioWidth())

        self.setLayout(layout)

        self.checkReport.stateChanged.connect(self.onCheckChange)
        self.reportwidget.onCompleteStateChanged.connect(self.completeStateChanged)
        self.reportwidget.onReportProgressed.connect(self.reportProgressed)
        self.onCheckChange()

    def onCheckChange(self):
        self.reportwidget.setVisible(self.checkReport.isChecked())
        self.completeStateChanged()

    def isComplete(self):
        if not self.checkReport.isChecked(): return True
        return self.reportwidget.isComplete()

    def saveData(self,mustbevalid):
        if mustbevalid and self.checkReport.isChecked():
            ret = self.reportwidget.generate()
            if ret:
                self.result.store['ReportSettings'].copyFrom(self.report.store.root,replace=True)
            return ret
        return True

    def reportProgressed(self,progressed,status):
        if self.progressbar.isHidden():
            self.label.setText('Please wait while the report is created...')
            self.checkReport.hide()
            self.reportwidget.hide()
            self.progressbar.show()
            self.labStatus.show()
            self.repaint()
            
        self.progressbar.setValue(round(progressed*100))
        self.labStatus.setText(status)
        QtWidgets.qApp.processEvents()

    def destroy(self,destroyWindow = True,destroySubWindows = True):
        self.report.release()
        self.reportwidget.destroy(destroyWindow,destroySubWindows)
        commonqt.WizardPage.destroy(self,destroyWindow,destroySubWindows)

class PageSave(commonqt.WizardPage):

    def __init__(self,parent=None):
        commonqt.WizardPage.__init__(self, parent)

        self.result = parent.getProperty('result')

        self.label = QtWidgets.QLabel('Do you want to save the result of your simulation?',self)
        self.bngroup     = QtWidgets.QButtonGroup()
        self.radioNoSave = QtWidgets.QRadioButton('No, I do not want to save the result.', parent)
        self.radioSave   = QtWidgets.QRadioButton('Yes, I want to save the result to file.', parent)

        self.pathSave = commonqt.PathEditor(self,header='File to save to: ',save=True)
        self.pathSave.filter = 'GOTM result files (*.gotmresult);;All files (*.*)'
        if self.result.path is not None: self.pathSave.setPath(self.result.path)

        self.checkboxAddFigures = QtWidgets.QCheckBox('Also save my figure settings.',self)
        self.checkboxAddFigures.setChecked(True)

        self.bngroup.addButton(self.radioNoSave, 0)
        self.bngroup.addButton(self.radioSave,   1)

        layout = QtWidgets.QGridLayout()
        layout.addWidget(self.label,      0,0,1,2)
        layout.addWidget(self.radioNoSave,1,0,1,2)
        layout.addWidget(self.radioSave,  2,0,1,2)
        layout.addWidget(self.pathSave,   3,1,1,1)
        layout.addWidget(self.checkboxAddFigures,4,1,1,1)

        layout.setRowStretch(5,1)
        layout.setColumnStretch(1,1)
        layout.setColumnMinimumWidth(0,commonqt.getRadioWidth())

        self.setLayout(layout)

        self.bngroup.buttonClicked.connect(self.onSourceChange)
        self.pathSave.onChanged.connect(self.completeStateChanged)

        self.radioSave.setChecked(True)
        self.onSourceChange()

    def onSourceChange(self):
        checkedid = self.bngroup.checkedId()
        self.pathSave.setVisible(checkedid==1)
        self.checkboxAddFigures.setVisible(checkedid==1)
        self.completeStateChanged()

    def isComplete(self):
        checkedid = self.bngroup.checkedId()
        if   checkedid==0:
            return True
        elif checkedid==1:
            return self.pathSave.hasPath()

    def saveData(self,mustbevalid):
        if not mustbevalid: return True
        checkedid = self.bngroup.checkedId()
        if checkedid==1:
            targetpath = self.pathSave.path()
            if os.path.isfile(targetpath):
                ret = QtWidgets.QMessageBox.warning(self, 'Overwrite existing file?', 'There already exists a file at the specified location. Overwrite it?', QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
                if ret==QtWidgets.QMessageBox.No:
                    return False
            dialog = commonqt.ProgressDialog(self,title='Saving...',suppressstatus=True)
            try:
                try:
                    self.result.save(targetpath,addfiguresettings=self.checkboxAddFigures.isChecked(),callback=dialog.onProgressed)
                finally:
                    dialog.close()
                self.owner.settings.addUniqueValue('Paths/RecentResults','Path',targetpath)
            except Exception as e:
                print(e)
                QtWidgets.QMessageBox.critical(self, 'Unable to save result', str(e), QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.NoButton)
                return False
        return True

    def doNotShow(self):
        return (not self.result.hasChanged())

class PageFinal(commonqt.WizardPage):
    
    def __init__(self,parent=None):
        commonqt.WizardPage.__init__(self, parent)

        self.label = QtWidgets.QLabel('You are now done. Click the "Home" button below to work with another scenario or result.',self)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.label)
        layout.addStretch()
        self.setLayout(layout)

    def isComplete(self):
        return True

def visualizeResult(result):
    # Create the application and enter the main message loop.
    createQApp = QtWidgets.QApplication.startingUp()
    if createQApp:
        app = QtWidgets.QApplication([' '])
    else:
        app = QtWidgets.qApp

    dialog = QtWidgets.QDialog()

    visualizer = VisualizeWidget(result,parent=dialog)

    pm = QtGui.QPixmap(os.path.join(common.getDataRoot(),'logo.png'),'PNG')
    piclabel = QtWidgets.QLabel(dialog)
    piclabel.setPixmap(pm)
    piclabel.setMinimumWidth(20)

    layout = QtWidgets.QVBoxLayout()
    layout.addWidget(piclabel)
    layout.addWidget(visualizer)
    layout.setSpacing(0)
    layout.setContentsMargins(0,0,0,0)
    dialog.setLayout(layout)

    dialog.setWindowTitle('Visualize results')
    dialog.show()
    
    ret = app.exec_()

def main():
    # Debug info
    print('Python version: '+str(sys.version_info))
    print('%s version: %s' % (qt4_backend,qt4_backend_version))
    print('Qt version: '+QtCore.qVersion())
    print('xml version: '+xml.__version__)

    # Create the application and enter the main message loop.
    createQApp = QtWidgets.QApplication.startingUp()
    if createQApp:
        app = QtWidgets.QApplication([' '])
    else:
        app = QtWidgets.qApp

    # Create wizard dialog
    wiz = commonqt.Wizard()
    wiz.setWindowTitle('Result visualizer')
    wiz.resize(800, 600)

    seq = [PageOpen,PageChooseAction,PageVisualize,PageReportGenerator,PageSave,PageFinal]

    # Get NetCDF file to open from command line or from FileOpen dialog.
    if len(sys.argv)>1:
        res = None
        try:
            res = loadResult(sys.argv[1])
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, 'Unable to load result', repr(e), QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.NoButton)
        if res is not None:
            seq.pop(0)
            wiz.setProperty('result',res)
            wiz.setProperty('scenario',res.scenario.addref())

    seq = commonqt.WizardSequence(seq)
    wiz.setSequence(seq)
    wiz.show()

    ret = app.exec_()
    page = None

    wiz.unlink()

    sys.exit(ret)

# If the script has been run (as opposed to imported), enter the main loop.
if (__name__=='__main__'): main()
