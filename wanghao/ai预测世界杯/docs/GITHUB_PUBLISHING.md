# GitHub 发布操作手册

当前目录尚未初始化 Git，也没有远端。建议第一次先创建 **Private** 仓库，确认第三方数据条款和 Git LFS 状态后再决定是否公开。

## 发布前检查

```powershell
python scripts/check_repository.py
python -m unittest discover -s tests -v
python scripts/build_repository_manifest.py
git lfs version
```

确认目录中没有 `.env`、钱包、API key、浏览器 cookie、个人仓位或其他敏感信息。当前自动文件名审计未发现此类文件，但仍应人工检查即将提交的 diff。

## 情形 A：GitHub 上是全新的空仓库

在本项目根目录执行：

```powershell
git lfs install
git init -b main
git add .gitattributes .gitignore
git add .
git status --short
git lfs ls-files
git diff --cached --stat
git commit -m "Initial import: World Cup 2026 prediction research"
git remote add origin https://github.com/OWNER/REPOSITORY.git
git remote -v
git push -u origin main
```

GitHub 创建空仓库时，不要勾选自动生成 README、`.gitignore` 或 LICENSE，避免首推出现无关历史冲突。

## 情形 B：目标 GitHub 项目已经有提交

不要直接在当前目录 `git init` 后强推。更安全的流程是：

1. 克隆目标仓库到一个新目录。
2. 在目标仓库创建导入分支，例如 `import/world-cup-model`。
3. 将本项目作为目标仓库的一个子目录复制进去，例如 `research/world-cup-2026-polymarket/`；不要复制 `.git/` 或 `.venv/`。
4. 在目标仓库根目录配置 Git LFS 规则，检查是否与现有 `.gitattributes` 冲突。
5. 提交到导入分支并通过 Pull Request 合并。

建议命令框架：

```powershell
git clone https://github.com/OWNER/REPOSITORY.git
Set-Location REPOSITORY
git switch -c import/world-cup-model
# 在文件管理器中将本项目复制到约定子目录；排除 .git、.venv 和 __pycache__。
git add research/world-cup-2026-polymarket
git status --short
git commit -m "Add World Cup 2026 Polymarket research archive"
git push -u origin import/world-cup-model
```

## LFS 验证

本项目的 `.gitattributes` 将 PDF、GZip 数据和 Polymarket 原始订单簿 JSON 交给 LFS。首次提交前：

```powershell
git lfs install
git check-attr filter -- data/raw/fifa_performance_reports_2026/PMSR-M101-FRA-V-ESP.pdf
git check-attr filter -- data/raw/statsbomb_world_cups/2022/events/3857254.json.gz
git check-attr filter -- data/raw/polymarket/remaining_matches_live_20260718_161429Z.json
```

三条结果都应显示 `filter: lfs`。提交后 `git lfs ls-files` 应列出这些文件。

## 首次提交不要做的事

- 不要使用 `git push --force`。
- 不要把完整项目压成 ZIP 再提交；这样无法进行代码审查和历史维护。
- 不要删除历史输出，只保留“最终版”。模型错误和预测修订本身是研究记录。
- 不要在提交后才决定排除 100 MB 以上文件；大文件一旦进入 Git 历史，普通删除不会移除历史对象。
- 不要随意选择开源许可证。先确认代码归属、第三方数据和你希望允许的使用方式。

## 后续维护节奏

每次新预测建议采用一个小提交：

1. `data/raw/` 新快照和 provenance。
2. `data/inputs/` 当时阵容/假设。
3. 配置与代码变更。
4. 新的 `outputs/runs/<UTC>_<version>_<fixture>/`。
5. 复盘作为后续独立提交，不能改写赛前预测。

推荐提交信息：

```text
data: freeze Polymarket snapshot at 2026-07-19T18:00Z
model: add lineup uncertainty calibration for v8
prediction: add Spain vs Argentina final pre-match run
postmortem: compare final forecast with actual events
docs: update prediction history and data provenance
```
