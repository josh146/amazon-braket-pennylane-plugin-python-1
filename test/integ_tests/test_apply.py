# Copyright 2019-2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.

"""Tests that gates are correctly applied in the plugin device"""
import numpy as np
import pennylane as qml
import pytest
from conftest import U2, U

from braket.pennylane_plugin import (
    ISWAP,
    PSWAP,
    XX,
    XY,
    YY,
    ZZ,
    CPhaseShift,
    CPhaseShift00,
    CPhaseShift01,
    CPhaseShift10,
)

np.random.seed(42)


# =========================================================

# list of all non-parametrized single-qubit gates,
# along with the PennyLane operation name
single_qubit = [qml.PauliX, qml.PauliY, qml.PauliZ, qml.Hadamard, qml.S, qml.SX, qml.T]

# List of all non-parametrized single-qubit gates with inverses.
single_qubit_inverse = [qml.S, qml.T]

# list of all parametrized single-qubit gates
single_qubit_param = [qml.PhaseShift, qml.RX, qml.RY, qml.RZ]

# list of all non-parametrized two-qubit gates
two_qubit = [qml.CNOT, qml.CY, qml.CZ, qml.SWAP, ISWAP]

# list of all three-qubit gates
three_qubit = [qml.CSWAP, qml.Toffoli]

# list of all parametrized two-qubit gates
two_qubit_param = [CPhaseShift, CPhaseShift00, CPhaseShift01, CPhaseShift10, PSWAP, XY, XX, YY, ZZ]


@pytest.mark.parametrize("shots", [8192])
class TestHardwareApply:
    """Test application of PennyLane operations on hardware simulators."""

    def test_basis_state(self, device, tol):
        """Test basis state initialization"""
        dev = device(4)
        state = np.array([0, 0, 1, 0])

        @qml.qnode(dev)
        def circuit():
            qml.BasisState.decomposition(state, wires=[0, 1, 2, 3])
            return qml.probs(wires=range(4))

        expected = np.zeros([2 ** 4])
        expected[np.ravel_multi_index(state, [2] * 4)] = 1
        assert np.allclose(circuit(), expected, **tol)

    def test_qubit_state_vector(self, init_state, device, tol):
        """Test state vector preparation"""
        dev = device(1)
        state = init_state(1)

        @qml.qnode(dev)
        def circuit():
            qml.QubitStateVector.decomposition(state, wires=[0])
            return qml.probs(wires=range(1))

        assert np.allclose(circuit(), np.abs(state) ** 2, **tol)

    @pytest.mark.parametrize("op", single_qubit)
    def test_single_qubit_no_parameters(self, init_state, device, op, tol):
        """Test single-qubit gates without parameters"""
        dev = device(1)
        state = init_state(1)

        @qml.qnode(dev)
        def circuit():
            qml.QubitStateVector.decomposition(state, wires=[0])
            op(wires=[0])
            return qml.probs(wires=range(1))

        assert np.allclose(circuit(), np.abs(op._matrix() @ state) ** 2, **tol)

    @pytest.mark.xfail
    @pytest.mark.parametrize("op", single_qubit_inverse)
    def test_single_qubit_no_parameters_inverse(self, init_state, device, op, tol):
        """Test inverses of single-qubit gates without parameters, where applicable"""
        dev = device(1)
        state = init_state(1)

        @qml.qnode(dev)
        def circuit():
            qml.QubitStateVector.decomposition(state, wires=[0])
            op(wires=[0]).inv()
            return qml.probs(wires=range(1))

        assert np.allclose(circuit(), np.abs(op._matrix().H @ state) ** 2, **tol)

    @pytest.mark.parametrize("theta", [0.5432, -0.232])
    @pytest.mark.parametrize("op", single_qubit_param)
    def test_single_qubit_parameters(self, init_state, device, op, theta, tol):
        """Test parametrized single-qubit gates"""
        dev = device(1)
        state = init_state(1)

        @qml.qnode(dev)
        def circuit():
            qml.QubitStateVector.decomposition(state, wires=[0])
            op(theta, wires=[0])
            return qml.probs(wires=range(1))

        assert np.allclose(circuit(), np.abs(op._matrix(theta) @ state) ** 2, **tol)

    @pytest.mark.parametrize("op", two_qubit)
    def test_two_qubit_no_parameters(self, init_state, device, op, tol):
        """Test two qubit gates with no parameters"""
        dev = device(2)
        state = init_state(2)

        @qml.qnode(dev)
        def circuit():
            qml.QubitStateVector.decomposition(state, wires=[0, 1])
            op(wires=[0, 1])
            return qml.probs(wires=range(2))

        assert np.allclose(circuit(), np.abs(op._matrix() @ state) ** 2, **tol)

    @pytest.mark.parametrize("theta", [0.5432, -0.232])
    @pytest.mark.parametrize("op", two_qubit_param)
    def test_two_qubit_parameters(self, init_state, device, op, theta, tol):
        """Test PauliX application"""
        dev = device(2)
        state = init_state(2)

        dev.pre_measure()

        @qml.qnode(dev)
        def circuit():
            qml.QubitStateVector.decomposition(state, wires=[0, 1])
            op(theta, wires=[0, 1])
            return qml.probs(wires=range(2))

        assert np.allclose(circuit(), np.abs(op._matrix(theta) @ state) ** 2, **tol)

    @pytest.mark.parametrize("op", three_qubit)
    def test_three_qubit_no_parameters(self, init_state, device, op, tol):
        dev = device(3)
        state = init_state(3)

        dev.pre_measure()

        @qml.qnode(dev)
        def circuit():
            qml.QubitStateVector.decomposition(state, wires=[0, 1, 2])
            op(wires=[0, 1, 2])
            return qml.probs(wires=range(3))

        assert np.allclose(circuit(), np.abs(op._matrix() @ state) ** 2, **tol)

    @pytest.mark.parametrize("mat", [U, U2])
    def test_qubit_unitary(self, init_state, device, mat, tol):
        N = int(np.log2(len(mat)))
        dev = device(N)
        state = init_state(N)
        wires = list(range(N))

        @qml.qnode(dev)
        def circuit():
            qml.QubitStateVector.decomposition(state, wires=wires)
            qml.QubitUnitary(mat, wires=wires)
            return qml.probs(wires=wires)

        assert np.allclose(circuit(), np.abs(mat @ state) ** 2, **tol)

    def test_rotation(self, init_state, device, tol):
        """Test three axis rotation gate"""
        dev = device(1)
        state = init_state(1)

        a = 0.542
        b = 1.3432
        c = -0.654

        @qml.qnode(dev)
        def circuit():
            qml.QubitStateVector.decomposition(state, wires=[0])
            qml.Rot(a, b, c, wires=[0])
            return qml.probs(wires=range(1))

        assert np.allclose(
            circuit(), np.abs(qml.Rot(a, b, c, wires=[0]).matrix @ state) ** 2, **tol
        )
