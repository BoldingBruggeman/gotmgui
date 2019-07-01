cmake_minimum_required(VERSION 3.0)

# Build wheel
add_custom_command(OUTPUT wheel.stamp
#KB                   COMMAND ${CMAKE_COMMAND} -E copy "$<TARGET_FILE:gotmgui>" pygotm/
                   COMMAND ${CMAKE_COMMAND} -E copy_directory "${CMAKE_SOURCE_DIR}/gotmgui" gotmgui/
                   COMMAND ${CMAKE_COMMAND} -E copy "${CMAKE_BINARY_DIR}/pygotm/libpython_gotm.so" ${CMAKE_CURRENT_BINARY_DIR}/gotmgui/
                   COMMAND ${PYTHON_EXECUTABLE} "${CMAKE_CURRENT_SOURCE_DIR}/setup.py" bdist_wheel
                   VERBATIM)
add_custom_target(wheel ALL DEPENDS wheel.stamp python_gotm)

# Let pip install the wheel
install(CODE "execute_process(COMMAND ${PYTHON_EXECUTABLE} -m pip install --no-index --find-links=${CMAKE_CURRENT_BINARY_DIR}/dist --user --force-reinstall --upgrade gotmgui WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/dist)")

# Upload
add_custom_target(wheel_upload COMMAND twine upload dist/*.whl DEPENDS wheel)

