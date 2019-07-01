cmake_minimum_required(VERSION 3.0)

# Use solution folders in IDEs
set_property(GLOBAL PROPERTY USE_FOLDERS ON)

# Create main project.
project(gotmgui LANGUAGES NONE)

# Find target Python interpreter.
find_package(PythonInterp)
# Query Python itself for default installation prefix.
execute_process(COMMAND ${PYTHON_EXECUTABLE} -m site --user-site
                OUTPUT_VARIABLE SITE_PACKAGES_DIR
                OUTPUT_STRIP_TRAILING_WHITESPACE)
set(DEFAULT_PREFIX "${SITE_PACKAGES_DIR}")

# Set cache variable with installation prefix.
if(CMAKE_INSTALL_PREFIX_INITIALIZED_TO_DEFAULT)
  # None set - set our default prefix.
  set(CMAKE_INSTALL_PREFIX "${DEFAULT_PREFIX}" CACHE PATH "Directory to install gotmgui in" FORCE)
else()
  # User specified a prefix - just update the variable description.
  set(CMAKE_INSTALL_PREFIX "${DEFAULT_PREFIX}" CACHE PATH "Directory to install gotmgui in")
endif()
message(STATUS "Installation prefix: ${CMAKE_INSTALL_PREFIX}")

add_subdirectory(pygotm EXCLUDE_FROM_ALL)
include(gotmgui/CMakeLists.txt)
