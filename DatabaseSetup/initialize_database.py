"""读取 zhuang 配置，仅补建缺失数据库/表；不导入历史记录，不执行删表语句。"""
from __future__ import annotations

import argparse
from datetime import datetime
import getpass
import json
from pathlib import Path
import re
import shutil
import socket
import sys

TABLES=("wcs_stock_box","wcs_stock_box_all","wcs_success_box","wcs_box_orientation","wcs_plc_queue")


def statements(text):
    """分割普通SQL语句，保留引号内分号并忽略dump注释。"""
    current=[]
    quote=None
    i=0
    while i<len(text):
        c=text[i]
        if quote:
            current.append(c)
            if c=="\\" and i+1<len(text):
                i+=1
                current.append(text[i])
            elif c==quote:
                if i+1<len(text) and text[i+1]==quote:
                    i+=1
                    current.append(text[i])
                else: quote=None
        elif c in "'\"`":
            quote=c
            current.append(c)
        elif text.startswith("/*",i):
            end=text.find("*/",i+2)
            if end<0: raise ValueError("SQL块注释未闭合")
            current.append(" ")
            i=end+1
        elif c=="#" or (text.startswith("--",i) and (i+2==len(text) or text[i+2].isspace())):
            end=text.find("\n",i)
            if end<0: break
            current.append("\n")
            i=end
        elif c==";":
            if "".join(current).strip(): yield "".join(current).strip()
            current=[]
        else: current.append(c)
        i+=1
    if quote: raise ValueError("SQL字符串未闭合")
    if "".join(current).strip(): yield "".join(current).strip()


def extract_create(text,table):
    found=[]
    for sql in statements(text):
        match=re.match(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?`?([A-Za-z0-9_]+)`?\s*\(",sql,re.I)
        if match:
            if match.group(1)!=table: raise ValueError(f"SQL文件包含非预期表：{match.group(1)}")
            found.append(sql)
    if len(found)!=1: raise ValueError(f"{table} 必须恰好包含一条CREATE TABLE")
    sql=re.sub(r"^CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?","CREATE TABLE IF NOT EXISTS ",found[0],count=1,flags=re.I)
    sql=re.sub(r"\b(bigint|mediumint|smallint|tinyint|int)\s*\(\s*\d+\s*\)",r"\1",sql,flags=re.I)
    sql=re.sub(r"\s+AUTO_INCREMENT\s*=\s*\d+","",sql,flags=re.I)
    columns=set(re.findall(r"(?:\(|,)\s*`([^`]+)`\s+\w+",sql))
    if not columns: raise ValueError(f"未能读取{table}的列定义")
    return sql,columns


def quote_identifier(name):
    if not isinstance(name,str) or not re.fullmatch(r"[A-Za-z0-9_]+",name):
        raise ValueError("数据库/表名仅允许英文字母、数字和下划线")
    return f"`{name}`"


def replace_database_password(text,password):
    start=re.search(r"^database:\s*(?:#.*)?$",text,re.M)
    if not start: raise ValueError("配置中找不到顶层database段")
    next_section=re.search(r"^[^\s#][^\n]*:",text[start.end():],re.M)
    end=start.end()+next_section.start() if next_section else len(text)
    block=text[start.start():end]
    value=json.dumps(password,ensure_ascii=False)
    pattern=r"^(\s+)password\s*:[^\n]*$"
    if re.search(pattern,block,re.M):
        block=re.sub(pattern,lambda m:f"{m.group(1)}password: {value}",block,count=1,flags=re.M)
    else:
        line_end=block.find("\n")
        if line_end<0: block+=f"\n  password: {value}\n"
        else: block=block[:line_end+1]+f"  password: {value}\n"+block[line_end+1:]
    return text[:start.start()]+block+text[end:]


def load_project(project):
    import yaml
    project=Path(project).resolve()
    path=project/"config/packing_config.yaml"
    text=path.read_text(encoding="utf-8-sig")
    config=yaml.safe_load(text) or {}
    db=config.get("database") or {}
    if not isinstance(db,dict): raise ValueError("database配置必须是对象")
    host=str(db.get("host") or "localhost")
    if host not in ("localhost","127.0.0.1","::1"):
        raise ValueError("此工具只初始化本机MySQL；当前host不是本机，已停止")
    database=str(db.get("database") or "zhuangdb")
    quote_identifier(database)
    schemas={table:extract_create((project/"sql"/f"{table}.sql").read_text(encoding="utf-8-sig"),table) for table in TABLES}
    connection={"host":host,"port":int(db.get("port") or 3306),"user":str(db.get("user") or "root"),
                "password":str(db.get("password") or ""),"charset":str(db.get("charset") or "utf8mb4"),
                "connect_timeout":5,"read_timeout":15,"write_timeout":15,"autocommit":True}
    return path,text,database,connection,schemas


def run(args):
    path,text,database,connection,schemas=load_project(args.project)
    if args.write_sql:
        target=Path(args.write_sql)
        target.parent.mkdir(parents=True,exist_ok=True)
        sql=(f"CREATE DATABASE IF NOT EXISTS {quote_identifier(database)} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;\n"
             f"USE {quote_identifier(database)};\n\n"+";\n\n".join(s[0] for s in schemas.values())+";\n")
        target.write_text(sql,encoding="utf-8")
        print(f"已生成只建缺失表的SQL：{target}")
        return 0
    print(f"检查本机数据库：{connection['host']}:{connection['port']}/{database}，账号：{connection['user']}")
    try:
        with socket.create_connection((connection['host'],connection['port']),timeout=3): pass
    except OSError:
        raise RuntimeError("MYSQL_NOT_RUNNING：本机配置端口没有可连接的MySQL服务。请先安装MySQL Server、完成Configurator配置并启动服务。") from None
    if args.ask_password:
        connection['password']=getpass.getpass("请输入安装MySQL时设置的密码（输入不显示）：")
        if not connection['password']: raise ValueError("请输入已设置的密码")
    import pymysql
    with pymysql.connect(**connection) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT VERSION()")
            server_version=cursor.fetchone()[0]
            cursor.execute("SELECT SCHEMA_NAME FROM information_schema.SCHEMATA WHERE SCHEMA_NAME=%s",(database,))
            exists=cursor.fetchone() is not None
            if not exists and not args.initialize:
                raise RuntimeError("服务已连通，但数据库尚未创建，请运行初始化数据库.bat")
            if not exists:
                cursor.execute(f"CREATE DATABASE {quote_identifier(database)} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            conn.select_db(database)
            if args.initialize:
                for table,(sql,_) in schemas.items():
                    cursor.execute(sql)
                    print(f"已检查/补建：{table}")
            report_tables={}
            for table,(_,expected_columns) in schemas.items():
                cursor.execute(f"SHOW COLUMNS FROM {quote_identifier(table)}")
                actual={row[0] for row in cursor.fetchall()}
                missing=expected_columns-actual
                if missing:
                    raise RuntimeError(f"{table}已有表结构缺少列{sorted(missing)}；工具不会覆盖旧表，请另行迁移")
                report_tables[table]={"required_columns":len(expected_columns),"actual_columns":len(actual),"pass":True}
                print(f"通过：{table}（{len(actual)}列）")
    changed=False
    if args.save_config and args.ask_password:
        updated=replace_database_password(text,connection['password'])
        if updated!=text:
            backup=path.with_name(path.name+datetime.now().strftime(".backup_database_%Y%m%d_%H%M%S_%f"))
            shutil.copy2(path,backup)
            path.write_text(updated,encoding="utf-8")
            changed=True
            print("已备份并更新项目database.password；下次计算将生成新的临时配置。")
    report={"ready":True,"server_version":server_version,"host":connection['host'],"port":connection['port'],
            "database":database,"tables":report_tables,"config_updated":changed,
            "note":"仅验证数据库连接与所需列；未运行装箱或访问WCS/PLC。"}
    target=Path(args.report) if args.report else Path(__file__).resolve().parent/"last_database_check.json"
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print("DATABASE_READY：连接和5张表结构检查通过。请回到zhuang界面重新点击一键装箱。")
    return 0


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project",type=Path,default=Path(__file__).resolve().parent.parent/"packing-system")
    parser.add_argument("--initialize",action="store_true",help="只补建不存在的库和表")
    parser.add_argument("--ask-password",action="store_true",help="在本机终端隐藏输入密码")
    parser.add_argument("--save-config",action="store_true",help="连接和表检查成功后备份并更新项目密码")
    parser.add_argument("--write-sql",type=Path,help="仅生成无DROP/无历史数据的建表SQL，不连接数据库")
    parser.add_argument("--report",type=Path)
    args=parser.parse_args(argv)
    try: return run(args)
    except Exception as exc:
        print(f"[未完成] {exc}",file=sys.stderr)
        if isinstance(exc,ImportError) or "cryptography" in str(exc):
            print(f'可用项目自带Python补装依赖："{sys.executable}" -m pip install "PyMySQL[rsa]" PyYAML',file=sys.stderr)
        return 2


if __name__=="__main__": raise SystemExit(main())
