import os
from pathlib import Path

# 定义需要过滤的文件夹模式
FILTERED_DIRS = ['.venv', '.DS_Store', '__pycache__', 'temp_*', '.git']
# 定义需要显示文件夹名但不展开内容的模式
FOLDER_ONLY = ['.venv*', 'config*', 'temp_*', '.git*']
# 定义需要显示文件名但不展开内容的模式
FILE_ONLY = ['temp*.py']

def should_skip(path: Path) -> bool:
    """检查路径是否应该被完全跳过"""
    name = path.name
    if path.is_dir():
        return any(pattern in FILTERED_DIRS and pattern in name for pattern in FILTERED_DIRS)
    return False

def is_folder_only(path: Path) -> bool:
    """检查路径是否是只显示文件夹名的文件夹"""
    name = path.name
    return path.is_dir() and any(pattern in FOLDER_ONLY and pattern in name for pattern in FOLDER_ONLY)

def is_file_only(path: Path) -> bool:
    """检查路径是否是只显示文件名的文件"""
    name = path.name
    return path.is_file() and any(pattern in FILE_ONLY and pattern in name for pattern in FILE_ONLY)

def generate_tree(path: str = '.', depth: int = 5, prefix: str = '') -> None:
    """
    生成指定路径的文件树，支持自定义过滤规则
    
    参数:
        path: 要生成文件树的目录路径，默认为当前目录
        depth: 树的最大深度，默认为5
        prefix: 用于缩进的前缀字符串，递归调用时使用
    """
    # 检查路径是否存在
    if not os.path.exists(path):
        print(f"错误: 路径 '{path}' 不存在")
        return
    
    # 获取目录内容并排序（文件夹优先，然后按名称排序）
    try:
        items = sorted(
            Path(path).iterdir(), 
            key=lambda x: (not x.is_dir(), str(x).lower())
        )
    except PermissionError:
        print(f"{prefix}└── {Path(path).name}/ (权限不足)")
        return
    
    # 遍历目录中的每个项目
    for index, item in enumerate(items):
        # 确定是否为最后一个项目
        is_last = index == len(items) - 1
        
        # 构建当前项目的前缀
        current_prefix = '└── ' if is_last else '├── '
        
        # 跳过需要过滤的项目
        if should_skip(item):
            continue
        
        # 处理只显示文件夹名的情况
        if is_folder_only(item):
            print(f"{prefix}{current_prefix}{item.name}/")
            continue
        
        # 处理只显示文件名的情况
        if is_file_only(item):
            print(f"{prefix}{current_prefix}{item.name}")
            continue
        
        # 打印当前项目
        if item.is_dir():
            print(f"{prefix}{current_prefix}{item.name}/")
        else:
            print(f"{prefix}{current_prefix}{item.name}")
        
        # 如果是目录且未达到最大深度，则递归生成子树
        if item.is_dir() and depth > 1:
            # 构建子目录的前缀
            child_prefix = '    ' if is_last else '│   '
            generate_tree(
                path=item, 
                depth=depth - 1, 
                prefix=prefix + child_prefix
            )

if __name__ == "__main__":
    print(f"当前目录文件树（深度=5，按规则过滤）:")
    print(f"{'=' * 40}")
    generate_tree()    