from __future__ import print_function

# Current GOTM/namelist version used by (1) the GUI, (2) saved GUI scenario files.
# Currently (2) differs from (1) because (1) is still in development, while saved files must use a frozen
# scenario version in order to be usable later too.
guiscenarioversion = 'gotmgui-0.5.0'
savedscenarioversion = 'gotm-4.0.0'

# Import modules from standard Python library
import os, shutil, re, datetime, sys

# Import our own custom modules
import xmlstore.xmlstore, xmlstore.util, xmlstore.datatypes
from . import common, namelist

# Some parts of the schemas will be loaded from the GOTM source directory.
# For the developer's version, the source directory can be found one level below the GUI.
# For the frozen version (py2exe build), the required files are present in the gotmsrc
# subdirectory directly below the GUI directory.
if hasattr(sys,'frozen'):
    srcdir = os.path.abspath(os.path.join(common.getDataRoot(),'gotmsrc'))
else:
    srcdir = os.path.abspath(os.path.join(common.getDataRoot(),'../src'))
if os.path.isdir(srcdir): xmlstore.xmlstore.Schema.knownpaths['gotmsrc'] = srcdir

schemadir = None

class NamelistStore(xmlstore.xmlstore.TypedStore):

    def __init__(self,*args,**kwargs):
        super(NamelistStore,self).__init__(*args,**kwargs)

        self.namelistextension = self.root.templatenode.getAttribute('namelistextension')

    @classmethod
    def fromNamelists(cls,path,prototypepath=None,targetversion=None,strict = False,requireplatform=None,root=None):
        # Get a list of available schema versions and check if the target version is available.
        sourceids = cls.getSchemaInfo().getSchemas().keys()
        if targetversion is not None and targetversion not in sourceids:
            raise Exception('No schema available for desired version "%s".' % targetversion)
            
        # Rank the source versions according to correspondence with target version and version number (higher is better).
        sourceids = cls.rankSources(sourceids,targetversion,requireplatform=requireplatform)
        
        # Try the available schemas one by one, and see if they match the namelists.
        scenario,missingcount = None,None
        failures = ''
        if common.verbose:
            print('Detecting suitable schema for namelists in "%s"...' % path)
        for sourceid in sourceids:
            if common.verbose:
                print('Trying schema "%s"...' % sourceid,)
            curscenario = cls.fromSchemaName(sourceid)
            try:
                curscenario.loadFromNamelists(path,strict=strict,prototypepath=prototypepath,root=root)
            except namelist.NamelistParseException as e:
                failures += 'Path "%s" does not match template "%s".\nReason: %s\n' % (path,sourceid,e)
                if common.verbose:
                    print('no match, %s.' % (e,))
                curscenario.release()
                continue
            curmissing = ['/'.join(n.location) for n in curscenario.root.getEmptyNodes()]
            curmissingcount = len(curmissing)
            
            if common.verbose:
                if curmissingcount>0:
                    print('match, %i missing values:' % (curmissingcount,))
                    for nodepath in curmissing:
                        print('  %s' % nodepath)
                else:
                    print('complete match')
                
            if scenario is not None:
                # A schema with higher priority matched - determine if this is a better match, based on the number of missing values.
                if missingcount<=curmissingcount:
                    # Earlier schema was a better match - clean up the current one and move on.
                    curscenario.release()
                    continue
                scenario.release()
            scenario,missingcount = curscenario,curmissingcount
                
        # Check if we found a schema that matches the namelists.
        if scenario is None:
            raise Exception('The path "%s" does not contain a supported scenario. Details:\n%s' % (path,failures))

        if common.verbose:
            print('Final selected schema: %s.' % (scenario.version))
            
        # Convert the store to the desired version, if specified.
        if targetversion is not None and scenario.version!=targetversion:
            if common.verbose:
                print('Converting to desired schema version %s...' % targetversion)
            newscenario = scenario.convert(targetversion)
            scenario.release()
            return newscenario
        else:
            return scenario
            
    class NoNamelistRepresentationException(Exception):
        pass
        
    def detectNodeRolesInNamelist(self,interface=None):
        if interface is None: interface = self.getInterface(omitgroupers=True,interfacetype='nml')
    
        # Iterate over all nodes and determine whether they represent
        # a directory (0), a file (1), a namelist (2) or a namelist variable (3) in a namelist representation.
        node2nmltype = {}
        def detectNodeRoleInNml(node):
            children = interface.getChildren(node)
            if len(children)==0:
                tp = 3
            else:
                tp = None
                for child in children:
                    typefromchild = max(0,detectNodeRoleInNml(child)-1)
                    if tp is None:
                        tp = typefromchild
                    elif tp!=typefromchild:
                        raise self.NoNamelistRepresentationException('Node %s contains mixed content that cannot correspond to a namelist representation.' % '/'.join(node.location))
            node2nmltype[node] = tp
            return tp
        detectNodeRoleInNml(self.root)
        return node2nmltype

    def loadFromNamelists(self, srcpath, strict=False, prototypepath=None, root=None):

        def processDirectory(node,prefix=''):
            assert node2nmltype[node]==0,'processDirectory should only be called on nodes representing a directory in the namelist representation.'
            for child in interface.getChildren(node):
                childpath = prefix+child.getId()
                if node2nmltype[child]==0:
                    # Child node represents another directory.
                    processDirectory(child,childpath+'/')
                else:
                    # Child node represents a file with namelists.
                    cursubs = globalsubs
                    if prototypepath is None:
                        # Normal namelist file
                        ext = self.namelistextension
                        if child.templatenode.hasAttribute('namelistextension'):
                            ext = child.templatenode.getAttribute('namelistextension')
                        fullnmlfilename = childpath+ext
                    else:
                        # Prototype namelist in which values will be substituted.
                        fullnmlfilename = childpath+'.proto'

                        # Load the relevant value substitutions (if any).
                        df = container.getItem(nmlfilename+'.values')
                        if df is not None:
                            df_file = df.getAsReadOnlyFile()
                            cursubs = [namelist.NamelistSubstitutions(df_file)]
                            df_file.close()
                            df.release()

                    # Find and parse the namelist file.
                    for fn in nmlfilelist:
                        if fn==fullnmlfilename or fn.endswith('/'+fullnmlfilename):
                            # Note - we currently also allow the namelist file to be found deeper in the source container tree.
                            # This serves to allow tar/gz files with a single root folder that contains the namelist files.
                            fullnmlfilename = fn
                            break
                    else:
                        # Namelist file was not found.
                        if child.templatenode.getAttribute('optional')=='True':
                            # This namelist file is missing but not required. Use default values and continue.
                            if self.defaultstore is not None:
                                child.copyFrom(self.defaultstore.mapForeignNode(child))
                            continue
                        elif child.isHidden():
                            # This namelist file is missing but will not be used. Thus no worries: continue.
                            continue
                        else:
                            raise namelist.NamelistParseException('Namelist file "%s" is not present.' % fullnmlfilename,None,None,None)
                            
                    # Obtain the namelist file, open it, parse it, and close it.
                    df = nmlcontainer.getItem(fullnmlfilename)
                    df_file = df.getAsReadOnlyFile()
                    nmlfile = namelist.NamelistFile(df_file,cursubs)
                    df_file.close()
                    df.release()
            
                    # Child node represents a file containing namelists.
                    processFile(child,nmlfile,fullnmlfilename)
        
        def processFile(node,nmlfile,fullnmlfilename):
            # Loop over all nodes below the node representing the namelst file (each node represents a namelist)
            for filechild in interface.getChildren(node):
                processNamelist(filechild,nmlfile,fullnmlfilename)
        
        def processNamelist(node,nmlfile,fullnmlfilename):
            # Get name of the expected namelist.
            listname = node.getId()
            
            # Get a list with all child nodes (i.e., namelist variables)
            listchildren = interface.getChildren(node)

            assert not node.canHaveValue(), 'Found non-folder node with id %s below branch %s, where only folders are expected.' % (listname,nmlfilename)

            # Parse the next namelist.
            nmlist = nmlfile.parseNextNamelist(expectedlist=listname)

            # Index of next expected child node [used only in "strict" parsing mode]
            childindex = 0

            for (foundvarname,slic,vardata) in nmlist:

                if strict:
                    # Strict parsing: all variables must appear once and in predefined order.
                    if childindex>=len(listchildren):
                        raise namelist.NamelistParseException('Encountered variable "%s" where end of namelist was expected.' % (foundvarname,),fullnmlfilename,listname,None)
                    listchild = listchildren[childindex]
                    varname = listchild.getId()
                    if varname.lower()!=foundvarname.lower():
                        raise namelist.NamelistParseException('Found variable "%s" where "%s" was expected.' % (foundvarname,varname),fullnmlfilename,listname,varname)
                    childindex += 1
                else:
                    # Loose parsing: variables can appear multiple times or not at all, and do not need to appear in order.
                    # This is how FORTRAN operates.
                    for listchild in listchildren:
                        varname = listchild.getId()
                        if varname.lower()==foundvarname.lower(): break
                    else:
                        raise namelist.NamelistParseException('Encountered variable "%s", which should not be present in this namelist.' % (foundvarname,),fullnmlfilename,listname)
                        
                # If no value was provided, skip to the next assignment.
                if vardata is None: continue

                # Retrieve the value (in the correct data type) from the namelist string.
                vartype = listchild.getValueType(returnclass=True)
                if slic is None:
                    # No slice specification - assign to entire variable.
                    try:
                        val = vartype.fromNamelistString(vardata,datafilecontext,listchild.templatenode)
                    except Exception as e:
                        raise namelist.NamelistParseException('%s Variable data: %s' % (e,vardata),fullnmlfilename,listname,varname)
                else:
                    # Slice specification provided - assign to subset of variable.
                    val = listchild.getValue()
                    if val is None: val = vartype(template=listchild.templatenode)
                    val.setItemFromNamelist(slic,vardata,datafilecontext,listchild.templatenode)

                # Transfer the value to the store.
                listchild.setValue(val)
                
                # Release the value object.
                if isinstance(val,xmlstore.util.referencedobject):
                    val.release()
                
            # If we are in "strict" mode, check if there are any remaining variables that were not assigned to.
            if strict and childindex<len(listchildren):
                lcnames = ['"%s"' % lc.getId() for lc in listchildren[childindex:]]
                raise namelist.NamelistParseException('Variables %s are missing' % ', '.join(lcnames),fullnmlfilename,listname,None)

        # Start with empty scenario
        self.setStore(None)

        # Retrieve an interface to the store.
        # (by accessing it through the interface, namelist-specific instructions in the schema
        # will be respected)
        interface = self.getInterface(omitgroupers=True,interfacetype='nml')
        
        # Determine for each node in the store what structure it corresponds to in the namelist representation.
        # Structures can be directories (type 0), files (type 1), namelists (type 2) and namelist variables (type 3).
        # An exception will be thrown if the schema cannot map to a valid namelist representation, i.e.,
        # when a node would contain a mixture of files, namelists and/or namelist variables.
        try:
            node2nmltype = self.detectNodeRolesInNamelist(interface)
        except self.NoNamelistRepresentationException:
            raise namelist.NamelistParseException('This schema cannot be used for namelists.')

        if root is None:
            root = self.root
        elif isinstance(root, (str, u''.__class__)):
            strroot = root
            root = self.root[strroot]
            if root is None:
                raise namelist.NamelistParseException('Specified root node "%s" does not exist in schema.' % strroot)

        datafilecontext = {}
        roottype = node2nmltype[root]
        assert roottype in (0,1),'Root of data store should represent either a directory (0) or file (1) in namelists, but its type equals %i.' % roottype
        try:
            if roottype==0:
                # Root node maps to a directory in namelist representation.
            
                # Try to open the specified path as a file container (currently can be zip, tar/gz or a directory)
                # This path will contain namelist values.
                try:
                    container = xmlstore.datatypes.DataContainer.fromPath(srcpath)
                except Exception as e:
                    raise Exception('Unable to load specified path. ' + unicode(e))

                # Retrieve the container for the namelist structures.
                # This is the same container that contains values, unless we are using prototype files.
                globalsubs = []
                if prototypepath is not None:
                    # Namelist are specified as .proto files plus one or more .values files.

                    # Open the container for prototype/template files.
                    nmlcontainer = xmlstore.datatypes.DataContainerDirectory(prototypepath)

                    # Load the substitutions specified in the main .values file.
                    df = container.getItem(os.path.basename(srcpath)+'.values')
                    df_file = df.getAsReadOnlyFile()
                    globalsubs.append(namelist.NamelistSubstitutions(df_file))
                    df_file.close()
                    df.release()
                else:
                    # Namelist structure and values are stored together in files with F90 namelists.
                    # Obtain a new reference to the values container that was opened before.
                    nmlcontainer = container.addref()

                # Build a list of files in the namelist directory
                nmlfilelist = nmlcontainer.listFiles()
                
                # Define the context for reading store values. This includes a reference to the source container,
                # as values may be stored in separate files containing binary or textual data.
                datafilecontext['container'] = container.addref()
            
                try:
                    processDirectory(root)
                finally:
                    container.release()
                    nmlcontainer.release()
            else:
                if not os.path.isfile(srcpath):
                    raise Exception('"%s" is not an existing file.' % srcpath)
                    
                # Define the context for reading store values. This includes a reference to the source container,
                # as values may be stored in separate files containing binary or textual data.
                datafilecontext['container'] = xmlstore.datatypes.DataContainerDirectory(os.path.split(srcpath)[0])

                # Open the namelist file, parse it, and close it.
                df_file = open(srcpath,'rU')
                nmlfile = namelist.NamelistFile(df_file)
                df_file.close()
        
                # Child node represents a file containing namelists.
                processFile(root,nmlfile,srcpath)
        finally:            
            self.disconnectInterface(interface)
            if 'linkedobjects' in datafilecontext:
                for v in datafilecontext['linkedobjects'].values():
                    v.release()
            if 'container' in datafilecontext:
                datafilecontext['container'].release()

    def writeAsNamelists(self, targetpath, copydatafiles=True, addcomments=False, allowmissingvalues=False, callback=None, root=None):
    
        def processDirectory(node,prefix=''):
            children = interface.getChildren(node)
            progslicer = xmlstore.util.ProgressSlicer(callback,len(children))
            for child in children:
                childpath = os.path.join(prefix,child.getId())
                progslicer.nextStep(childpath)
                
                if child.isHidden(): continue
                
                if node2nmltype[child]==0:
                    # Child node maps to a directory in namelist representation.
                    if not os.path.isdir(childpath): os.mkdir(childpath)
                    processDirectory(child,childpath)
                else:
                    # Child node maps to a file in namelist representation.

                    # Create the namelist file.
                    ext = self.namelistextension
                    if child.templatenode.hasAttribute('namelistextension'):
                        ext = child.templatenode.getAttribute('namelistextension')
                    nmlfilepath = childpath+ext
                    nmlfile = open(nmlfilepath,'w')
                    try:
                        processFile(child,nmlfile)
                    finally:
                        nmlfile.close()

        def processFile(node,nmlfile):
            for child in interface.getChildren(node):
                listname = child.getId()
                listchildren = interface.getChildren(child)

                if addcomments:
                    nmlfile.write('!'+(linelength-1)*'-'+'\n')
                    title = child.getText(detail=2).encode('ascii','xmlstore_descrepl')
                    nmlfile.write(textwrap.fill(title,linelength-2,initial_indent='! ',subsequent_indent='! '))
                    nmlfile.write('\n!'+(linelength-1)*'-'+'\n')

                    comments = []
                    varnamelength = 0
                    for listchild in listchildren:
                        comment = self.getNamelistVariableDescription(listchild)
                        if len(comment[0])>varnamelength: varnamelength = len(comment[0])
                        comments.append(comment)
                    wrapper.width = linelength-varnamelength-5
                    for (varid,vartype,lines) in comments:
                        wrappedlines = []
                        lines.insert(0,'['+vartype+']')
                        for line in lines:
                            line = line.encode('ascii','xmlstore_descrepl')
                            wrappedlines += wrapper.wrap(line)
                        firstline = wrappedlines.pop(0)
                        nmlfile.write('! %-*s %s\n' % (varnamelength,varid,firstline))
                        for line in wrappedlines:
                            nmlfile.write('! '+varnamelength*' '+'   '+line+'\n')
                    if len(comments)>0:
                        nmlfile.write('!'+(linelength-1)*'-'+'\n')
                    nmlfile.write('\n')

                nmlfile.write('&'+listname+'\n')
                for listchild in listchildren:
                    if listchild.hasChildren():
                        raise Exception('Found a folder ("%s") below branch %s/%s, where only variables are expected.' % (listchild.getId(),nmlfilename,listname))
                    varname = listchild.getId()
                    varval = listchild.getValue(usedefault=True)
                    if varval is None:
                        # If the variable value is not set while its node is hidden,
                        # the variable will not be used, and we skip it silently.
                        if allowmissingvalues or listchild.isHidden(): continue
                        raise Exception('Value for variable "%s" in namelist "%s" not set.' % (varname,listname))
                    varstring = varval.toNamelistString(context,listchild.templatenode)
                    if isinstance(varstring,(list,tuple)):
                        for ind,value in varstring:
                            nmlfile.write('   %s(%s) = %s,\n' % (varname,ind,value.encode('ascii','xmlstore_descrepl')))
                    else:
                        nmlfile.write('   %s = %s,\n' % (varname,varstring.encode('ascii','xmlstore_descrepl')))
                    if isinstance(varval,xmlstore.util.referencedobject): varval.release()
                nmlfile.write('/\n\n')

        # Retrieve an interface to the store.
        # (by accessing it through the interface, namelist-specific instructions in the schema
        # will be respected)
        interface = self.getInterface(omitgroupers=True,interfacetype='nml')
        
        # Determine for each node in the store what structure it corresponds to in the namelist representation.
        # Structures can be directories (type 0), files (type 1), namelists (type 2) and namelist variables (type 3).
        # An exception will be thrown if the schema cannot map to a valid namelist representation, i.e.,
        # when a node would contain a mixture of files, namelists and/or namelist variables.
        node2nmltype = self.detectNodeRolesInNamelist(interface)

        if common.verbose:
            print('Exporting scenario to namelist files...')

        if addcomments:
            # Import and configure text wrapping utility.
            import textwrap
            linelength = 80
            wrapper = textwrap.TextWrapper(subsequent_indent='  ')

        # Define the context used for writing data files.
        context = {}
        
        # If root node is not specified, use the root of the schema.
        if root is None:
            root = self.root
        elif isinstance(root, (str, u''.__class__)):
            root = self.root[root]
            
        roottype = node2nmltype[root]
        assert roottype in (0,1),'Root of data store should represent either a directory (0) or file (1) in namelists, but its type equals %i.' % roottype
        try:
            if roottype==0:
                # Root node maps to a directory in namelist representation.
            
                # If the directory to write to does not exist, create it.
                createddir = False
                if not os.path.isdir(targetpath):
                    try:
                        os.mkdir(targetpath)
                        createddir = True
                    except Exception as e:
                        raise Exception('Unable to create target directory "%s". Error: %s' %(targetpath,str(e)))
                        
                # Set the context for writing of node values.
                # The "targetcontainer" variable will serve as the location to write auxilliary data files to.
                if copydatafiles:
                    context['targetcontainer'] = xmlstore.datatypes.DataContainerDirectory(targetpath)
                    
                # Write the namelist tree, and make sure the created directory is deleted if any error occurs.
                try:
                    processDirectory(root,targetpath)
                except:
                    if createddir: shutil.rmtree(targetpath)
                    raise
            else:
                # Root node maps to a file in namelist representation
                if copydatafiles:
                    context['targetcontainer'] = xmlstore.datatypes.DataContainerDirectory(os.path.split(os.path.normpath(targetpath))[0])

                # Open the target namelist file
                nmlfile = open(targetpath,'w')
                try:
                    processFile(root,nmlfile)
                finally:
                    nmlfile.close()
        finally:
            self.disconnectInterface(interface)
            if 'targetcontainer' in context: context['targetcontainer'].release()

    @staticmethod
    def getNamelistVariableDescription(node):
        varid = node.getId()
        datatype = node.getValueType()
        description = node.getText(detail=2)
        lines = [description]
        
        if node.templatenode.hasAttribute('hasoptions'):
            # Create list of options.
            options = xmlstore.util.findDescendantNode(node.templatenode,['options'])
            assert options is not None, 'Node is of type "select" but lacks "options" childnode.'
            for ch in options.childNodes:
                if ch.nodeType==ch.ELEMENT_NODE and ch.localName=='option':
                    lab = ch.getAttribute('description')
                    if lab=='': lab = ch.getAttribute('label')
                    lines.append(ch.getAttribute('value')+': '+lab)

        # Create description of data type and range.
        isarray = datatype.startswith('array(') and datatype.endswith(')')
        if isarray: datatype = datatype[6:-1]
        if datatype=='gotmdatafile':
            datatype = 'file path'
        elif datatype=='int':
            datatype = 'integer'
        elif datatype=='datetime':
            datatype = 'string, format = "yyyy-mm-dd hh:mm:ss"'
        if isarray:
            datatype += ' array'
            if node.templatenode.hasAttribute('shape'):
                datatype += ' with shape (%s)' % node.templatenode.getAttribute('shape')
        if node.templatenode.hasAttribute('minInclusive'):
            datatype += ', minimum = ' + node.templatenode.getAttribute('minInclusive')
        if node.templatenode.hasAttribute('maxInclusive'):
            datatype += ', maximum = ' + node.templatenode.getAttribute('maxInclusive')
        unit = node.getUnit()
        if unit is not None:
            datatype += ', unit = ' + unit

        # Get description of conditions (if any).
        condition = xmlstore.util.findDescendantNode(node.templatenode,['condition'])
        if condition is not None:
            prefix = 'This variable is only used if '
            condtype = condition.getAttribute('type')
            if condtype=='ne':
                prefix = 'This variable is not used if '
                condtype = 'eq'
            condline = NamelistStore.getNamelistConditionDescription(condition,condtype)
            lines.append(prefix+condline)

        return (varid,datatype,lines)

    @staticmethod
    def getNamelistConditionDescription(node,condtype=None):
        if condtype is None: condtype = node.getAttribute('type')
        if condtype=='eq' or condtype=='ne':
            var = node.getAttribute('variable')
            val = node.getAttribute('value')
            if var.startswith('./'): var=var[2:]
            if condtype=='eq':
                return var+' = '+val
            else:
                return var+' != '+val
        elif condtype=='and' or condtype=='or':
            conds = xmlstore.util.findDescendantNodes(node,['condition'])
            conddescs = map(NamelistStore.getNamelistConditionDescription,conds)
            return '('+(' '+condtype+' ').join(conddescs)+')'
        else:
            raise Exception('Unknown condition type "%s".' % condtype)

class Scenario(NamelistStore):

    # Descriptive name for the store to be used when communicating with the user.
    packagetitle = 'GOTM scenario'

    @classmethod
    def getSchemaInfo(cls):
        global schemadir
        if schemadir is None:
            import pygotm
            schemadir = (os.path.join(common.getDataRoot(),'schemas/scenario'), pygotm.get_schemas())
        return xmlstore.xmlstore.schemainfocache[schemadir]

    def __init__(self,schema,valueroot=None,adddefault = True):
        super(Scenario,self).__init__(schema,valueroot,adddefault=adddefault)

    @classmethod
    def getCustomDataTypes(ownclass):
        dt = super(Scenario,ownclass).getCustomDataTypes()
        import xmlplot.data
        dt['gotmdatafile'] = xmlplot.data.LinkedFileVariableStore
        return dt

    @classmethod
    def fromXmlFile(cls,path,**kwargs):
        store = super(Scenario,cls).fromXmlFile(path,**kwargs)

        # If the scenario was stored in the official 'save' version, and we only converted it to the display version,
        # we should not consider it changed. In that case, reset the 'changed' status.
        if store.originalversion==savedscenarioversion and store.version==guiscenarioversion: store.resetChanged()

        return store

    @classmethod
    def fromContainer(cls,path,*args,**kwargs):
        store = super(Scenario,cls).fromContainer(path,*args,**kwargs)

        # If the scenario was stored in the official 'save' version, and we only converted it to the display version,
        # we should not consider it changed. In that case, reset the 'changed' status.
        if store.originalversion==savedscenarioversion and store.version==guiscenarioversion: store.resetChanged()

        return store

    def saveAll(self,path,targetversion=None,*args,**kwargs):
        # Set default version
        if targetversion is None: targetversion = savedscenarioversion

        # Make sure any missing values are filled with defaults before saving.
        kwargs['fillmissing'] = True

        super(Scenario,self).saveAll(path,targetversion=targetversion,*args,**kwargs)
