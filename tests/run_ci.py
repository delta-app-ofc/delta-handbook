"""Runner com JUnit; descoberta vazia ou testes não aprovados retornam erro."""
import sys
import unittest
from pathlib import Path
import xmlrunner

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
suite = unittest.defaultTestLoader.discover(str(root / "tests"), pattern="test_*.py")
if suite.countTestCases() == 0:
    raise SystemExit("Nenhum teste coletado")
result = xmlrunner.XMLTestRunner(output=str(root / "reports/junit"), verbosity=2).run(suite)
raise SystemExit(0 if result.wasSuccessful() and not result.skipped else 1)
