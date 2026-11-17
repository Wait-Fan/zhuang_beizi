import tempfile
import unittest
from pathlib import Path

from initialize_database import extract_create,replace_database_password,quote_identifier


class DatabaseSetupTests(unittest.TestCase):
    def test_imports_only_create_and_handles_semicolon_inside_comment(self):
        text="""DROP TABLE `wcs_stock_box`;
        CREATE TABLE `wcs_stock_box` (`id` bigint(0) NOT NULL, `memo` text COMMENT 'a;b')
        ENGINE=InnoDB AUTO_INCREMENT=99;
        INSERT INTO `wcs_stock_box` VALUES (1,'old');"""
        create,columns=extract_create(text,"wcs_stock_box")
        self.assertTrue(create.startswith("CREATE TABLE IF NOT EXISTS"))
        self.assertNotIn("DROP TABLE",create)
        self.assertNotIn("INSERT INTO",create)
        self.assertNotIn("bigint(0)",create)
        self.assertNotIn("AUTO_INCREMENT=99",create)
        self.assertIn("'a;b'",create)
        self.assertEqual(columns,{"id","memo"})

    def test_escaped_quotes_do_not_expose_data_statements(self):
        text="CREATE TABLE `t` (`id` int COMMENT 'a\\';b') ENGINE=InnoDB; INSERT INTO t VALUES(7);"
        create,_=extract_create(text,"t")
        self.assertNotIn("INSERT INTO",create)
        self.assertIn("a\\';b",create)

    def test_mismatched_or_repeated_create_is_rejected(self):
        for text in ("CREATE TABLE other (`id` int) ENGINE=InnoDB;",
                     "CREATE TABLE t (`id` int);CREATE TABLE t (`id` int);"):
            with self.assertRaises(ValueError): extract_create(text,"t")

    def test_only_database_password_is_replaced_and_comments_remain(self):
        text='''# keep header
database:
  host: localhost
  password: old # old credential
  database: zhuangdb
api:
  password: untouched
# keep footer
'''
        updated=replace_database_password(text,'new"pass#word')
        self.assertIn('password: "new\\"pass#word"',updated)
        self.assertIn('  password: untouched',updated)
        self.assertIn('# keep footer',updated)
        self.assertIn('  host: localhost',updated)

    def test_missing_password_is_added_inside_database_only(self):
        updated=replace_database_password('database:\n  host: localhost\nother:\n  value: 1\n','secret')
        self.assertIn('database:\n  password: "secret"\n',updated)
        self.assertIn('other:\n  value: 1',updated)

    def test_database_identifier_cannot_inject_sql(self):
        self.assertEqual(quote_identifier("zhuangdb"),'`zhuangdb`')
        for name in ('a;DROP DATABASE b','x`y','',None):
            with self.assertRaises(ValueError): quote_identifier(name)


if __name__=="__main__": unittest.main()
