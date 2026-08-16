from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from phase3_training.gates import TrainingGateError, training_gate_status


class Phase3TrainingGateTests(unittest.TestCase):
    def test_trainer_defaults_to_dry_run_status(self) -> None:
        status = training_gate_status(real_training=False, human_pipeline_signoff=None)
        self.assertEqual(status["status"], "DRY_RUN_ONLY")
        self.assertEqual(status["training"], "NOT_PERFORMED")
        self.assertEqual(status["gradients"], "NOT_COMPUTED")

    def test_real_training_requires_human_signoff(self) -> None:
        with self.assertRaises(TrainingGateError):
            training_gate_status(real_training=True, human_pipeline_signoff=None)


if __name__ == "__main__":
    unittest.main()

