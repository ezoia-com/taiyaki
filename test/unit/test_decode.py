import numpy as np
import unittest

from taiyaki import decode

import torch

try:
    import taiyaki.cupy_extensions.flipflop as cuff
    _cupy_is_available = torch.cuda.is_available()
except ImportError:
    _cupy_is_available = False


class TestFlipFlopDecode(unittest.TestCase):

    def setUp(self):
        self.scores = np.array([
            [[0, 1, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0]],  # BA step (can't start in flop!)
            [[0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0]],  # Aa step
            [[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0]],  # aa stay
            [[0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0]],  # aB step
            [[0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0]],  # BB stay
            [[0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]],  # BA step
            [[1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]],  # AA stay
        ], dtype='f4')
        self.alphabet = 'AB'
        self.expected_path = np.array([1, 0, 2, 2, 1, 1, 0, 0], dtype=int)[:, None]

    def assertArrayEqual(self, a, b):
        self.assertEqual(a.shape, b.shape,
                         msg='Array shape mismatch: {} != {}\n'.format(a.shape, b.shape))
        self.assertTrue(np.allclose(a, b),
                        msg='Array element mismatch: {} != {}\n'.format(a, b))

    def test_cpu_decoding(self):
        _, _, path = decode.flipflop_viterbi(torch.tensor(self.scores))
        path = path.numpy()
        self.assertArrayEqual(path, self.expected_path)

    @unittest.skipIf(not torch.cuda.is_available(), "CUDA is not available")
    def test_gpu_decoding_no_cupy(self):
        _, _, path = decode.flipflop_viterbi(torch.tensor(self.scores, device=0),
                                             _never_use_cupy=True)
        path = path.cpu().numpy()
        self.assertArrayEqual(path, self.expected_path)

    @unittest.skipIf(not _cupy_is_available, "Cupy is not installed")
    def test_gpu_decoding_with_cupy(self):
        _, _, path = decode.flipflop_viterbi(torch.tensor(self.scores, device=0))
        path = path.cpu().numpy()
        self.assertArrayEqual(path, self.expected_path)

    @unittest.skipIf(not _cupy_is_available, "Cupy is not installed")
    def test_cupy_equals_torch_make_trans(self):
        trans_torch = decode.flipflop_make_trans(torch.tensor(self.scores, device=0),
                                                 _never_use_cupy=True)
        trans_cupy = decode.flipflop_make_trans(torch.tensor(self.scores, device=0))
        self.assertArrayEqual(trans_torch.cpu().numpy(), trans_cupy.cpu().numpy())
