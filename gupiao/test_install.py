"""
依赖安装测试脚本
"""
import subprocess
import sys

def install_package(package):
    """安装单个包"""
    try:
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', '--break-system-packages',
            package
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except:
        return False

# 安装核心依赖
print("正在安装核心依赖...")
packages = [
    'fastapi',
    'uvicorn',
    'sqlalchemy',
    'pydantic',
]

for pkg in packages:
    if install_package(pkg):
        print(f"✓ {pkg} 安装成功")
    else:
        print(f"✗ {pkg} 安装失败")

print("\n依赖安装完成！")
print("\n启动命令:")
print("python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
