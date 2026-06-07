from typing import List, Dict, Set


def expand_target_files(
    target_files,
    export_table,
    call_graph=None,
    import_graph=None,
    symbol_index=None
):
    result = set(target_files)

    changed = True

    while changed:
        changed = False

        #
        # ImportGraph 反向扩散
        #
        if import_graph:
            for file_path, deps in import_graph.items():

                if any(dep in result for dep in deps):

                    if file_path not in result:
                        result.add(file_path)
                        changed = True

        #
        # CallGraph 反向扩散
        #
        if call_graph:
            for caller, callees in call_graph.items():

                if any(callee in result for callee in callees):

                    if caller not in result:
                        result.add(caller)
                        changed = True

    return sorted(result)