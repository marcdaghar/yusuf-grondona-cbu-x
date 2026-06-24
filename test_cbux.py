"""
Tests unitaires pour le système CBU-X
"""
import unittest
import numpy as np
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from option2_logistique_villani import Port, VillaniLogistics
from option3_waqf_numerique import WaqfGenerator

class TestTransportOptimal(unittest.TestCase):
    def test_port_creation(self):
        p = Port("Test", 0.0, 0.0, 0.5, 0.5)
        self.assertEqual(p.nom, "Test")
        self.assertEqual(p.offre, 0.5)

    def test_sinkhorn_convergence(self):
        ports = [
            Port("A", 0.0, 0.0, 0.5, 0.5),
            Port("B", 1.0, 0.0, 0.5, 0.5)
        ]
        model = VillaniLogistics(ports, epsilon=0.1, max_iter=100)
        model.build_cost_matrix()
        P = model.sinkhorn()
        self.assertIsNotNone(P)
        self.assertEqual(P.shape, (2, 2))

    def test_ricci_curvature(self):
        ports = [
            Port("A", 0.0, 0.0, 0.5, 0.5),
            Port("B", 1.0, 0.0, 0.5, 0.5)
        ]
        model = VillaniLogistics(ports, epsilon=0.1, max_iter=100)
        model.build_cost_matrix()
        model.sinkhorn()
        curvature = model.compute_ricci_curvature()
        self.assertEqual(curvature.shape, (2, 2))

class TestWaqfNumerique(unittest.TestCase):
    def test_contract_generation(self):
        gen = WaqfGenerator()
        contrat = gen.generer_contrat_solidity()
        self.assertIn("pragma solidity", contrat)
        self.assertIn("WaqfClusterMed", contrat)

    def test_beneficiaires_count(self):
        gen = WaqfGenerator()
        self.assertEqual(len(gen.beneficiaires), 4)
        total = sum(b['part'] for b in gen.beneficiaires)
        self.assertEqual(total, 100)

if __name__ == '__main__':
    unittest.main()
