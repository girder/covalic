add_python_test(challenge PLUGIN covalic)
add_python_test(challenge_timeframe PLUGIN covalic)
add_python_test(phase PLUGIN covalic)
add_python_test(user_emails PLUGIN covalic)
add_python_test(asset_folder PLUGIN covalic)
add_python_test(submission_folder_access PLUGIN covalic)
add_python_style_test(python_static_analysis_covalic
                      "${PROJECT_SOURCE_DIR}/plugins/covalic/server")

add_eslint_test(
  covalic "${PROJECT_SOURCE_DIR}/plugins/covalic/web_external"
  ESLINT_CONFIG_FILE "${PROJECT_SOURCE_DIR}/plugins/covalic/web_external/.eslintrc"
  ESLINT_IGNORE_FILE "${PROJECT_SOURCE_DIR}/plugins/covalic/web_external/.eslintignore"
)

add_puglint_test(
    covalic "${PROJECT_SOURCE_DIR}/plugins/${PLUGIN}/web_external/templates")
