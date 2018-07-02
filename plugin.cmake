get_filename_component(PLUGIN ${CMAKE_CURRENT_LIST_DIR} NAME)

add_python_test(submission PLUGIN ${PLUGIN} PACKAGE "covalic")
add_python_test(challenge PLUGIN ${PLUGIN} PACKAGE "covalic")
add_python_test(challenge_timeframe PLUGIN ${PLUGIN} PACKAGE "covalic")
add_python_test(phase PLUGIN ${PLUGIN} PACKAGE "covalic")
add_python_test(user_emails PLUGIN ${PLUGIN} PACKAGE "covalic")
add_python_test(asset_folder PLUGIN ${PLUGIN} PACKAGE "covalic")
add_python_test(submission_folder_access PLUGIN ${PLUGIN})
add_python_style_test(python_static_analysis_covalic
                      "${PROJECT_SOURCE_DIR}/plugins/${PLUGIN}/covalic")

if (JAVASCRIPT_STYLE_TESTS)
  add_test(
    NAME "eslint_covalic"
    WORKING_DIRECTORY "${CMAKE_CURRENT_LIST_DIR}"
    COMMAND ${PROJECT_SOURCE_DIR}/node_modules/.bin/eslint .
  )
  set_property(TEST "eslint_covalic" PROPERTY LABELS girder_browser)
endif()

add_puglint_test(
    covalic "${PROJECT_SOURCE_DIR}/plugins/${PLUGIN}/covalic/web_client/templates")

add_puglint_test(
    covalic_external "${PROJECT_SOURCE_DIR}/plugins/${PLUGIN}/covalic/web_external/templates")
