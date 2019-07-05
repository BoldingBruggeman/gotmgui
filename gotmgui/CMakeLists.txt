cmake_minimum_required(VERSION 3.0)

# Create gotmgui project.
project(gotmgui LANGUAGES NONE)

find_package(PythonInterp)

# Build wheel
add_custom_command(OUTPUT gotmgui_wheel.stamp
#KB                   COMMAND ${CMAKE_COMMAND} -E copy "$<TARGET_FILE:gotmgui>" pygotm/
                   COMMAND ${CMAKE_COMMAND} -E copy_directory "${CMAKE_SOURCE_DIR}/gotmgui" gotmgui/
                   COMMAND ${PYTHON_EXECUTABLE} "${CMAKE_CURRENT_SOURCE_DIR}/setup.py" bdist_wheel
                   VERBATIM)
#add_custom_target(wheel ALL DEPENDS wheel.stamp python_gotm)
add_custom_target(gotmgui_wheel ALL DEPENDS gotmgui_wheel.stamp)

# Let pip install the wheel
install(CODE "execute_process(COMMAND ${PYTHON_EXECUTABLE} -m pip install --no-index --find-links=${CMAKE_CURRENT_BINARY_DIR}/dist --user --force-reinstall --upgrade gotmgui WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/dist)")

# Upload
add_custom_target(gotmgui_wheel_upload COMMAND twine upload dist/*.whl DEPENDS gotmgui_wheel)
