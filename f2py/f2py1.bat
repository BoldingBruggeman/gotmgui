f2py.py -h gotm.pyf ../../src/gotm/gotm.F90 only: init_gotm time_loop clean_up : ../../src/util/time.F90 only: minn maxn : ../gui_util.f90 only: redirectoutput resetoutput getversion : ../../src/extras/bio/bio_var.F90 only: var_names,var_units,var_long,cc : ../../src/meanflow/meanflow.F90 only: h : -m gotm