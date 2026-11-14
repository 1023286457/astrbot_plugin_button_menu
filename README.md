<div align="center">

> **AstrBot· 可视化按钮面板**

# 🧰 QQ官机按钮菜单

**QQ官机菜单面板插件：在 WebUI 可视化配置 `/Astrbot菜单` 的按钮、发送文字/图片/链接、分页布局、生效机器人与分页预览。**

[![版本 1.0.0](https://img.shields.io/badge/版本-1.0.0-89b4fa.svg)](CHANGELOG.md)
[![License: CC BY-NC-ND 4.0](https://img.shields.io/badge/License-CC%20BY--NC--ND%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-nd/4.0/)
[![作者 简单么么熊](https://img.shields.io/badge/作者-简单么么熊-f5b7c7.svg)](https://github.com/1023286457)
[![QQ群 1081896895](https://img.shields.io/badge/QQ群-1081896895-12B7F5.svg)](https://qm.qq.com/q/LWmwpA9kuk)

<img src="https://count.getloli.com/@1023286457_button_menu?name=1023286457_button_menu&amp;theme=green&amp;padding=7&amp;offset=0&amp;align=top&amp;scale=1&amp;pixelated=1&amp;darkmode=auto" alt="访问计数" />

[功能总览](#overview) · [安装](#install) · [WebUI](#webui) · [指令](#commands) · [按钮配置](#buttons) · [分页布局](#pagination) · [生效机器人](#bots) · [常见问题](#faq) · [更新日志](CHANGELOG.md)

</div>

---

<a id="overview"></a>

## 🧭 功能总览

把 `/Astrbot菜单` 做成一整套可以在 WebUI 里配置的 QQ 官方按钮面板。按钮点击使用 QQ 原生回调，由插件直接发送配置的内容，不需要用户再手动发指令。

| | 能力 | 说明 |
| --- | --- | --- |
| 🧩 | **按钮菜单** | `/Astrbot菜单` 发送按钮面板，支持多页翻页 |
| 🎛️ | **WebUI 配置** | 标题、副标题、底部提示、按钮文字、按钮说明全部可视化编辑 |
| 💬 | **发送文字** | 点击按钮直接发送配置的文本 |
| 🖼️ | **发送图片** | 在 WebUI 上传 PNG/JPG，点击按钮直接发图 |
| 🔗 | **发送链接** | 点击按钮发送“按钮文字 + 链接地址” |
| 🧱 | **分页布局** | 每行 1–5 个、每页 1–20 个，自动预留翻页导航行 |
| 👀 | **分页预览** | 右侧按真实 QQ 键盘列数实时预览每一页 |
| 🤖 | **机器人选择** | 全部机器人生效，或只勾选指定 QQ 官方机器人 |
| 🎨 | **原生回调** | action type 1 回调，点击后插件直接处理 |

---

<a id="install"></a>

## 📦 安装

把插件目录放到 AstrBot 的：

```text
data/plugins/astrbot_plugin_button_menu
```

重载插件即可。支持的平台：

- `qq_official`
- `qq_official_webhook`

---

<a id="webui"></a>

## 🖥️ WebUI 配置

打开：

**AstrBot WebUI → 插件 → QQ官机按钮菜单 → 可视化视图**

页面分为左右两部分：

- 左侧：基础信息、分页布局、生效机器人、按钮列表
- 右侧：分页预览，实时显示当前页的按钮排布

保存后，群里重新发送一次 `/Astrbot菜单` 即可看到新菜单。旧消息上的按钮不会热更新。

---

<a id="commands"></a>

## ⌨️ 指令

| 指令 | 作用 |
| --- | --- |
| `/Astrbot菜单` | 发送按钮面板 |
| `/Astrbot菜单 2` | 直接发送第 2 页 |

如果当前会话配置了其它唤醒词，也可以用对应前缀。群聊需要先 @机器人。

---

<a id="buttons"></a>

## 🎛️ 按钮配置

每个按钮包含：

| 字段 | 说明 |
| --- | --- |
| 按钮文字 | 显示在 QQ 键盘上的文字，最多 20 个字符 |
| 按钮动作 | 发送文字 / 发送图片 / 发送链接 |
| 发送内容 | 文字内容、图片文件或链接地址 |
| 说明 | 可选，显示在菜单正文和预览里 |

- 文字：直接填写要发送的文本
- 图片：在 WebUI 点“上传图片”，支持 PNG/JPG，最大 5MB
- 链接：填写完整 URL，点击后发送按钮文字和链接地址
- 每个按钮可以上移、下移、删除
- 最多 50 个按钮

按钮点击后会先 ACK 回调，再读取当前配置发送内容。图片会先上传到 QQ 群，再以媒体消息发送。

---

<a id="pagination"></a>

## 🧱 分页布局

- 每行最多 5 个按钮
- 每页最多 20 个按钮
- 单条 QQ 键盘最多 5 行
- 有多页时自动预留最后一行作为“上一页 / 下一页”
- 因此实际每页容量可能小于配置值，WebUI 会显示实际每页数量

---

<a id="bots"></a>

## 🤖 生效机器人

WebUI 的「生效机器人」支持：

- **全部机器人**：所有 QQ 官方机器人实例都响应 `/Astrbot菜单`
- **仅选中的机器人**：只有勾选的实例响应，其它实例不发送菜单

如果当前没有检测到机器人实例，页面会提示先配置 QQ 官方平台。

---

<a id="faq"></a>

## ❓ 常见问题

**发了 `/Astrbot菜单` 没反应？**

确认插件版本是 `1.0.0` 并已重载；确认旧群管插件没有占用同名指令。

**按钮点击没有反应？**

确认机器人能收到 `INTERACTION_CREATE` 事件，并且插件已重载；查看 AstrBot 日志中的按钮回调错误。

**图片发不出去？**

确认图片是 PNG/JPG、大小不超过 5MB；QQ 媒体上传接口需要对应权限。

**为什么按钮不填输入框了？**

当前版本使用原生回调，点击后由插件直接发送配置内容，不再填指令。

---

## 📄 许可证

本项目采用 **CC BY-NC-ND 4.0** 许可：

- 允许非商业分享未修改版本，并注明作者
- 不允许商业使用、售卖或收费分发
- 不允许分发修改版或编译衍生版
- 私有修改可以保留，但不得分发

完整条款见 [LICENSE](LICENSE) 或 [Creative Commons 官方说明](https://creativecommons.org/licenses/by-nc-nd/4.0/)。
