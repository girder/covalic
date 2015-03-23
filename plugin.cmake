add_python_style_test(python_static_analysis_covalic
                      "${PROJECT_SOURCE_DIR}/plugins/covalic/server")

add_javascript_style_test(
  covalic "${PROJECT_SOURCE_DIR}/plugins/covalic/web_external/js"
  JSHINT_EXTRA_CONFIGS ${PROJECT_SOURCE_DIR}/plugins/covalic/web_external/js/.jshintrc
  )
