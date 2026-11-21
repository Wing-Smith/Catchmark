# WN-PBR Benchmark Suite 项目文档

> **版本**: 1.3.0 (Custom)  
> **作者**: Wing North Studio  
> **最后更新**: 2026-08-08

---

## 目录

1. [项目概述](#1-项目概述)
2. [系统架构](#2-系统架构)
3. [核心组件](#3-核心组件)
   - 3.1 [Benchmark 引擎 (SSNGG)](#31-benchmark-引擎-ssngg)
   - 3.2 [Benchmark Viewer (TTESGG)](#32-benchmark-viewer-ttesgg)
   - 3.3 [Decryptor (DDSGG)](#33-decryptor-ddsgg)
4. [客制化测试模式](#4-客制化测试模式)
5. [安装与部署](#5-安装与部署)
   - 5.1 [Inno Setup 安装包](#51-inno-setup-安装包)
   - 5.2 [自动打包脚本](#52-自动打包脚本)
6. [文件格式与关联](#6-文件格式与关联)
7. [安全设计](#7-安全设计)
8. [未来方向](#8-未来方向)
9. [附录](#9-附录)

---

## 1. 项目概述

WN-PBR Benchmark Suite 是一套面向 Python 运行环境的综合性能基准测试工具，由 Wing North Studio 开发。项目名称 **WN-PBR** 取自 **W**ing **N**orth **P**ython **B**enchma**R**k 的缩写。

项目核心目标是为 Python 开发者、硬件评测爱好者提供一个标准化、可对比的跨平台性能测试方案。测试结果以加密格式（`.wnpbr`）存储，通过配套的 Viewer 程序进行可视化展示，支持本地查看、手动编辑和格式转换。

### 主要特性

- **四模式测试**：
  - **经典三项**：大整数累加 / 矩阵乘法 / JSON 混合负载
  - **Neo 扩展六项**：经典三项 + 素数筛 / 字符串处理 / 字典运算
  - **Gen2 全面十项**：Neo 六项 + 内存带宽 / 列表操作 / I/O 吞吐 + GIL 并发
  - **客制化模式**：自选测试项目组合，动态权重计算
- **加密结果文件**：采用偏移量加密（Offset = 7350），防止结果篡改，同时支持解密查看
- **现代化 GUI**：基于 tkinter 的 Win11 风格界面，支持 DWM 毛玻璃效果、圆角卡片、明暗主题切换
- **多语言安装**：Inno Setup 安装包支持简体中文与英文，带 EULA 与序列号验证
- **文件关联**：`.wnpbr` 文件自动关联到 Viewer，双击即可打开
- **独立文件图标**：为 `.wnpbr` 文件类型定制了专属图标（16×16 / 32×32 / 48×48 / 64×64 / 128×128 / 256×256 六尺寸 ICO）

---

## 2. 系统架构

```
WN-PBR Benchmark Suite
├── SSNGG.py          # 基准测试引擎（控制台）v1.3.0
├── TTESGG.py         # 结果查看器（GUI）v1.2.0
├── DDSGG.py          # 解密工具（GUI）
├── Build_WN-PBR.ps1  # PowerShell 自动打包脚本
├── Build_WN-PBR.cmd  # CMD 自动打包脚本（备份）
├── make_ico.py       # 文件图标生成工具
├── Assets/
│   ├── WN-PBR_File.ico          # .wnpbr 文件类型图标
│   ├── Benchmark_Viewer.png     # Viewer 程序图标
│   ├── Decryptor.png            # Decryptor 程序图标
│   ├── Benchmark_Logo.ico       # Benchmark 程序图标
│   ├── Benchmark_Viewer_Logo.ico
│   ├── Decryptor_Logo.ico
│   └── SetupIcon.ico
├── Release/          # 编译输出目录
│   ├── WN-PBR Benchmark.exe
│   ├── WN-PBR Viewer.exe
│   └── WN-PBR Decryptor.exe
└── WN-PBR-Setup-1.3.0.iss  # Inno Setup 安装脚本
```

---

## 3. 核心组件

### 3.1 Benchmark 引擎 (SSNGG)

**定位**：核心测试程序，控制台应用，负责执行所有性能测试并生成加密的 `.wnpbr` 结果文件。

**测试项目**

| 序号 | 测试项 | 规模 | Gen2 权重 | 分组 | 说明 |
|------|--------|------|-----------|------|------|
| 1 | 大整数累加 | 斐波那契第 10,000,000 项 | 20% | classic | 测试 Python 大整数运算与多进程性能 |
| 2 | 矩阵乘法 | 512 × 512 双精度浮点 | 15% | classic | 测试纯 Python 浮点运算与内存访问 |
| 3 | JSON 混合负载 | 200,000 条记录 | 10% | classic | 测试序列化、哈希与字符串操作 |
| 4 | 素数筛 | 10,000,000 埃拉托斯特尼筛法 | 15% | neo | 整数运算与内存访问 |
| 5 | 字符串处理 | 100,000 条正则匹配 | 10% | neo | 字符串与正则性能 |
| 6 | 字典运算 | 500,000 次插入/查找/排序 | 10% | neo | 哈希表与排序性能 |
| 7 | 内存带宽 | 50MB bytearray 读写 + 对象分配 | 10% | gen2 | 内存分配与连续读写 |
| 8 | 列表操作 | 500,000 次追加/排序/插入/切片 | 5% | gen2 | 列表综合操作 |
| 9 | I/O 吞吐 | 1MB 二进制 + 10,000 行文本读写 | 5% | gen2 | 文件顺序读写 |
| 10 | GIL 并发 | 1,000,000 次哈希计算 | — | gen2 | 多线程加速比（不计入总分） |

**评分体系**

每项测试以基准耗时为参照，计算单项得分（`基准耗时 / 实际耗时 × 1000`），再按权重加权得到综合得分。基准值基于参考硬件标定，确保跨平台可比性。

- **经典模式**：固定权重（40% / 30% / 30%）
- **Neo 模式**：经典权重不变，新增项固定权重（40% / 30% / 30%），Neo 综合与经典综合独立计算
- **Gen2 模式**：九项加权（见上表），GIL 并发仅作参考展示
- **客制化模式**：用户自选项目，权重按所选项目的 Gen2 原始权重归一化动态计算

**命令行参数**

```bash
WN-PBR Benchmark.exe [选项]
  --classic         直接启动经典测试
  --neo             直接启动 Neo 扩展测试
  --gen2            直接启动 Gen2 全面测试
  --custom          直接启动客制化测试（自选项目）
  --output, -o      指定结果文件保存路径
  --plain           同时输出未加密的 JSON（调试）
  --silent, -s      静默模式（无彩色输出、无通知）
  --no-progress     禁用进度条
  --no-notify       禁用 Windows Toast 通知
```

**Windows 通知**

测试完成后通过 `win11toast`（优先）或 `win10toast` 发送 Toast 通知，显示测试模式与综合得分。通知发送者显示为 **"Wing North Software"**，使用 `Benchmark_Logo.ico` 作为通知图标。

---

### 3.2 Benchmark Viewer (TTESGG)

**定位**：结果可视化工具，GUI 应用，用于查看、编辑和生成 `.wnpbr` 加密结果文件。

**功能模块**

1. **结果面板（Dashboard）**
   - 加载 `.wnpbr` 文件后自动解密并以卡片式布局展示
   - 支持四种布局自适应切换：经典版（3 项）、Neo 版（6 项）、Gen2 版（10 项）、客制化版（动态）
   - 综合评分使用大字号高亮显示
   - 客制化模式下显示"客制化综合评分"大卡片，未执行的测试项显示为 `-`

2. **制作结果（Editor）**
   - 手动填写或修改测试数据，自动生成单项得分与综合得分
   - 支持经典版 / Neo 版 / Gen2 版 / 客制化版 四种模式切换
   - 系统信息（CPU / Python 版本 / 核心数）自动填充
   - 生成加密文件前需输入密码验证（`mxt20060818`）
   - 支持加载已有文件作为模板修改后重新生成
   - 客制化模式下，综合得分根据已填写的项目动态归一化计算

3. **转换工具（Convert）**
   - 旧版本未加密 `.wnpbr` 文件转换为新版加密格式
   - 纯文本跑分结果自动解析并生成标准加密文件

**界面特性**

- Win11 DWM 毛玻璃效果（标题栏与窗口边框）
- 圆角卡片（Canvas 绘制，16px 圆角）
- 明暗主题一键切换（全局配色同步更新）
- 鼠标滚轮支持（结果面板与制作结果页均可滚动）
- 自定义 DPI 感知（`SetProcessDpiAwareness`）

**命令行参数支持**

Viewer 支持通过命令行参数接收 `.wnpbr` 文件路径，实现双击文件自动打开：
```bash
WN-PBR Viewer.exe "C:\Users\...\Result.wnpbr"
```

---

### 3.3 Decryptor (DDSGG)

**定位**：轻量级解密工具，GUI 应用，用于将 `.wnpbr` 加密文件解密为可读的 JSON 文本。

**功能**

- 选择 `.wnpbr` 文件，实时解密并显示格式化 JSON
- 支持将解密后的 JSON 保存到本地
- 明暗主题切换
- 同样支持命令行参数自动加载文件

**设计哲学**

Decryptor 作为 Viewer 的补充工具，面向需要查看原始数据结构的高级用户。程序本身不连接网络，不访问任何外部服务，确保数据处理的完全本地化和安全性。

---

## 4. 客制化测试模式

客制化测试（Custom Mode）是 v1.3.0 引入的全新功能，允许用户像"自选餐"一样自由组合测试项目，程序根据所选项目动态执行并计算归一化权重得分。

### 4.1 使用方式

启动 Benchmark 引擎后选择 `[5] 客制化测试`，或在命令行使用 `--custom` 参数直接启动。

**交互式选择界面示例**：

```
============================================================
         客 制 化 测 试 项 目 选 择
============================================================
  请勾选要测试的项目（输入编号，用空格分隔）:

  [1] 大整数累加     斐波那契第 10,000,000 项
  [2] 矩阵乘法       512 x 512 浮点矩阵
  [3] JSON 混合负载  200,000 条记录
  [4] 素数筛         埃拉托斯特尼筛法 10,000,000
  [5] 字符串处理     100,000 条正则匹配
  [6] 字典运算       500,000 次插入/查找/排序
  [7] 内存带宽       50MB bytearray 读写 + 对象分配
  [8] 列表操作       500,000 次追加/排序/插入/切片
  [9] I/O 吞吐       1MB 二进制 + 10,000 行文本读写

  [G] GIL 并发       CPU 密集型多线程加速比测试（不计入总分）

  示例: 1 2 4 7  G

  输入选项: 1 3 5 7 9
```

### 4.2 权重归一化机制

客制化模式不采用固定权重，而是基于 Gen2 原始权重进行动态归一化：

1. 用户选择若干测试项（至少 1 项）
2. 提取每项在 Gen2 中的原始权重
3. 将原始权重按比例缩放，使总和为 100%
4. 按归一化后的权重计算综合得分

**示例**：若用户选择"大整数（20%）+ 素数筛（15%）+ 内存带宽（10%）"，则归一化后权重为：
- 大整数：20 / 45 = **44%**
- 素数筛：15 / 45 = **33%**
- 内存带宽：10 / 45 = **22%**

### 4.3 结果文件结构

客制化模式的结果文件包含以下特有字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `mode` | string | 固定为 `"custom"` |
| `custom_mode` | bool | `true` |
| `custom_items` | array | 用户选择的测试项 key 列表 |
| `custom_weights` | object | 每项的归一化权重（保留 4 位小数） |
| `custom_total_score` | int | 客制化综合得分 |

### 4.4 GIL 并发附加项

GIL 并发测试（`[G]`）作为可选附加项，**不计入综合得分**，仅在报告中独立展示加速比与并发效率。适合需要评估 Python GIL 对多线程性能影响的用户。

---

## 5. 安装与部署

### 5.1 Inno Setup 安装包

**安装模式**

| 模式 | 包含组件 | 序列号要求 |
|------|----------|-----------|
| 完整安装 | Benchmark + Viewer + Decryptor | Viewer / Decryptor 需序列号 |
| 最小安装 | Benchmark 仅 | 无 |
| 自定义安装 | 用户自选 | 视组件而定 |

**序列号系统**

采用 Gen1 自定义校验算法：
- 25 位字符（5 组 × 5 位），去除易混淆字符（0, 1, I, O）
- 第 1 位：世代标识（固定为 `2`，即 Gen1）
- 第 2 位：授权类型（`V`=Viewer, `D`=Decryptor, `A`=全能）
- 第 3–20 位：随机载荷
- 第 21–25 位：基于前 20 位的校验和（自定义哈希算法）

安装时序列号写入注册表 `HKLM\Software\WN-PBR\Licenses`，卸载时自动清理。已授权用户重新安装对应组件时自动跳过序列号输入。

**文件关联**

安装 Viewer 或 Decryptor 时自动注册 `.wnpbr` 文件扩展名：
- 默认图标：`WN-PBR_File.ico`（独立文件图标，非程序图标）
- 默认打开方式：WN-PBR Viewer（优先）
- 卸载时自动清理注册表关联

**EULA**

使用 RTF 格式许可证文件（`license_zh.rtf` / `license_en.rtf`），支持字体大小、加粗、颜色控制，随安装语言自动切换。

---

### 5.2 自动打包脚本

**PowerShell 脚本 (`Build_WN-PBR.ps1`)**

- 自动解析 `python313` 真实路径（支持别名、py 启动器、python 回退）
- 每个组件在独立子进程中编译，彻底隔离 Nuitka 缓存
- 编译前自动清理 `build`、`onefilebuild`、`*.{src}.build`、`*.{src}.onefile-build` 等残留目录
- 编译后自动刷新 Windows 图标缓存（`ie4uinit.exe -show`）

**Nuitka 编译配置**

| 组件 | 类型 | 特殊参数 |
|------|------|----------|
| Benchmark | 控制台 | `--windows-console-mode=disable` 未启用（保留控制台） |
| Viewer | GUI | `--windows-console-mode=disable --enable-plugin=tk-inter --include-data-files=Benchmark_Viewer.png` |
| Decryptor | GUI | `--windows-console-mode=disable --enable-plugin=tk-inter --include-data-files=Decryptor.png` |

**CMD 脚本 (`Build_WN-PBR.cmd`)**

作为 PowerShell 脚本的备份方案，功能完全一致，使用 `call :CleanNuitkaCache` 子程序清理缓存，通过 `for /d` 循环匹配并删除临时目录。

---

## 6. 文件格式与关联

### `.wnpbr` 文件格式

`.wnpbr` 是 WN-PBR 的专用结果文件格式，本质为 **JSON 文本经偏移量加密后的字符串**。

**加密算法**
```python
OFFSET = 7350

def encrypt(text):
    return "".join(chr(ord(c) + OFFSET) for c in text)

def decrypt(text):
    return "".join(chr(ord(c) - OFFSET) for c in text)
```

**JSON 数据结构 — 经典模式**
```json
{
  "cpu": "Intel(R) Core(TM) Ultra 9 285H",
  "python": "3.14.6",
  "cores": 16,
  "timestamp": "2026-08-04 16:44:11",
  "mode": "classic",
  "fib_time": 77.384,
  "fib_digits": 2089876,
  "fib_score": 3877,
  "mat_time": 4.728,
  "mat_gflops": 0.057,
  "mat_checksum": 4061.2434,
  "mat_score": 1057,
  "json_time": 0.432,
  "json_size_mb": 23.86,
  "json_sha16": "2dcc9551eeb9d7bc",
  "json_score": 1158,
  "classic_total_score": 26988
}
```

**JSON 数据结构 — 客制化模式**
```json
{
  "cpu": "Intel(R) Core(TM) Ultra 9 285H",
  "python": "3.14.6",
  "cores": 16,
  "timestamp": "2026-08-08 18:30:00",
  "mode": "custom",
  "custom_mode": true,
  "custom_items": ["fib_10m", "prime_10m", "memory_50m"],
  "custom_weights": {
    "fib_10m": 0.4444,
    "prime_10m": 0.3333,
    "memory_50m": 0.2222
  },
  "custom_total_score": 15234,
  "fib_time": 77.384,
  "fib_digits": 2089876,
  "fib_score": 3877,
  "prime_time": 0.045,
  "prime_count": 664579,
  "prime_score": 55556,
  "memory_time": 0.312,
  "memory_bandwidth": 320.5,
  "memory_score": 961
}
```

### 文件图标

为 `.wnpbr` 文件类型独立设计了六尺寸 ICO 图标（16/32/48/64/128/256），采用蓝色文档折角风格，中心放置 WN-PBR 品牌标识，与程序图标明确区分。

---

## 7. 安全设计

**结果加密**
- 偏移量加密虽非密码学安全，但足以防止普通用户直接篡改文本结果
- 加密密钥（OFFSET = 7350）仅在源码中出现一次，编译后难以直接提取

**序列号验证**
- 客户端校验算法，无网络验证依赖
- 校验和基于自定义哈希，增加逆向难度
- 授权信息写入注册表，重装时自动识别

**密码保护**
- Viewer 的"制作结果"功能生成加密文件前需输入密码（`mxt20060818`），防止误操作或未经授权的结果伪造

**网络隔离**
- Decryptor 完全不访问网络
- Viewer 当前版本无网络功能（未来联网功能为可选扩展）
- Benchmark 引擎仅支持本地通知（Toast），无网络上传

---

## 8. 未来方向

### 8.1 联网数据库与排行榜（TinyWebDB）

**目标**：建立在线跑分排行榜，实现用户测试结果的云端共享与对比。

**技术方案**
- **当前阶段**：使用 `https://tinywebdb.appinventor.space/` 公网服务作为原型验证
- **后续阶段**：迁移至同学树莓派自建 TinyWebDB 服务端（内网或公网穿透）

**数据结构设计**

采用 TinyWebDB 键值对存储，通过 tag 前缀实现命名空间隔离：

| Tag 前缀 | 用途 | 读写权限 |
|----------|------|----------|
| `wnpbr_leaderboard_` | 跑分排行榜条目 | Benchmark 写，Viewer 读 |
| `wnpbr_announcement` | 系统公告 / 版本更新 | 管理员写，全员读 |
| `wnpbr_version_latest` | 最新版本号 | 管理员写，Benchmark 启动时读 |
| `wnpbr_meta_` | 统计元数据 | Viewer 读 |

**客户端权限约束**
- **Benchmark**：仅封装 `update` 调用，上传跑分结果（只写）
- **Viewer**：封装 `get` / `search`，拉取排行榜与公告（只读），可选支持手动上传/修正记录
- **Decryptor**：完全不引入网络相关代码（无访问权限）

**安全考量**
- TinyWebDB 默认实例数据公开，不存储敏感信息（真实姓名、精确地理位置）
- 客户端权限为逻辑约束，非服务端鉴权（小众工具可接受的风险）
- 自建服务后可更换 `user` / `secret`，并增加离线回退（网络异常时静默失败，不影响本地功能）

**树莓派部署**
- 服务端选用 `tinywebdb-php`（Apache/Nginx + PHP，无需 MySQL）
- 内存占用 < 50MB，远低于 Minecraft 服务器
- 数据目录建议映射至外接存储（SD 卡寿命考虑）
- 内网穿透可用 frp/ngrok，或利用校园网公网 IP

### 8.2 通知系统增强

**Windows Toast 优化**
- 当前已实现：发送者名称 "Wing North Software"、自定义图标
- 未来可探索：通过注册表 AUMID 注册，实现通知标题栏左上角应用图标（需 MSIX 或注册表 `AppUserModelId` 映射，复杂度较高，优先级低）

### 8.3 安装包优化

- 考虑为 `.wnpbr` 文件添加右键菜单"用 Decryptor 打开"选项（作为 Viewer 的备用）
- 安装程序数字签名（需购买代码签名证书）
- 自动更新检测（基于 TinyWebDB 的 `wnpbr_version_latest` 标签）

### 8.4 测试项扩展

- 增加 NumPy / Pandas 专项测试（可选依赖）
- 增加多线程 / asyncio 并发测试
- 增加内存带宽测试（`bytearray` 大规模操作）—— **已在 Gen2 中实现**

### 8.5 跨平台支持

- 当前 Windows 为主平台（DWM、Toast、wmic 等）
- Linux / macOS 适配：CPU 型号获取改用 `lscpu` / `sysctl`，通知改用 `notify2` / `pync`
- 打包方案：Linux 用 PyInstaller + AppImage，macOS 用 PyInstaller + `.app` Bundle

---

## 9. 附录

### 9.1 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0.0 | — | 初始版本，经典三项测试 |
| 1.1.0 | 2026-08-04 | 新增 Neo 扩展测试（素数筛 / 字符串 / 字典） |
| 1.1.1 | 2026-08-04 | Viewer 制作结果页底部按钮改为紧凑卡片条 |
| 1.1.2 | 2026-08-04 | 修复全局鼠标滚轮支持 |
| 1.1.3 | 2026-08-05 | Benchmark Toast 通知改为 "Wing North Software" + 自定义图标 |
| 1.1.4 | 2026-08-08 | 新增 `.wnpbr` 文件类型独立图标；Viewer/Decryptor 支持命令行参数自动加载文件 |
| 1.2.0 | 2026-08-08 | 新增 Gen2 全面测试（内存带宽 / 列表操作 / I/O 吞吐 / GIL 并发）；九项加权评分体系 |
| 1.3.0 | 2026-08-08 | **新增客制化测试模式**：自选测试项目组合，动态权重归一化计算；Viewer 与 Editor 全面支持 Custom 模式 |

### 9.2 依赖清单

**运行时依赖**
- Python 3.13+
- `win11toast`（可选，Win11 通知）
- `win10toast`（可选，Win10 通知）
- `Pillow`（可选，图标加载回退）

**编译依赖**
- Nuitka（`python -m nuitka`）
- Inno Setup 6（安装包制作）
- Pillow（ICO 图标生成）

### 9.3 项目仓库结构建议

```
wnpbr-suite/
├── src/
│   ├── SSNGG.py              # v1.3.0 - 含 Custom 模式
│   ├── TTESGG.py             # v1.2.0 - 含 Custom 布局与编辑器
│   └── DDSGG.py              # 无变更
├── scripts/
│   ├── Build_WN-PBR.ps1
│   ├── Build_WN-PBR.cmd
│   └── make_ico.py
├── setup/
│   ├── WN-PBR-Setup-1.3.0.iss
│   ├── license_zh.rtf
│   └── license_en.rtf
├── assets/
│   ├── icons/
│   │   ├── WN-PBR_File.ico
│   │   ├── Benchmark_Logo.ico
│   │   ├── Benchmark_Viewer_Logo.ico
│   │   └── Decryptor_Logo.ico
│   └── images/
│       ├── Benchmark_Viewer.png
│       └── Decryptor.png
├── docs/
│   └── WN-PBR_Documentation.md
└── release/
```

### 9.4 许可证

WN-PBR Benchmark Suite 由 Wing North Studio 开发，最终解释权归作者所有。未经授权不得用于商业用途或二次分发。

---

*文档结束*