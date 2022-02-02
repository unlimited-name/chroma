from .unittest_find import unittest
import itertools

from chroma import generator
from chroma.generator.vertex import constant_particle_gun
from chroma.demo.optics import water

class TestG4ParallelGenerator(unittest.TestCase):
    def test_center(self):
        '''Generate Cherenkov light at the center of the world volume'''
        gen = generator.photon.G4ParallelGenerator(1, water)
        vertex = itertools.islice(constant_particle_gun('e-', (0,0,0), (1,0,0), 100), 10)
        for event in gen.generate_events(vertex):
            self.assertGreater(len(event.photons_beg.pos), 0)

    def test_off_center(self):
        '''Generate Cherenkov light at (1 m, 0 m, 0 m)'''
        gen = generator.photon.G4ParallelGenerator(1, water)
        vertex = itertools.islice(constant_particle_gun('e-', (1000,0,0), (1,0,0), 100), 10)
        for event in gen.generate_events(vertex):
            self.assertGreater(len(event.photons_beg.pos), 0)
