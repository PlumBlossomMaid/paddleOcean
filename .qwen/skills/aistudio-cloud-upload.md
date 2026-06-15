# paddleOcean Skill — AI Studio Cloud 上传模块

`ocean/cli/cloud/upload.py` 提供了向百度 AI Studio 上传文件和文件夹的能力。

## 使用方式

```
/skill aistudio-cloud-upload
```

## CLI 用法

```bash
# 设置 token（首次）
set AISTUDIO_ACCESS_TOKEN=your_token

# 上传单文件
ocean cloud upload user/repo ./file.zip --repo-type dataset

# 上传文件夹
ocean cloud upload user/repo ./data_dir/ --repo-type dataset

# 指定目标路径和提交信息
ocean cloud upload user/repo ./file.zip --path-in-repo dir/file.zip --commit-message "my message"
```

## Python API

```python
from ocean.cloud import upload_file, upload_folder

upload_file("user/repo", "./file.zip", repo_type="dataset")
upload_folder("user/repo", "./data_dir/", repo_type="dataset")
```

## 架构要点

### 去 BCE SDK 依赖
- 不依赖 `baidubce` SDK（其 `put_super_obejct_from_file` 方法名有 typo）
- BOS 上传通过 `requests` 直接 HTTP PUT 到 pre-signed URL
- 文件 > 5GB 时使用 BOS REST API 实现 multipart 分片上传（含 BCE auth v1 签名）

### 上传流程
1. **LFS batch API** → 获取 pre-signed URL + STS token
   - 需要 Content-Type: `application/vnd.git-lfs+json`
   - 需要 Accept: `application/vnd.git-lfs+json`
2. **BOS 上传** → HTTP PUT 到 pre-signed URL（或 STS multipart）
3. **LFS 指针提交** → POST/PUT 到 Gitea contents API

### 关键设计决策
- 使用 `data=json.dumps(data)` 而非 `json=data`（避免 requests 覆盖 Content-Type）
- `_check_file_exists` 直接调 `requests.get` 而非通过 `_git_api`（404 是正常情况）
- LFS 指针提交与内容上传解耦（内容已存在时仍需提交指针）
- 线程池异常通过 `future.result()` 重新抛出，统一收集错误

### 彩虹进度条
```python
from ocean.utils.colored_tqdm import ColoredTqdm

with ColoredTqdm(total=file_size, unit="B", unit_scale=True, desc="  ☁️  file.zip") as pbar:
    ...
```

## 文件结构
```
ocean/cli/cloud/
├── __init__.py   # 注册 cloud CLI 命令组 + 导出 Python API
├── _config.py    # API 端点常量 + repo_id 校验
├── auth.py       # token 管理（环境变量 / 本地缓存文件）
├── upload.py     # 上传实现（核心）
├── download.py   # 下载文件
└── job.py        # 训练任务管理

ocean/utils/
└── colored_tqdm.py  # 彩虹渐变进度条
```
