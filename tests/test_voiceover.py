import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest

import numpy as np
from splice import RATE, write_wav, read_wav, process
from voiceover import ROOT, deliver, find_ffmpeg


class ProcessorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ffmpeg = find_ffmpeg(os.environ.get('VOICEOVER_FFMPEG'))

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT)
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        self.settings = json.loads((ROOT/'settings.json').read_text())
        tone = (5000*np.sin(2*np.pi*440*np.arange(RATE)/RATE)).astype(np.int16)
        self.source = self.path/'input.wav'
        write_wav(self.source, np.concatenate([tone, np.zeros(RATE//2,dtype=np.int16), tone])[:,None])

    def render(self, name='result.mp3', cap=43, settings=None):
        return deliver(self.source,self.path/name,cap,settings or self.settings,self.ffmpeg)

    def test_export_pitch_cap_hash_and_no_overwrite(self):
        original = hashlib.sha256(self.source.read_bytes()).hexdigest()
        report = self.render()
        self.assertEqual(report['source_sha256'],original)
        self.assertEqual(hashlib.sha256(self.source.read_bytes()).hexdigest(),original)
        self.assertEqual(report['speed'],1.3)
        self.assertLess(report['mp3_seconds'],2)
        for suffix in ('mp3','wav','json'):
            self.assertGreater((self.path/f'result.{suffix}').stat().st_size,0)
        audio = read_wav(self.path/'result.wav')[:RATE//2,0].astype(float)
        peak = np.fft.rfftfreq(len(audio),1/RATE)[np.argmax(abs(np.fft.rfft(audio)))]
        self.assertAlmostEqual(peak,440*1.3,delta=3)
        with self.assertRaisesRegex(ValueError,'already exist'):
            self.render()

    def test_cap_adjusts_within_range(self):
        first = self.render()
        cap = first['spliced_seconds']/1.32
        second = self.render('cap.mp3',cap)
        self.assertLessEqual(second['mp3_seconds'],cap)
        self.assertGreater(second['speed'],1.3)
        self.assertLessEqual(second['effective_speed'],1.33)

    def test_conflicting_cap_leaves_no_outputs(self):
        with self.assertRaisesRegex(ValueError,'permitted speed range'):
            self.render('impossible.mp3',.5)
        self.assertFalse(any(self.path.glob('impossible.*')))

    def test_explicit_override_does_not_change_defaults(self):
        report=self.render(settings={**self.settings,'base_speed':1.4,'maximum_speed':1.4})
        self.assertEqual(report['speed'],1.4)
        self.assertEqual(json.loads((ROOT/'settings.json').read_text())['base_speed'],1.3)

    def test_invalid_inputs(self):
        with self.assertRaises(ValueError):
            deliver(self.path/'missing.wav',self.path/'missing.mp3',ffmpeg=self.ffmpeg)
        for cap in (0,float('nan')):
            with self.assertRaises(ValueError):
                self.render(cap=cap)
        for settings in ({}, {'base_speed':1.3}, {**self.settings,'head_ms':-1}, {**self.settings,'base_speed':1.34}):
            with self.assertRaises(ValueError):
                deliver(self.source,self.path/'invalid.mp3',43,settings,self.ffmpeg)
        write_wav(self.path/'silent.wav',np.zeros((RATE,1),dtype=np.int16))
        with self.assertRaises(ValueError):
            deliver(self.path/'silent.wav',self.path/'silent.mp3',ffmpeg=self.ffmpeg)

    def test_existing_sidecar_and_source_protection(self):
        (self.path/'blocked.json').write_text('keep')
        with self.assertRaises(ValueError):
            self.render('blocked.mp3')
        self.assertEqual((self.path/'blocked.json').read_text(),'keep')
        with self.assertRaises(ValueError):
            self.render('input.mp3')  # would overwrite the input.wav sidecar

    def test_synthetic_quiet_edge_is_inside_margin(self):
        data=read_wav(self.source)
        # Quiet 40 ms burst immediately before the second tone is protected by 45 ms head margin.
        start=RATE+RATE//2-int(.04*RATE)
        data[start:RATE+RATE//2,0]=100
        write_wav(self.source,data)
        report=self.render()
        self.assertTrue(report['cuts'])
        self.assertLessEqual(report['cuts'][0]['end'],start/RATE)


if __name__ == '__main__':
    unittest.main()
