//
// $Id: gotmmodule.cpp,v 1.1 2006-11-24 15:52:14 kbk Exp $
//
/* File: gotmmodule.c
 * This file is auto-generated with f2py (version:2_2236).
 * f2py is a Fortran to Python Interface Generator (FPIG), Second Edition,
 * written by Pearu Peterson <pearu@cens.ioc.ee>.
 * See http://cens.ioc.ee/projects/f2py2e/
 * Generation date: Sat Sep 16 10:21:23 2006
 * $Revision: 1.1 $
 * $Date: 2006-11-24 15:52:14 $
 * Do not edit this file directly unless you know what you are doing!!!
 */
#ifdef __cplusplus
extern "C" {
#endif

/*********************** See f2py2e/cfuncs.py: includes ***********************/
#include "Python.h"
#include "fortranobject.h"
#include <string.h>

/**************** See f2py2e/rules.py: mod_rules['modulebody'] ****************/
static PyObject *gotm_error;
static PyObject *gotm_module;

/*********************** See f2py2e/cfuncs.py: typedefs ***********************/
typedef char * string;

/****************** See f2py2e/cfuncs.py: typedefs_generated ******************/
/*need_typedefs_generated*/

/********************** See f2py2e/cfuncs.py: cppmacros **********************/
#define STRINGCOPYN(to,from,n)\
  if ((strncpy(to,from,sizeof(char)*(n))) == NULL) {\
    PyErr_SetString(PyExc_MemoryError, "strncpy failed");\
    goto capi_fail;\
  } else if (strlen(to)<(n)) {\
    memset((to)+strlen(to), ' ', (n)-strlen(to));\
  } /* Padding with spaces instead of nulls. */

#define STRINGMALLOC(str,len)\
  if ((str = (string)malloc(sizeof(char)*(len+1))) == NULL) {\
    PyErr_SetString(PyExc_MemoryError, "out of memory");\
    goto capi_fail;\
  } else {\
    (str)[len] = '\0';\
  }

#ifdef DEBUGCFUNCS
#define CFUNCSMESS(mess) fprintf(stderr,"debug-capi:"mess);
#define CFUNCSMESSPY(mess,obj) CFUNCSMESS(mess) \
  PyObject_Print((PyObject *)obj,stderr,Py_PRINT_RAW);\
  fprintf(stderr,"\n");
#else
#define CFUNCSMESS(mess)
#define CFUNCSMESSPY(mess,obj)
#endif

#ifndef MAX
#define MAX(a,b) ((a > b) ? (a) : (b))
#endif
#ifndef MIN
#define MIN(a,b) ((a < b) ? (a) : (b))
#endif

#define rank(var) var ## _Rank
#define shape(var,dim) var ## _Dims[dim]
#define old_rank(var) (((PyArrayObject *)(capi_ ## var ## _tmp))->nd)
#define old_shape(var,dim) (((PyArrayObject *)(capi_ ## var ## _tmp))->dimensions[dim])
#define fshape(var,dim) shape(var,rank(var)-dim-1)
#define len(var) shape(var,0)
#define flen(var) fshape(var,0)
#define size(var) PyArray_SIZE((PyArrayObject *)(capi_ ## var ## _tmp))
/* #define index(i) capi_i ## i */
#define slen(var) capi_ ## var ## _len

#define STRINGFREE(str)\
  if (!(str == NULL)) free(str);

#if defined(PREPEND_FORTRAN)
#if defined(NO_APPEND_FORTRAN)
#if defined(UPPERCASE_FORTRAN)
#define F_FUNC(f,F) _##F
#else
#define F_FUNC(f,F) _##f
#endif
#else
#if defined(UPPERCASE_FORTRAN)
#define F_FUNC(f,F) _##F##_
#else
#define F_FUNC(f,F) _##f##_
#endif
#endif
#else
#if defined(NO_APPEND_FORTRAN)
#if defined(UPPERCASE_FORTRAN)
#define F_FUNC(f,F) F
#else
#define F_FUNC(f,F) f
#endif
#else
#if defined(UPPERCASE_FORTRAN)
#define F_FUNC(f,F) F##_
#else
#define F_FUNC(f,F) f##_
#endif
#endif
#endif
#if defined(UNDERSCORE_G77)
#define F_FUNC_US(f,F) F_FUNC(f##_,F##_)
#else
#define F_FUNC_US(f,F) F_FUNC(f,F)
#endif


/************************ See f2py2e/cfuncs.py: cfuncs ************************/
static int string_from_pyobj(string *str,int *len,const string inistr,PyObject *obj,const char *errmess) {
  PyArrayObject *arr = NULL;
  PyObject *tmp = NULL;
#ifdef DEBUGCFUNCS
fprintf(stderr,"string_from_pyobj(str='%s',len=%d,inistr='%s',obj=%p)\n",(char*)str,*len,(char *)inistr,obj);
#endif
  if (obj == Py_None) {
    if (*len == -1)
      *len = strlen(inistr); /* Will this cause problems? */
    STRINGMALLOC(*str,*len);
    STRINGCOPYN(*str,inistr,*len);
    return 1;
  }
  if (PyArray_Check(obj)) {
    if ((arr = (PyArrayObject *)obj) == NULL)
      goto capi_fail;
    if (!ISCONTIGUOUS(arr)) {
      PyErr_SetString(PyExc_ValueError,"array object is non-contiguous.");
      goto capi_fail;
    }
    if (*len == -1)
      *len = (arr->descr->elsize)*PyArray_SIZE(arr);
    STRINGMALLOC(*str,*len);
    STRINGCOPYN(*str,arr->data,*len);
    return 1;
  }
  if (PyString_Check(obj)) {
    tmp = obj;
    Py_INCREF(tmp);
  }
  else
    tmp = PyObject_Str(obj);
  if (tmp == NULL) goto capi_fail;
  if (*len == -1)
    *len = PyString_GET_SIZE(tmp);
  STRINGMALLOC(*str,*len);
  STRINGCOPYN(*str,PyString_AS_STRING(tmp),*len);
  Py_DECREF(tmp);
  return 1;
capi_fail:
  Py_XDECREF(tmp);
  {
    PyObject* err = PyErr_Occurred();
    if (err==NULL) err = gotm_error;
    PyErr_SetString(err,errmess);
  }
  return 0;
}


/********************* See f2py2e/cfuncs.py: userincludes *********************/
/*need_userincludes*/

/********************* See f2py2e/capi_rules.py: usercode *********************/


/* See f2py2e/rules.py */
/*eof externroutines*/

/******************** See f2py2e/capi_rules.py: usercode1 ********************/


/******************* See f2py2e/cb_rules.py: buildcallback *******************/
/*need_callbacks*/

/*********************** See f2py2e/rules.py: buildapi ***********************/

void for_stop_core(void) {
	throw "GOTM library stopped\n";
}

/********************************* init_gotm *********************************/
static char doc_f2py_rout_gotm_gotm_init_gotm[] = "\
Function signature:\n\
  init_gotm()\n\
";
/*  */
static PyObject *f2py_rout_gotm_gotm_init_gotm(const PyObject *capi_self,
                           PyObject *capi_args,
                           PyObject *capi_keywds,
                           void (*f2py_func)(void)) {
  PyObject * volatile capi_buildvalue = NULL;
  volatile int f2py_success = 1;
/*decl*/

  static char *capi_kwlist[] = {NULL};

/*routdebugenter*/
#ifdef F2PY_REPORT_ATEXIT
f2py_start_clock();
#endif
  if (!PyArg_ParseTupleAndKeywords(capi_args,capi_keywds,\
    "|:gotm.gotm.init_gotm",\
    capi_kwlist))
    return NULL;
/*frompyobj*/
/*end of frompyobj*/
#ifdef F2PY_REPORT_ATEXIT
f2py_start_call_clock();
#endif

/*callfortranroutine*/
const char * strException = 0;
Py_BEGIN_ALLOW_THREADS
try {
        (*f2py_func)();
}
catch (const char * ex) {
	strException = ex;
}
Py_END_ALLOW_THREADS
if (strException!=0) PyErr_SetString(PyExc_Exception, strException);

if (PyErr_Occurred())
  f2py_success = 0;
#ifdef F2PY_REPORT_ATEXIT
f2py_stop_call_clock();
#endif
/*end of callfortranroutine*/
    if (f2py_success) {
/*pyobjfrom*/
/*end of pyobjfrom*/
    CFUNCSMESS("Building return value.\n");
    capi_buildvalue = Py_BuildValue("");
/*closepyobjfrom*/
/*end of closepyobjfrom*/
    } /*if (f2py_success) after callfortranroutine*/
/*cleanupfrompyobj*/
/*end of cleanupfrompyobj*/
  if (capi_buildvalue == NULL) {
/*routdebugfailure*/
  } else {
/*routdebugleave*/
  }
  CFUNCSMESS("Freeing memory.\n");
/*freemem*/
#ifdef F2PY_REPORT_ATEXIT
f2py_stop_clock();
#endif
  return capi_buildvalue;
}
/****************************** end of init_gotm ******************************/

/********************************* time_loop *********************************/
static char doc_f2py_rout_gotm_gotm_time_loop[] = "\
Function signature:\n\
  time_loop()\n\
";
/*  */
static PyObject *f2py_rout_gotm_gotm_time_loop(const PyObject *capi_self,
                           PyObject *capi_args,
                           PyObject *capi_keywds,
                           void (*f2py_func)(void)) {
  PyObject * volatile capi_buildvalue = NULL;
  volatile int f2py_success = 1;
/*decl*/

  static char *capi_kwlist[] = {NULL};

/*routdebugenter*/
#ifdef F2PY_REPORT_ATEXIT
f2py_start_clock();
#endif
  if (!PyArg_ParseTupleAndKeywords(capi_args,capi_keywds,\
    "|:gotm.gotm.time_loop",\
    capi_kwlist))
    return NULL;
/*frompyobj*/
/*end of frompyobj*/
#ifdef F2PY_REPORT_ATEXIT
f2py_start_call_clock();
#endif

/*callfortranroutine*/
const char * strException = 0;
Py_BEGIN_ALLOW_THREADS
try {
        (*f2py_func)();
}
catch (const char * ex) {
	strException = ex;
}
Py_END_ALLOW_THREADS
if (strException!=0) PyErr_SetString(PyExc_Exception, strException);

if (PyErr_Occurred())
  f2py_success = 0;
#ifdef F2PY_REPORT_ATEXIT
f2py_stop_call_clock();
#endif
/*end of callfortranroutine*/
    if (f2py_success) {
/*pyobjfrom*/
/*end of pyobjfrom*/
    CFUNCSMESS("Building return value.\n");
    capi_buildvalue = Py_BuildValue("");
/*closepyobjfrom*/
/*end of closepyobjfrom*/
    } /*if (f2py_success) after callfortranroutine*/
/*cleanupfrompyobj*/
/*end of cleanupfrompyobj*/
  if (capi_buildvalue == NULL) {
/*routdebugfailure*/
  } else {
/*routdebugleave*/
  }
  CFUNCSMESS("Freeing memory.\n");
/*freemem*/
#ifdef F2PY_REPORT_ATEXIT
f2py_stop_clock();
#endif
  return capi_buildvalue;
}
/****************************** end of time_loop ******************************/

/********************************** clean_up **********************************/
static char doc_f2py_rout_gotm_gotm_clean_up[] = "\
Function signature:\n\
  clean_up()\n\
";
/*  */
static PyObject *f2py_rout_gotm_gotm_clean_up(const PyObject *capi_self,
                           PyObject *capi_args,
                           PyObject *capi_keywds,
                           void (*f2py_func)(void)) {
  PyObject * volatile capi_buildvalue = NULL;
  volatile int f2py_success = 1;
/*decl*/

  static char *capi_kwlist[] = {NULL};

/*routdebugenter*/
#ifdef F2PY_REPORT_ATEXIT
f2py_start_clock();
#endif
  if (!PyArg_ParseTupleAndKeywords(capi_args,capi_keywds,\
    "|:gotm.gotm.clean_up",\
    capi_kwlist))
    return NULL;
/*frompyobj*/
/*end of frompyobj*/
#ifdef F2PY_REPORT_ATEXIT
f2py_start_call_clock();
#endif

/*callfortranroutine*/
const char * strException = 0;
Py_BEGIN_ALLOW_THREADS
try {
        (*f2py_func)();
}
catch (const char * ex) {
	strException = ex;
}
Py_END_ALLOW_THREADS
if (strException!=0) PyErr_SetString(PyExc_Exception, strException);

if (PyErr_Occurred())
  f2py_success = 0;
#ifdef F2PY_REPORT_ATEXIT
f2py_stop_call_clock();
#endif
/*end of callfortranroutine*/
    if (f2py_success) {
/*pyobjfrom*/
/*end of pyobjfrom*/
    CFUNCSMESS("Building return value.\n");
    capi_buildvalue = Py_BuildValue("");
/*closepyobjfrom*/
/*end of closepyobjfrom*/
    } /*if (f2py_success) after callfortranroutine*/
/*cleanupfrompyobj*/
/*end of cleanupfrompyobj*/
  if (capi_buildvalue == NULL) {
/*routdebugfailure*/
  } else {
/*routdebugleave*/
  }
  CFUNCSMESS("Freeing memory.\n");
/*freemem*/
#ifdef F2PY_REPORT_ATEXIT
f2py_stop_clock();
#endif
  return capi_buildvalue;
}
/****************************** end of clean_up ******************************/

/******************************* redirectoutput *******************************/
static char doc_f2py_rout_gotm_gui_util_redirectoutput[] = "\
Function signature:\n\
  redirectoutput(outpath,errpath)\n\
Required arguments:\n"
"  outpath : input string(len=255)\n"
"  errpath : input string(len=255)";
/*  */
static PyObject *f2py_rout_gotm_gui_util_redirectoutput(const PyObject *capi_self,
                           PyObject *capi_args,
                           PyObject *capi_keywds,
                           void (*f2py_func)(string,string,size_t,size_t)) {
  PyObject * volatile capi_buildvalue = NULL;
  volatile int f2py_success = 1;
/*decl*/

  string outpath = NULL;
  int slen(outpath);
  PyObject *outpath_capi = Py_None;
  string errpath = NULL;
  int slen(errpath);
  PyObject *errpath_capi = Py_None;
  static char *capi_kwlist[] = {"outpath","errpath",NULL};

/*routdebugenter*/
#ifdef F2PY_REPORT_ATEXIT
f2py_start_clock();
#endif
  if (!PyArg_ParseTupleAndKeywords(capi_args,capi_keywds,\
    "OO|:gotm.gui_util.redirectoutput",\
    capi_kwlist,&outpath_capi,&errpath_capi))
    return NULL;
/*frompyobj*/
  /* Processing variable outpath */
  slen(outpath) = 255;
  f2py_success = string_from_pyobj(&outpath,&slen(outpath),"",outpath_capi,"string_from_pyobj failed in converting 1st argument `outpath' of gotm.gui_util.redirectoutput to C string");
  if (f2py_success) {
  /* Processing variable errpath */
  slen(errpath) = 255;
  f2py_success = string_from_pyobj(&errpath,&slen(errpath),"",errpath_capi,"string_from_pyobj failed in converting 2nd argument `errpath' of gotm.gui_util.redirectoutput to C string");
  if (f2py_success) {
/*end of frompyobj*/
#ifdef F2PY_REPORT_ATEXIT
f2py_start_call_clock();
#endif
/*callfortranroutine*/
        (*f2py_func)(outpath,errpath,slen(outpath),slen(errpath));
if (PyErr_Occurred())
  f2py_success = 0;
#ifdef F2PY_REPORT_ATEXIT
f2py_stop_call_clock();
#endif
/*end of callfortranroutine*/
    if (f2py_success) {
/*pyobjfrom*/
/*end of pyobjfrom*/
    CFUNCSMESS("Building return value.\n");
    capi_buildvalue = Py_BuildValue("");
/*closepyobjfrom*/
/*end of closepyobjfrom*/
    } /*if (f2py_success) after callfortranroutine*/
/*cleanupfrompyobj*/
    STRINGFREE(errpath);
  }  /*if (f2py_success) of errpath*/
  /* End of cleaning variable errpath */
    STRINGFREE(outpath);
  }  /*if (f2py_success) of outpath*/
  /* End of cleaning variable outpath */
/*end of cleanupfrompyobj*/
  if (capi_buildvalue == NULL) {
/*routdebugfailure*/
  } else {
/*routdebugleave*/
  }
  CFUNCSMESS("Freeing memory.\n");
/*freemem*/
#ifdef F2PY_REPORT_ATEXIT
f2py_stop_clock();
#endif
  return capi_buildvalue;
}
/*************************** end of redirectoutput ***************************/

/******************************** resetoutput ********************************/
static char doc_f2py_rout_gotm_gui_util_resetoutput[] = "\
Function signature:\n\
  resetoutput()\n\
";
/*  */
static PyObject *f2py_rout_gotm_gui_util_resetoutput(const PyObject *capi_self,
                           PyObject *capi_args,
                           PyObject *capi_keywds,
                           void (*f2py_func)(void)) {
  PyObject * volatile capi_buildvalue = NULL;
  volatile int f2py_success = 1;
/*decl*/

  static char *capi_kwlist[] = {NULL};

/*routdebugenter*/
#ifdef F2PY_REPORT_ATEXIT
f2py_start_clock();
#endif
  if (!PyArg_ParseTupleAndKeywords(capi_args,capi_keywds,\
    "|:gotm.gui_util.resetoutput",\
    capi_kwlist))
    return NULL;
/*frompyobj*/
/*end of frompyobj*/
#ifdef F2PY_REPORT_ATEXIT
f2py_start_call_clock();
#endif
/*callfortranroutine*/
        (*f2py_func)();
if (PyErr_Occurred())
  f2py_success = 0;
#ifdef F2PY_REPORT_ATEXIT
f2py_stop_call_clock();
#endif
/*end of callfortranroutine*/
    if (f2py_success) {
/*pyobjfrom*/
/*end of pyobjfrom*/
    CFUNCSMESS("Building return value.\n");
    capi_buildvalue = Py_BuildValue("");
/*closepyobjfrom*/
/*end of closepyobjfrom*/
    } /*if (f2py_success) after callfortranroutine*/
/*cleanupfrompyobj*/
/*end of cleanupfrompyobj*/
  if (capi_buildvalue == NULL) {
/*routdebugfailure*/
  } else {
/*routdebugleave*/
  }
  CFUNCSMESS("Freeing memory.\n");
/*freemem*/
#ifdef F2PY_REPORT_ATEXIT
f2py_stop_clock();
#endif
  return capi_buildvalue;
}
/***************************** end of resetoutput *****************************/
/*eof body*/

/******************* See f2py2e/f90mod_rules.py: buildhooks *******************/

static FortranDataDef f2py_gotm_def[] = {
  {"init_gotm",-1,{{-1}},0,NULL,(f2py_init_func)f2py_rout_gotm_gotm_init_gotm,doc_f2py_rout_gotm_gotm_init_gotm},
  {"time_loop",-1,{{-1}},0,NULL,(f2py_init_func)f2py_rout_gotm_gotm_time_loop,doc_f2py_rout_gotm_gotm_time_loop},
  {"clean_up",-1,{{-1}},0,NULL,(f2py_init_func)f2py_rout_gotm_gotm_clean_up,doc_f2py_rout_gotm_gotm_clean_up},
  {NULL}
};

static void f2py_setup_gotm(char *init_gotm,char *time_loop,char *clean_up) {
  int i_f2py=0;
  f2py_gotm_def[i_f2py++].data = init_gotm;
  f2py_gotm_def[i_f2py++].data = time_loop;
  f2py_gotm_def[i_f2py++].data = clean_up;
}
extern void F_FUNC(f2pyinitgotm,F2PYINITGOTM)(void (*)(char *,char *,char *));
static void f2py_init_gotm(void) {
  F_FUNC(f2pyinitgotm,F2PYINITGOTM)(f2py_setup_gotm);
}


static FortranDataDef f2py_time_def[] = {
  {"maxn",0,{{-1}},PyArray_INT},
  {"minn",0,{{-1}},PyArray_INT},
  {NULL}
};

static void f2py_setup_time(char *maxn,char *minn) {
  int i_f2py=0;
  f2py_time_def[i_f2py++].data = maxn;
  f2py_time_def[i_f2py++].data = minn;
}
extern void F_FUNC(f2pyinittime,F2PYINITTIME)(void (*)(char*,char*));
static void f2py_init_time(void) {
  F_FUNC(f2pyinittime,F2PYINITTIME)(f2py_setup_time);
}


static FortranDataDef f2py_gui_util_def[] = {
  {"redirectoutput",-1,{{-1}},0,NULL,(f2py_init_func)f2py_rout_gotm_gui_util_redirectoutput,doc_f2py_rout_gotm_gui_util_redirectoutput},
  {"resetoutput",-1,{{-1}},0,NULL,(f2py_init_func)f2py_rout_gotm_gui_util_resetoutput,doc_f2py_rout_gotm_gui_util_resetoutput},
  {NULL}
};

static void f2py_setup_gui_util(char *redirectoutput,char *resetoutput) {
  int i_f2py=0;
  f2py_gui_util_def[i_f2py++].data = redirectoutput;
  f2py_gui_util_def[i_f2py++].data = resetoutput;
}
extern void F_FUNC_US(f2pyinitgui_util,F2PYINITGUI_UTIL)(void (*)(char *,char *));
static void f2py_init_gui_util(void) {
  F_FUNC_US(f2pyinitgui_util,F2PYINITGUI_UTIL)(f2py_setup_gui_util);
}

/*need_f90modhooks*/

/************** See f2py2e/rules.py: module_rules['modulebody'] **************/

/******************* See f2py2e/common_rules.py: buildhooks *******************/

/*need_commonhooks*/

/**************************** See f2py2e/rules.py ****************************/

static FortranDataDef f2py_routine_defs[] = {

/*eof routine_defs*/
  {NULL}
};

static PyMethodDef f2py_module_methods[] = {

  {NULL,NULL}
};

DL_EXPORT(int) initgotm(void) {
  int i;
  PyObject *m,*d, *s;
  m = gotm_module = Py_InitModule("gotm", f2py_module_methods);
  PyFortran_Type.ob_type = &PyType_Type;
#ifdef OLD_NUMPY
  import_array();
#else
  import_array1(-1);
#endif
  if (PyErr_Occurred())
    Py_FatalError("can't initialize module gotm (failed to import numpy)");
  d = PyModule_GetDict(m);
  s = PyString_FromString("$Revision: 1.1 $");
  PyDict_SetItemString(d, "__version__", s);
  s = PyString_FromString("This module 'gotm' is auto-generated with f2py (version:2_2236).\nFunctions:\n"
"Fortran 90/95 modules:\n""  gotm --- init_gotm(),time_loop(),clean_up()""  time --- maxn,minn""  gui_util --- redirectoutput(),resetoutput()"".");
  PyDict_SetItemString(d, "__doc__", s);
  gotm_error = PyErr_NewException ("gotm.error", NULL, NULL);
  Py_DECREF(s);
  for(i=0;f2py_routine_defs[i].name!=NULL;i++)
    PyDict_SetItemString(d, f2py_routine_defs[i].name,PyFortranObject_NewAsAttr(&f2py_routine_defs[i]));





/*eof initf2pywraphooks*/
  PyDict_SetItemString(d, "gui_util", PyFortranObject_New(f2py_gui_util_def,f2py_init_gui_util));
  PyDict_SetItemString(d, "time", PyFortranObject_New(f2py_time_def,f2py_init_time));
  PyDict_SetItemString(d, "gotm", PyFortranObject_New(f2py_gotm_def,f2py_init_gotm));
/*eof initf90modhooks*/

/*eof initcommonhooks*/

  if (PyErr_Occurred())
    return -1;

#ifdef F2PY_REPORT_ATEXIT
  on_exit(f2py_report_on_exit,(void*)"gotm");
#endif
return 0;
}
#ifdef __cplusplus
}
#endif
