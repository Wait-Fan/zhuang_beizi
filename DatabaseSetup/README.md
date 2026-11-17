# zhuang 本机数据库安装与初始化

适用目录：`E:\范卓燃\码垛算法\文件\装箱算法\zhuang`。本目录 `DatabaseSetup` 应与 `PackingPortable`、`packing-system` 并列。

当前报错是本机MySQL连接被拒绝；程序在写库存表时中断。装上Python的pymysql并不等于安装MySQL Server。此工具没有安装MySQL Server，需要先完成下面第一步。

## 1. 安装并配置 MySQL Server

官方入口：https://dev.mysql.com/downloads/mysql/8.4.html

选择 **MySQL Community Server 8.4 LTS → Windows (x86,64-bit), MSI Installer**。无需下载Debug/Test Suite。

按安装向导安装Server；随后打开随附的 **MySQL Configurator** 完成配置：

- 本机开发用途可选Development Computer，TCP/IP端口3306。
- 本机使用不需要勾选开放Windows防火墙端口的选项。
- 设置并记住root账号的密码。密码只在你本机输入，不需要发到聊天。
- Windows服务名称可保留MySQL84；勾选随Windows启动，并完成Execute/Apply步骤，确认服务启动成功。

你机器已检测到Visual C++ 2015–2022 x64运行库。若安装器仍提示运行库问题，按官方安装器提示处理。

官方文档：https://dev.mysql.com/doc/refman/8.4/en/windows-installation.html

## 2. 安装项目Python的认证依赖

双击 `00_install_client_dependencies.bat`。它只用项目自带的Python安装 `PyMySQL[rsa]` 和PyYAML，不使用Conda，不修改算法。

你的便携Python中已存在PyMySQL，但缺少cryptography。PyMySQL连接MySQL8默认caching_sha2_password认证时需要RSA额外依赖：
https://pymysql.readthedocs.io/en/latest/user/installation.html

## 3. 初始化项目数据库

双击 `01_initialize_database.bat`，输入第一步设置的root密码。输入时屏幕不显示字符，这是正常现象。

工具从 `packing-system/config/packing_config.yaml` 读取本机地址、端口、用户名和库名；当前项目为localhost:3306、root、zhuangdb。密码使用你本次输入的值。

连接成功后只创建缺失的数据库/表：

1. wcs_stock_box：当前库存
2. wcs_stock_box_all：历史库存
3. wcs_success_box：装箱结果
4. wcs_box_orientation：箱体目标姿态
5. wcs_plc_queue：命令队列表

它从项目SQL文件提取CREATE TABLE，去掉旧数据自增起点和整数显示宽度，加入IF NOT EXISTS；不执行DROP、DELETE、TRUNCATE或历史INSERT。已有表不会被重建；若已有表缺少列，会停止并提示另行迁移。

表检查通过后，工具备份主配置文件，再将输入的密码保存到该文件的database.password。其余配置保持不变。主配置的备份名含 `.backup_database_时间`。

看到 `DATABASE_READY` 才表示数据库连接和所需列检查通过。成功报告为 `last_database_check.json`，不包含密码。

## 4. 回到原zhuang界面重新计算

关闭并重开原界面，重新选择历史接口JSON，再点击一键装箱。临时UI配置由主配置重新生成，不要编辑旧的ui_config_api文件。

后续可双击 `02_check_database.bat` 检查服务、当前配置密码和表结构；它不建表、不运行装箱、不访问WCS或PLC。单纯创建PLC队列表不会发送设备命令。

`DATABASE_READY` 只说明数据库这一环节就绪，完整装箱是否完成仍取决于输入数据、算法约束和后续服务配置，不能以数据库测试替代全系统测试。

## 常见结果

- `MYSQL_NOT_RUNNING` / 2003 / 10061：Server未启动、未完成Configurator配置，或端口与项目不一致。
- `1045 Access denied`：用户名/密码不匹配。再运行01并输入安装时设置的密码。
- `cryptography is required`：先运行00安装认证依赖。
- `1049 Unknown database` / `1146 Table doesn't exist`：运行01补建库表。
- 已有表缺少列：工具会保留旧表，不自动覆盖；需要根据提示做结构迁移。

备用的 `create_zhuangdb_tables.sql` 是从当前项目导出的只建缺失表版本，可人工导入；它不会同步主配置密码。优先使用01脚本。

## 开发验证

6项测试覆盖SQL引号/注释分割、排除历史数据、非预期表拒绝、仅更新database密码、缺失密码字段补充、数据库名称注入防护。当前尚未实际连上MySQL，不能把脚本测试等同于数据库安装/初始化完成。
