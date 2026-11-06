# 智伴 AI · Windows 重建版

这是从头重建的 Windows 桌面助手项目。当前交付的是完整源码与 Windows 打包脚本，不是已经编译验证的 `.exe` 安装包。

## 功能
- 深色科技风聊天界面
- OpenAI 兼容 Chat Completions API
- 系统托盘常驻；关闭窗口后缩到托盘
- Alt + Space 全局唤起快捷键（部分电脑/权限环境可能被其他软件占用）
- 桌面悬浮助手
- 屏幕理解：必须由用户主动点击并二次确认；截图会发送给所配置的模型服务商
- 本地待办清单
- 可选语音朗读
- 配置和待办保存在 `%APPDATA%\\ZhiBanAI`

## 普通用户最终使用方式
目标交付物是 `智伴AI_Windows安装程序.exe`。安装后从桌面快捷方式启动，不需要在用户电脑安装 Python。

## 不在自己电脑安装 Python：云端构建（推荐）
项目包含 GitHub Actions 工作流 `.github/workflows/build-windows.yml`。你可以把 `智伴AI` 文件夹中的全部内容上传到自己的 GitHub 仓库，在仓库的 **Actions** 页面运行 **Build ZhiBan AI Windows Installer**。GitHub 会在云端 Windows 环境安装构建依赖并生成安装程序；完成后在该次工作流页面的 Artifacts 区域下载 `ZhiBanAI-Windows-Installer`。这条路径不要求你的 Windows 电脑安装 Python，但需要 GitHub 账号并把项目上传到仓库。

## 在 Windows 11 本机手动构建安装包
构建电脑需要：
1. Windows 10/11 64 位
2. Python 3.10 或更新版本（只用于构建，不是最终用户运行依赖）
3. Inno Setup 6（用于生成安装程序；官网 https://jrsoftware.org/isinfo.php）

步骤：
1. 解压整个项目文件夹。
2. 双击 `构建Windows安装包.bat`。
3. 若系统已安装 Inno Setup 且 `ISCC` 在 PATH 中，安装程序会输出到 `installer_output`。
4. 若没有 Inno Setup，先得到 `dist\\智伴AI\\智伴AI.exe`，再安装 Inno Setup 并运行 `ISCC installer.iss`。

## 首次启动
1. 点击左侧“设置”。
2. 填入 API Base URL，例如 `https://api.openai.com/v1`。
3. 填入服务商发放的 API Key。
4. 填入模型名，例如 `gpt-4o-mini`（以服务商实际支持为准）。
5. 保存后即可聊天。

本程序不内置 API Key，也不包含免费模型额度。不同服务商的兼容接口地址和模型名称可能不同。

## 隐私与安全
- API Key 保存在本机 `%APPDATA%\\ZhiBanAI\\config.json`，当前版本未做 Windows 凭据库加密；请勿与他人共享该文件。
- 屏幕理解会截取整个主屏幕，并在你确认后把图片发送到配置的模型服务商。不要分享含密码、支付信息或其他敏感资料的画面。
- 截图副本保存在 `%APPDATA%\\ZhiBanAI\\last_screen_capture.png`。
- 待办数据保存在 `%APPDATA%\\ZhiBanAI\\todos.json`。

## 当前版本边界
- 这是可运行的基础重建版，不具备系统级自动操控电脑、读取所有应用内容或后台监控能力。
- 全局快捷键依赖 `keyboard` 库，若被其他程序占用或权限受限可能不可用。
- 语音朗读依赖 Windows 语音环境，某些设备可能没有可用语音。
- Windows 安装包必须在 Windows 构建环境生成并测试；当前交付环境不能直接编译 Windows 安装程序，因此没有把未验证文件伪装成安装包。
