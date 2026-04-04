# 打包说明

由于网络限制，pyinstaller未能在2小时内安装成功。以下是手动打包步骤：

## 前置条件

- 已安装 Python 3.8+
- 可访问外网（或使用国内镜像源）

## 步骤

1. 安装依赖

```bash
pip install -r requirements.txt
```

如果速度慢，使用清华镜像：

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

2. 测试程序

```bash
python gui.py
```

3. 打包为exe

```bash
pyinstaller --onefile --name opensims_demo gui.py
```

4. 获取exe

```bash
dist/opensims_demo.exe
```

拷贝到任何Windows电脑即可运行（无需安装Python）。

---

## 打包选项

- `--onefile`：单文件模式
- `--windowed`：无控制台窗口（仅GUI）
- `--icon=app.ico`：添加图标

完整示例：

```bash
pyinstaller --onefile --windowed --name "OpenSims" gui.py
```