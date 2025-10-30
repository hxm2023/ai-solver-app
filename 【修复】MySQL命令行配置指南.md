# MySQL命令行工具配置指南

## 问题现象

运行批处理文件时提示：
```
❌ 错误：未找到mysql命令
```

## 原因

MySQL的bin目录不在系统PATH环境变量中

---

## 解决方案

### 方法1：临时设置（本次有效）

在命令行中执行：

```cmd
set PATH=%PATH%;C:\Program Files\MySQL\MySQL Server 8.0\bin
```

然后重新运行升级脚本。

**注意**：路径可能不同，请根据实际安装位置调整。

---

### 方法2：永久设置（推荐）

#### Windows 10/11

1. **找到MySQL安装路径**
   - 常见位置：
     - `C:\Program Files\MySQL\MySQL Server 8.0\bin`
     - `C:\Program Files\MySQL\MySQL Server 5.7\bin`
     - `C:\xampp\mysql\bin`
   - 确认路径下有 `mysql.exe` 文件

2. **添加到系统PATH**
   - 按 `Win + X`，选择 `系统`
   - 点击 `高级系统设置`
   - 点击 `环境变量`
   - 在 `系统变量` 区域，找到并双击 `Path`
   - 点击 `新建`
   - 输入MySQL的bin路径，例如：`C:\Program Files\MySQL\MySQL Server 8.0\bin`
   - 点击 `确定` → `确定` → `确定`

3. **验证配置**
   - 关闭所有命令行窗口
   - 打开新的命令行窗口
   - 输入：`mysql --version`
   - 应该看到MySQL版本信息

#### 详细图文步骤

1. 右键 `此电脑` → `属性`
2. 点击 `高级系统设置`
3. 点击 `环境变量`
4. 在下方 `系统变量` 中找到 `Path`，双击
5. 点击 `新建`，添加MySQL的bin路径
6. 一路点 `确定` 保存

---

### 方法3：使用完整路径（快速方案）

修改批处理文件，直接使用MySQL的完整路径：

```batch
"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -h 14.103.127.20 -P 3306 -u root -p edu < backend\database_schema_v25.2.sql
```

---

## 如果找不到MySQL安装位置

### 搜索mysql.exe

1. 按 `Win + S` 打开搜索
2. 搜索 `mysql.exe`
3. 找到后，右键 → `打开文件位置`
4. 复制该路径

### 或者检查服务

1. 按 `Win + R`，输入 `services.msc`
2. 找到 `MySQL` 服务
3. 右键 → `属性`
4. 查看 `可执行文件路径`

---

## 验证配置成功

打开命令行，输入：

```cmd
mysql --version
```

应该看到类似输出：
```
mysql  Ver 8.0.xx for Win64 on x86_64
```

---

## 仍然无法解决？

使用Navicat或MySQL Workbench手动执行SQL脚本：

1. 打开Navicat
2. 连接到数据库
3. 新建查询
4. 复制 `backend\database_schema_v25.2.sql` 的内容
5. 粘贴并执行

**更简单，不需要配置命令行！**

