FILE(GLOB PY_FILES *.py)
FILE(GLOB DESCR_FILES description/*.txt)
FILE(GLOB HELPER_FILES helper/*.py)
FiLE(GLOB HELP_FILES description/doc/*.html)

PLUGIN_INSTALL(processing ./swmm ${PY_FILES} swmm.png)
