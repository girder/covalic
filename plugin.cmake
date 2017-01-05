get_filename_component(PLUGIN ${CMAKE_CURRENT_LIST_DIR} NAME)

add_python_test(challenge PLUGIN ${PLUGIN})
add_python_test(challenge_timeframe PLUGIN ${PLUGIN})
add_python_test(phase PLUGIN ${PLUGIN})
add_python_test(user_emails PLUGIN ${PLUGIN})
add_python_test(asset_folder PLUGIN ${PLUGIN})
add_python_test(submission_folder_access PLUGIN ${PLUGIN})
add_python_style_test(python_static_analysis_covalic
                      "${PROJECT_SOURCE_DIR}/plugins/${PLUGIN}/server")

add_eslint_test(
  ${PLUGIN} "${PROJECT_SOURCE_DIR}/plugins/${PLUGIN}/web_external"
  ESLINT_CONFIG_FILE "${PROJECT_SOURCE_DIR}/plugins/${PLUGIN}/web_external/.eslintrc"
  ESLINT_IGNORE_FILE "${PROJECT_SOURCE_DIR}/plugins/${PLUGIN}/web_external/.eslintignore"
)

add_puglint_test(
    covalic "${PROJECT_SOURCE_DIR}/plugins/${PLUGIN}/web_external/templates")
