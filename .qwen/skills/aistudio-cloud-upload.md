# paddleOcean Skill — AI Studio Cloud SDK

向百度 AI Studio 上传/下载文件、管理训练任务。不依赖官方 `aistudio-sdk` 包。

## 使用方式

```
/skill aistudio-cloud-upload
```

---

## 文件结构

```
ocean/cli/cloud/
├── __init__.py   注册 cloud CLI 命令组 + 导出公共 Python API
├── _config.py    API 端点常量 + repo_id 校验
├── auth.py       token 管理（环境变量 AISTUDIO_ACCESS_TOKEN / 本地缓存 ~/.cache/ocean/.auth/token）
├── upload.py     上传实现（核心，含 BOS 直传 / multipart）
├── download.py   下载文件（单文件 + 整仓列表）
└── job.py        训练任务管理（submit / list / stop）
ocean/cloud.py    简化的公共导入入口（from ocean.cloud import upload_file）
ocean/utils/colored_tqdm.py  彩虹渐变进度条
```

## CLI 命令

```bash
# 登录（保存 token，一次设置永久有效）
ocean cloud login --token <your_token>

# 上传单文件/文件夹
ocean cloud upload user/repo ./file.zip --repo-type dataset
ocean cloud upload user/repo ./data_dir/ --repo-type model
ocean cloud upload user/repo ./file.zip --path-in-repo dir/file.zip --commit-message "msg"

# 下载
ocean cloud download user/repo ./path/in/repo --local-dir ./
ocean cloud download user/repo  # 下载全部文件

# 训练任务
ocean cloud job submit --name my_job --cmd "python train.py" --path ./
ocean cloud job list
ocean cloud job stop <job_id>
```

## Python API

```python
from ocean.cloud import upload_file, upload_folder, download_file

# token 自动从环境变量 AISTUDIO_ACCESS_TOKEN 或 login 缓存读取
upload_file("user/repo", "./file.zip", repo_type="dataset")
upload_folder("user/repo", "./data/", repo_type="dataset")
download_file("user/repo", "model.pdparams", local_dir="./")
```

## 上传架构详解

### 整体流程（三步走）

```
upload_file() → upload_folder()
  └─ _upload_item()              判断走 LFS 还是普通上传
       ├─ LFS (≥5MB) ──→ _lfs_upload_file()
       │    1. SHA256 计算（ColoredTqdm 进度条）
       │    2. LFS batch API  → 获取 STS token + pre-signed URL
       │    3. BOS 上传       → HTTP PUT 或 multipart（ColoredTqdm 进度条）
       │    4. 指针提交       → POST/PUT Gitea contents API
       └─ Normal (<5MB) → _regular_upload_file()
            1. base64 编码
            2. POST/PUT Gitea contents API
```

### 关键设计决策

| 决策 | 原因 |
|------|------|
| 不依赖 `baidubce` SDK | BCE SDK 方法名 `put_super_obejct_from_file` 有 typo |
| 用 `data=json.dumps(data)` 而非 `json=data` | 避免 `requests` 覆盖自定义 Content-Type 头 |
| `_check_file_exists` 直接调 `requests.get` | 404 是「文件不存在」的正常情况，不是错误 |
| LFS 指针提交与内容上传解耦 | 内容 hash 已在 BOS 存在时仍需提交指针到仓库 |
| `future.result()` 收集异常 | 防止线程池异常被静默吞没 |

### 两点必须牢记

**1. LFS batch API 的 Content-Type**

```python
headers = {
    "Content-Type": "application/vnd.git-lfs+json",   # 必须
    "Accept": "application/vnd.git-lfs+json",          # 也必须！
}
```
漏掉 Accept 头会返回 `415 Unsupported Media Type`。

**2. LFS 指针必须提交，哪怕内容已存在**

LFS batch API 返回 `actions: {}` 时表示内容 hash 已在远程 LFS 存储。此时**仍需要**提交指针文件到 Gitea，否则文件在网页上不可见。

### BOS REST API（>5GB 需 multipart）

当文件 >5GB 时使用 `BosRestClient`，通过原始 REST 请求实现分片上传：

1. `POST /{bucket}/{key}?uploads` → 获取 uploadId
2. `PUT /{bucket}/{key}?partNumber=N&uploadId=ID` → 并行传分片
3. `POST /{bucket}/{key}?uploadId=ID` → 传完 complete
4. `DELETE /{bucket}/{key}?uploadId=ID` → 失败时 abort

BCE auth v1 签名算法在 `_bce_sign()` 中自实现。

### 彩虹进度条

```python
from ocean.utils.colored_tqdm import ColoredTqdm

with ColoredTqdm(total=file_size, unit="B", unit_scale=True,
                 desc="  ☁️  file.zip", leave=False) as pbar:
    pbar.update(chunk_size)
```

颜色从粉色 (`#DDA0A0`) 渐变到绿色 (`#A0DDA0`)，进度越高越绿。
