cmake_minimum_required(VERSION 3.0)

# Use solution folders in IDEs
set_property(GLOBAL PROPERTY USE_FOLDERS ON)

add_subdirectory(pygotm EXCLUDE_FROM_ALL)
include(gotmgui/CMakeLists.txt)
