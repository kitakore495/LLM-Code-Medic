from typing import List, Dict, Set

def expand_target_files(
    target_files: List[str],
    export_table: Dict,
    call_graph: Dict = None,     # 新增参数
    import_graph: Dict = None,   # 新增参数
    symbol_index: Dict = None    # 新增参数
) -> List[str]:
    """
    全图谱感知版：根据底层 AST 的引用和依赖关系，自动把可能受连带影响的文件加入诊断范围。
    """
    result: Set[str] = set(target_files)
    changed = True

    while changed:
        changed = False
        
        # 1. 你原有的基于 export_table 的追溯逻辑（保持并兼容）
        for file_path, meta in export_table.items():
            imports = meta.get("imports", [])
            for imp in imports:
                module_file = imp.get("module_file")
                if module_file in result:
                    if file_path not in result:
                        result.add(file_path)
                        changed = True

        # 2. 扩展：利用额外的图谱进行关联（防漏网之鱼）
        # 如果 import_graph 记录了直接的显式依赖，且被依赖文件在范围内，则将依赖它的文件也加进来
        if import_graph:
            for file_path, deps in import_graph.items():
                # deps 通常是一个列表或字典，记录该文件依赖了谁
                for dep in deps:
                    # 如果依赖的文件在待修复列表里，但当前文件不在，就加进来
                    if dep in result and file_path not in result:
                        result.add(file_path)
                        changed = True

    return sorted(result)