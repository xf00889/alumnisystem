"""Regression checks for the user-management service import collision."""
import ast
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]


class UserManagementImportTests(unittest.TestCase):
    def test_user_management_views_imports_module_explicitly(self):
        source = (ROOT / 'core/view_handlers/user_management_views.py').read_text(encoding='utf8')
        parsed = ast.parse(source)
        matched = [node for node in parsed.body if isinstance(node, ast.ImportFrom)
                   and node.module == 'core.services.user_management']
        self.assertEqual(len(matched), 1)
        self.assertEqual({alias.name for alias in matched[0].names}, {
            'UserManagementService', 'RoleAssignmentService', 'AuditLogService'
        })

    def test_service_class_definitions_present(self):
        new = (ROOT / 'core/services/user_management.py').read_text(encoding='utf8')
        old = (ROOT / 'core/services.py').read_text(encoding='utf8')
        original_classes = {n.name for n in ast.parse(old).body if isinstance(n, ast.ClassDef)}
        new_classes = {n.name for n in ast.parse(new).body if isinstance(n, ast.ClassDef)}
        self.assertTrue({'UserManagementService', 'RoleAssignmentService', 'AuditLogService'}.issubset(new_classes))
        self.assertEqual(original_classes, new_classes)

    def test_relative_imports_adjusted(self):
        mod = ast.parse((ROOT / 'core/services/user_management.py').read_text(encoding='utf8'))
        imports = {(node.level,node.module) for node in mod.body if isinstance(node, ast.ImportFrom)}
        self.assertIn((2, 'models.user_management'), imports)
        self.assertIn((2, 'email_utils'), imports)

    def test_facebook_module_remains_accessible(self):
        pkg = ROOT / 'core/services'
        self.assertTrue((pkg / '__init__.py').exists())
        self.assertTrue((pkg / 'facebook_page_feed.py').exists())

if __name__ == '__main__':
    unittest.main()
