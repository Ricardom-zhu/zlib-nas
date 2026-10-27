# zlib-nas

[English](README.md) · **中文**

一个跑在 NAS 上的、给自己用的 **Z-Library 账号网页客户端**。

它不是镜像站，也不托管任何内容：它只是用**你自己的账号**去调 Z-Library 的 EAPI，
把收藏夹同步进本地 SQLite，再用一条"额度守卫"队列把书稳稳地下载到你指定的文件夹。

```
┌─────────────┐   HTTPS    ┌──────────────┐   局域网   ┌────────────────┐
│   浏览器     │ ─────────► │  zlib-nas    │ ────────► │   你的书库目录   │
│  （局域网）   │            │  FastAPI     │   文件     │    NAS / 硬盘   │
└─────────────┘            └──────┬───────┘           └────────────────┘
                                  │ EAPI（HTTPS）
                                  ▼
                            Z-Library 镜像站
```

## 为什么做这个

现有的客户端要么是浏览器插件，要么是桌面软件，要么是 Telegram 机器人。书放在 NAS 上的
人用不上这些：想要的是书架在 NAS 上、下载在 NAS 上、文件直接落到阅读器已经扫描的那个
目录里。

zlib-nas 只做这一件事：

- **收藏夹优先。** 整个收藏夹同步进 SQLite，翻书架**不烧额度**；只有真正取文件时才消耗。
- **额度守卫。** 每个任务开始前先读剩余额度，用完了就整条队列暂停，而不是一条条地报错。
- **流式落盘。** 200 MB 的 PDF 分块写磁盘，绝不整本读进内存。
- **密码不落地。** 密码只在登录时用一次换回会话，磁盘上只留会话 Cookie（`0600` 权限）。
- **前端零构建。** 纯 HTML/CSS/JS，没有 npm、没有 CDN、没有打包步骤。

## 功能

| | |
|---|---|
| 收藏夹 | 一键同步、本地筛选、封面经服务端代理（NAS 连不上图床也能看） |
| 搜索 | 书名 / 作者 / ISBN，语言与格式筛选，翻页 |
| 下载 | 服务端队列、实时进度、失败重试、一键继续 |
| 本地库 | 列出磁盘上真实存在的文件，可直接下载 |
| 设置 | 镜像域名、密码登录**或**粘贴 Cookie 登录、退出 |
| 运维 | `/api/status` 健康检查、`/api/export` 导出 JSON、双语界面 |

## 快速开始

```bash
git clone https://github.com/<你的名字>/zlib-nas.git
cd zlib-nas
cp .env.example .env          # 可选：预先填好镜像域名
docker compose up -d --build
```

打开 `http://<NAS的IP>:8101` → **设置** → 填镜像域名（如 `zh.pirate101.ru`，不要带
`https://`）→ 登录 → 点 **同步收藏**。

不用 Docker：

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
DATA_DIR=./data uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 配置项

全部可选，留空的话在网页里填也一样。

| 变量 | 默认 | 说明 |
|---|---|---|
| `ZLIB_DOMAIN` | — | 镜像域名，不带协议头。网页里也能改。 |
| `ZLIB_EMAIL` / `ZLIB_PASSWORD` | — | 自动登录用。密码只用一次，不存储。 |
| `PROXY` | — | 访问镜像站和下载 CDN 的 HTTP 代理，如 `http://192.168.1.10:7890`。 |
| `DATA_DIR` | `/app/data` | 数据库、会话 Cookie、下载文件都在这。 |
| `DOWNLOAD_DIR` | `$DATA_DIR/downloads` | 书下载到哪。 |
| `MIRROR_DIR` | — | 可选。下载完的书在这里建软链，方便别的工具扫描入库，不占双份空间。 |
| `QUOTA_RESERVE` | `0` | 剩余额度低于这个值就暂停队列。填 `2` 可以留点余量。 |
| `MAX_CONCURRENT` | `1` | 并发下载数。**建议保持 1**，瓶颈是额度不是带宽。 |

## 和别的书库软件配合

如果已经有软件在扫描某个目录，把 `MIRROR_DIR` 指向它即可。下载完成后会在那里建一个
软链接，文件立刻出现在它的书库里，而真实文件仍在 `DOWNLOAD_DIR`，不重复占空间。

## 接口

所有接口都在 `/api` 下的 JSON。交互式文档：`/api/docs`。

| 方法 | 路径 | 用途 |
|---|---|---|
| `GET` | `/api/status` | 会话状态、额度、队列状态、计数 |
| `POST` | `/api/login` | `{domain, email, password}` 或 `{domain, cookies:{...}}` |
| `POST` | `/api/logout` | 删除已保存的会话 |
| `POST` | `/api/sync/saved` | 把整个收藏夹同步进 SQLite |
| `GET` | `/api/saved?q=&limit=&offset=` | 查询本地收藏夹 |
| `POST` | `/api/search` | `{query, page, limit, languages[], extensions[], year_from, year_to, order}` |
| `POST` | `/api/download` | `{id, hash, title, author, extension}` |
| `GET` | `/api/downloads` | 下载记录与进度 |
| `POST` | `/api/downloads/{id}/retry` | 重试失败任务 |
| `POST` | `/api/queue/pause` · `/api/queue/resume` | 暂停 / 继续队列 |
| `GET` | `/api/library` · `/api/library/{name}` | 列出 / 下载磁盘上的文件 |
| `GET` | `/api/cover?u=<url>` | 服务端代理封面图 |
| `GET` | `/api/export` | 导出整库 JSON |

## 安全须知

这是**局域网工具**，下面几条请务必读完：

- 它**本身没有任何用户认证**。谁能访问这个端口，谁就能用你的 Z-Library 会话。不要暴露
  到公网；需要远程访问请走 VPN，或在前面加一层带认证的反向代理。
- `data/session.json` 里是能直接登录你账号的 Cookie，文件权限已设为 `0600`，数据目录也要
  保护好。
- 密码不会被保存。不想发送密码的话，用 Cookie 登录：登录状态的浏览器里复制
  `remix_userid` 和 `remix_userkey` 两项即可。
- 下载下来的书请仅作个人使用，并遵守你所在地的法律。

## 已知限制

- 单账号、单用户，不做多用户，这是设计取舍。
- 镜像域名会变。如果接口开始返回 HTML 而不是 JSON，去设置里更新域名。
- `MAX_CONCURRENT > 1` 在额度边界情况下没有完整验证过，队列是按 1 并发设计的。
- 镜像可用性、额度规则、接口字段都在本项目控制之外，上游一改就可能失效，等客户端跟进。

## 项目结构

```
app/config.py      环境变量与路径
app/store.py       SQLite 建表与查询
app/zlibrary.py    EAPI 客户端（登录、收藏、搜索、额度、流式下载）
app/queue.py       额度守卫工作线程 + 文件名清洗
app/main.py        FastAPI 路由 + 静态文件挂载
static/            index.html、style.css、app.js（无需构建）
```

整个状态就是 `data/zlib-nas.db`，备份直接拷这个文件。

```bash
python -c "import app.main"     # 导入自检
curl -s localhost:8101/api/status | jq
python tests/test_offline.py    # 完整测试，不需要联网
```

`tests/test_offline.py` 会起一个模拟镜像站，按同样的 EAPI 格式应答，然后驱动真实的
客户端、存储和队列跑一遍：登录、收藏同步、搜索、额度守卫、流式下载、导出。所以贡献者
不用真账号也能验证改动，CI 每次推送都会跑。

## 许可

MIT。与 Z-Library 官方无关。见 [LICENSE](LICENSE)。
