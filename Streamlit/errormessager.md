Fehler bei der Klassifizierung: Could not find page: `pages/1_eBKP_Auswertung.py`. You must provide a file path relative to the entrypoint file (from the directory `Streamlit`). Only the entrypoint file and files in the `pages/` directory are supported.


KeyError: 'level'

File "/Users/orlandobassi/Documents/GitHub/TA.BA_DT_PROGR/Streamlit/pages/02_KI_Klassifizierung.py", line 1734, in `<module>`
    display_log()
    ~~~~~~~~~~~^^
File "/Users/orlandobassi/Documents/GitHub/TA.BA_DT_PROGR/Streamlit/pages/02_KI_Klassifizierung.py", line 290, in display_log
    level = log_entry['level']
            ~~~~~~~~~^^^^^^^^^



KeyError: 'level'

File "/Users/orlandobassi/Documents/GitHub/TA.BA_DT_PROGR/Streamlit/pages/02_KI_Klassifizierung.py", line 1734, in `<module>`
    display_log()
    ~~~~~~~~~~~^^
File "/Users/orlandobassi/Documents/GitHub/TA.BA_DT_PROGR/Streamlit/pages/02_KI_Klassifizierung.py", line 290, in display_log
    level = log_entry['level']
            ~~~~~~~~~^^^^^^^^^


ValueError: The truth value of a DataFrame is ambiguous. Use a.empty, a.bool(), a.item(), a.any() or a.all().

File "/Users/orlandobassi/Documents/GitHub/TA.BA_DT_PROGR/Streamlit/streamlit_app.py", line 186, in `<module>`
    show_workflow_progress()
    ~~~~~~~~~~~~~~~~~~~~~~^^
File "/Users/orlandobassi/Documents/GitHub/TA.BA_DT_PROGR/Streamlit/streamlit_app.py", line 171, in show_workflow_progress
    completed = sum(1 for _, key in steps if key in st.session_state and st.session_state[key])
File "/Users/orlandobassi/Documents/GitHub/TA.BA_DT_PROGR/Streamlit/streamlit_app.py", line 171, in `<genexpr>`
    completed = sum(1 for _, key in steps if key in st.session_state and st.session_state[key])
                                                                         ~~~~~~~~~~~~~~~~^^^^^
File "/Users/orlandobassi/Documents/GitHub/TA.BA_DT_PROGR/.venv/lib/python3.13/site-packages/pandas/core/generic.py", line 1580, in __nonzero__
    raise ValueError(
    ...<2 lines>...
    )


IndentationError: File "/Users/orlandobassi/Documents/GitHub/TA.BA_DT_PROGR/Streamlit/pages/02_KI_Klassifizierung.py", line 530
          if uploaded_file:
         ^
IndentationError: unexpected indent

File "/Users/orlandobassi/Documents/GitHub/TA.BA_DT_PROGR/.venv/lib/python3.13/site-packages/streamlit/runtime/scriptrunner/exec_code.py", line 128, in exec_func_with_error_handling
    result = func()
File "/Users/orlandobassi/Documents/GitHub/TA.BA_DT_PROGR/.venv/lib/python3.13/site-packages/streamlit/runtime/scriptrunner/script_runner.py", line 667, in code_to_exec
    _mpa_v1(self._main_script_path)
    ~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^
File "/Users/orlandobassi/Documents/GitHub/TA.BA_DT_PROGR/.venv/lib/python3.13/site-packages/streamlit/runtime/scriptrunner/script_runner.py", line 165, in _mpa_v1
    page.run()
    ~~~~~~~~^^
File "/Users/orlandobassi/Documents/GitHub/TA.BA_DT_PROGR/.venv/lib/python3.13/site-packages/streamlit/navigation/page.py", line 296, in run
    code = ctx.pages_manager.get_page_script_byte_code(str(self._page))
File "/Users/orlandobassi/Documents/GitHub/TA.BA_DT_PROGR/.venv/lib/python3.13/site-packages/streamlit/runtime/pages_manager.py", line 160, in get_page_script_byte_code
    return self._script_cache.get_bytecode(script_path)
           ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^
File "/Users/orlandobassi/Documents/GitHub/TA.BA_DT_PROGR/.venv/lib/python3.13/site-packages/streamlit/runtime/scriptrunner/script_cache.py", line 72, in get_bytecode
    filebody = magic.add_magic(filebody, script_path)
File "/Users/orlandobassi/Documents/GitHub/TA.BA_DT_PROGR/.venv/lib/python3.13/site-packages/streamlit/runtime/scriptrunner/magic.py", line 45, in add_magic
    tree = ast.parse(code, script_path, "exec")
File "/Library/Frameworks/Python.framework/Versions/3.13/lib/python3.13/ast.py", line 50, in parse
    return compile(source, filename, mode, flags,
                   _feature_version=feature_version, optimize=optimize)
