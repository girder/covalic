add_standard_plugin_tests(PACKAGE "covalic")

add_eslint_test(
    covalic_external "${CMAKE_CURRENT_LIST_DIR}/covalic/web_external")
add_puglint_test(
    covalic_external "${CMAKE_CURRENT_LIST_DIR}/covalic/web_external")
add_stylint_test(
    covalic_external "${CMAKE_CURRENT_LIST_DIR}/covalic/web_external")
