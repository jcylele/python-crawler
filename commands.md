### modules
使用conda
- 添加库

	conda install module_name
	安装后同步一下environment.yml

### db
1. 生成迁移文件（自动检测变更）

	alembic revision --autogenerate -m "blablablabla"

2. 检查生成的迁移文件

	顺便增加一些自己的迁移逻辑，比如数据初始化、

3. 应用迁移

	alembic upgrade head

4. 验证结果

	*查看当前数据库版本*
	alembic current

	*查看迁移历史*
	alembic history

### py
- 打包
	
	pyinstaller .\web.spec --noconfirm