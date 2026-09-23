# Codex Resets 中文复刻站

`codex-resets.com/zh-CN` 的静态复刻快照：奶油色 neo-brutalist 风格，含 54 条重置公告、重置热力图日历、统计卡片，支持明暗主题切换与「感谢」互动按钮。

## 本地预览

直接用浏览器打开 `index.html` 即可（需联网加载字体与赞助 logo，离线自动回退系统字体）。

## 重新生成

数据由 `build.py` 从原站 SSR HTML/CSS 解析后生成：

```bash
python build.py
```

## 部署（GitHub Pages）

仓库根目录已放好 `index.html` 与 `avatar.jpg`，可直接开启 GitHub Pages：

1. 仓库 → Settings → Pages → Build and deployment
2. Source 选 **Deploy from a branch**，Branch 选 **main**，目录选 **/ (root)**
3. 保存后访问 `https://dqtx760.github.io/codex-resets/`

## 文件说明

| 文件 | 说明 |
|------|------|
| `index.html` | 复刻成品（单文件） |
| `avatar.jpg` | 头像图片 |
| `build.py` | 生成器脚本 |
| `.gitignore` | 排除原站抓取的中间文件 |
