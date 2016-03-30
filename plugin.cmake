add_python_test(user_emails PLUGIN covalic)
add_python_style_test(python_static_analysis_covalic
                      "${PROJECT_SOURCE_DIR}/plugins/covalic/server")

add_eslint_test(
  covalic "${PROJECT_SOURCE_DIR}/plugins/covalic/web_external/js"
  ESLINT_CONFIG_FILE "${PROJECT_SOURCE_DIR}/plugins/covalic/web_external/js/.eslintrc"
  ESLINT_IGNORE_FILE "${PROJECT_SOURCE_DIR}/plugins/covalic/web_external/js/.eslintignore"
  )
