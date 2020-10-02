import tempfile,os,time

from . import common, result
import pygotm

gotmversion = pygotm.get_version()
if gotmversion.startswith('v'): gotmversion = gotmversion[1:]
gotmscenarioversion = list(map(int, gotmversion.split(' ')[0].split('-')[0].split('.')))
if gotmscenarioversion[0] >= 5:
    gotmscenarioversion = gotmscenarioversion[:2]
gotmscenarioversion = 'gotm-%s' % '.'.join(map(str, gotmscenarioversion))

verbose = False

clock = getattr(time, 'perf_counter', None)
if clock is None:
    clock = time.clock

class Simulator(object):
    def __init__(self,scenario,redirect=True):
        self.scenario = scenario
        self.redirect = redirect
        self.outfile = None
        self.errfile = None
        self.olddir = None
        
        # Create result object.
        if verbose:
            print('creating result')
        self.result = result.Result()

        try:
            self.initialize()
        except Exception as e:
            raise
            self.result.errormessage = str(e)
            self.result.returncode = 1
    
    def initialize(self):
        if verbose:
            print('initializing simulation')
        
        namelistscenario = self.scenario.convert(gotmscenarioversion)
        if verbose:
            print('scenario converted')
        self.simulationdir = common.TempDirManager.create('gotm-')
        namelistscenario['gotmrun/output/out_fmt'].setValue(2)
        namelistscenario['gotmrun/output/out_dir'].setValue('.')
        namelistscenario['gotmrun/output/out_fn' ].setValue('result')
        namelistscenario.writeAsNamelists(self.simulationdir)
        namelistscenario.release()
                    
        # Save old working directory
        self.olddir = getattr(os, 'getcwdu', os.getcwd)()

        if verbose:
            print('switch working directory')

        # Change to directory with GOTM scenario (catch exceptions that can occur,
        # for instance, if the specified directory does not exist).
        try:
            os.chdir(self.simulationdir)
        except Exception as e:
            os.chdir(self.olddir)
            raise Exception('Failed to enter temporary simulation directory "%s". %s' % (self.simulationdir,e))

        # Redirect FORTRAN output to (temporary) files.
        if self.redirect:
            (h,self.outfile) = tempfile.mkstemp('.txt','gotm')
            os.close(h)
            (h,self.errfile) = tempfile.mkstemp('.txt','gotm')
            os.close(h)
            pygotm.redirect_output(self.outfile,self.errfile)

        if verbose:
            print('initializing gotm module')

        # Initialize GOTM
        try:
            pygotm.initialize()
        except Exception as e:
            os.chdir(self.olddir)
            raise Exception('Exception thrown while initializing GOTM: %s' % str(e))

        # Get # of first step, last step, number of steps for whole GOTM run.
        self.start,self.stop = pygotm.get_time_bounds()
        self.stepcount = self.stop-self.start+1
        
        self.currentpos = self.start

    def finalize(self):
        # GOTM clean-up
        try:
            pygotm.finalize()
        except Exception as e:
            self.result.errormessage = 'Error during GOTM clean-up: %s' % e
            if self.result.returncode==0: self.result.returncode = 1
            
        if self.redirect:
            # Reset FORTRAN output
            pygotm.reset_output()

            def readoutput(path):
                f = open(path,'r')
                data = f.read()
                f.close()
                os.remove(path)
                return data
                
            # Read GOTM output from temporary files, then delete these files.
            if self.errfile is not None: self.result.stderr = readoutput(self.errfile)
            if self.outfile is not None: self.result.stdout = readoutput(self.outfile)

        # Return to previous working directory.
        if self.olddir is not None: os.chdir(self.olddir)

        if self.result.returncode==0:    
            # Succeeded: get the result. Note: the result "inherits" the temporary directory,
            # so we do not have to delete it here.
            respath = os.path.join(self.simulationdir,'result.nc')
            self.result.tempdir = self.simulationdir
            self.result.attach(respath,self.scenario,copy=False)
            self.result.changed = True
        else:
            # Failed: delete temporary simulation directory
            try:
                common.TempDirManager.delete(self.simulationdir)
            except Exception as e:
                print('Unable to completely remove GOTM temporary directory "%s".\nError: %s' % (self.simulationdir,e))
                
        return self.result
    
    def run(self,progresscallback=None,continuecallback=None):
        assert self.result.returncode==0, 'Run did not initialize successfully. %s' % self.result.errormessage
        
        # Calculate the size of time batches (small enough to respond rapidly to requests
        # for cancellation, and to show sufficiently detailed progress - e.g. in % -
        # but not so small that GUI slows down due to the avalanche of progress notifications)
        visualres = 0.01

        minslicesize = 2
        maxslicesize = int(round(self.stepcount/20.))    # Maximum slice: 5 % of complete simulation
        if maxslicesize<minslicesize: maxslicesize = minslicesize
        
        # if no progress notifications are desired and the simulation cannot be cancelled,
        # simply run the complete simulation at once (slice size = entire simulation)
        islicesize = 100
        if progresscallback is None and continuecallback is None: islicesize = self.stepcount

        hasmore = True
        
        time_runstart = clock()
        while hasmore:
            time_slicestart = clock()
            
            # Check if we have to cancel
            if continuecallback is not None and not continuecallback():
                print('GOTM run was cancelled; stopping simulation.')
                self.result.returncode = 2
                break

            hasmore = self.runSlab(slicesize=islicesize)

            time_slicestop = clock()

            if progresscallback is not None:
                # Send 'progress' event
                prog = self.getProgress()
                remaining = (1-prog)*(time_slicestop-time_runstart)/prog
                progresscallback(prog,remaining)

            # Adjust slice size, aiming for slices that take 0.4 seconds to simulate.
            elapsed = time_slicestop-time_slicestart
            if elapsed==0:
                islicesize = maxslicesize
            else:
                islicesize = int(round(islicesize * 0.4/elapsed))
                if islicesize<minslicesize: islicesize = minslicesize
                if islicesize>maxslicesize: islicesize = maxslicesize
          
    def getProgress(self):
        return (self.currentpos-self.start+1)/float(self.stepcount)

    def runSlab(self,slicesize=100):
        assert self.result.returncode==0, 'Run did not initialize successfully, or failed. %s' % self.result.errormessage
        assert self.currentpos<=self.stop,'Run has already completed'
        
        # Configure GOTM for new slice.
        islicestop = self.currentpos + slicesize - 1
        if islicestop>self.stop: islicestop = self.stop
        pygotm.set_time_bounds(self.currentpos,islicestop)
        
        # Process time batch
        try:
            pygotm.run()
        except Exception as e:
            self.result.errormessage = 'Exception thrown in GOTM time loop: %s' % e
            self.result.returncode = 1
            return

        self.currentpos = islicestop + 1

        return self.currentpos<=self.stop

    def getBioVariableInfo(self):
        def readstringarray(stringdata):
            if stringdata is None: return ()
            stringdata = stringdata.T.reshape(stringdata.shape)
            return [''.join(stringdata[i,:]).strip() for i in range(stringdata.shape[0])]
        names = readstringarray(gotm.bio_var.var_names)
        longnames = readstringarray(gotm.bio_var.var_long)
        units = readstringarray(gotm.bio_var.var_units)
        return names,longnames,units

    def getDepth(self):
        return gotm.meanflow.h.sum()

    def getBioValues(self):
        if gotm.bio_var.cc is None: return ()
        return list((gotm.bio_var.cc*gotm.meanflow.h).sum(axis=1)/gotm.meanflow.h.sum())

    def setBioValues(self,values):
        assert len(values)==gotm.bio_var.cc.shape[0],'Number of provided values (%i) does not match number of bio state variables (%s).' % (len(values),gotm.bio_var.cc.shape[0])
        oldvalues = self.getBioValues()
        values = list(values)
        import numpy
        values = numpy.asarray(values,dtype=numpy.float)
        relchange = values/numpy.asarray(oldvalues,dtype=numpy.float)
        relchange.shape = -1,1
        gotm.bio_var.cc *= relchange

def simulate(scenario,progresscallback=None,continuecallback=None,redirect=True):
    simulator = Simulator(scenario,redirect=redirect)
    result = simulator.result
    if result.returncode==0:
        simulator.run(progresscallback=progresscallback,continuecallback=continuecallback)
    simulator.finalize()
    return result
