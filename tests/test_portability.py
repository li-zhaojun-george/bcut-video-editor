"""Isolated data-flow checks; no native app, real media or live draft library is used."""
import json
import contextlib
import io
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
import uuid
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import bcut_draft as bd
import env_paths
from check_distribution import check
from register_draft import register


class PortabilityTests(unittest.TestCase):
    def setUp(self):
        self.work_root = Path(os.environ.get('BCUT_TEST_TMP', tempfile.gettempdir())).resolve()
        self.work_root.mkdir(parents=True, exist_ok=True)
        self.base = self.work_root / ('bcut-portability-' + uuid.uuid4().hex)
        self.base.mkdir()

    def tearDown(self):
        env_paths._CACHE.clear()
        if self.base.resolve().parent != self.work_root or not self.base.name.startswith('bcut-portability-'):
            raise RuntimeError('Unsafe test cleanup path')
        shutil.rmtree(self.base)

    def test_public_package(self):
        _, errors = check()
        self.assertEqual(errors, [])

    def test_two_independent_profiles(self):
        all_ids = []
        outputs = []
        for profile_name in ('profile-a', 'profile-b'):
            profile = self.base / profile_name
            install = profile / 'apps' / 'BCUT'
            speech = install / 'res' / 'subtt' / 'huazi' / 'speech'
            speech.mkdir(parents=True)
            (install / 'BCUT.exe').touch()
            (install / 'Font').mkdir()
            (install / 'Font' / 'Source Han Sans CN Medium.ttf').touch()
            media = profile / 'media'
            media.mkdir()
            video = media / 'clip.mp4'
            audio = media / 'music.wav'
            video.touch()
            audio.touch()
            staging = profile / 'staged'

            def fake_probe(path):
                return dict(path=str(path), kind='audio' if str(path).endswith('.wav') else 'video',
                            duration_ms=4000, width=1280, height=720, fps_num=30, fps_den=1)

            with patch.dict(os.environ, {'BCUT_HOME': str(install), 'BCUT_LOCAL_RES': str(profile / 'local_res')}), \
                    patch.object(env_paths, 'HOME', str(profile)), \
                    patch.object(bd, 'BCUT_HOME', str(install)), \
                    patch.object(bd, 'DRAFT_ROOT', str(staging)), patch.object(bd, 'probe', fake_probe):
                env_paths._CACHE.clear()
                tl = bd.Timeline(1280, 720, 30)
                tl.add_clip(str(video), trim_out=2000)
                tl.add_clip(str(video), trim_in=2000, trim_out=4000)
                tl.add_caption('示例字幕 A', 0, 1800)
                tl.add_caption('示例字幕 B', 2200, 3800)
                tl.add_audio(str(audio), trim_out=4000)
                guid = tl.save(name='示例项目', cover=False)
                data = bd.load(guid)
                timeline = data['timelineWidget']['timeline']
                self.assertEqual(timeline['videoTracks'][0]['index'], 0)
                self.assertEqual(timeline['captionTracks'][0]['index'], 1)
                for clip in timeline['videoTracks'][0]['clips']:
                    self.assertEqual(clip['sourcePath'], video.as_posix())
                    self.assertEqual(clip['propertyFxList'], [])
                    all_ids.extend(fx['idString'] for fx in clip['audioFxs'] + clip['fxs'])
                for caption in timeline['captionTracks'][0]['captions']:
                    self.assertEqual(caption['assetInfo']['srcPath'], speech.as_posix())
                    self.assertTrue(caption['fontPackagePath'].startswith(install.as_posix()))
                ac = timeline['audioTracks'][0]['audioClips'][0]
                self.assertEqual(ac['sourcePath'], audio.as_posix())
                self.assertEqual(ac['materialId'], '')
                self.assertNotIn('markSet', ac)
                self.assertEqual(ac['assetInfo']['content'], audio.stem)
                output = json.dumps(data, ensure_ascii=False)
                outputs.append(output)

                destination = profile / 'library'
                destination.mkdir()
                original = {'draftInfos': [{'id': 'existing-project', 'name': 'keep'}], 'custom': 'keep'}
                index = destination / 'draftInfo.json'
                index.write_text(json.dumps(original), encoding='utf-8')
                with patch('register_draft.subprocess.check_output', return_value='No matching process\n'), contextlib.redirect_stdout(io.StringIO()):
                    register(staging, guid, destination, profile / 'backups')
                actual = json.loads(index.read_text(encoding='utf-8'))
                self.assertEqual(actual['draftInfos'][:-1], original['draftInfos'])
                self.assertEqual(actual['custom'], original['custom'])
                self.assertEqual(len(list(destination.glob('*/.dsh-created'))), 1)
        self.assertEqual(len(all_ids), len(set(all_ids)))
        self.assertNotIn('profile-b', outputs[0])
        self.assertNotIn('profile-a', outputs[1])

    def test_missing_local_caption_resource_fails(self):
        with patch.object(bd, 'BCUT_HOME', str(self.base / 'missing')):
            with self.assertRaises(FileNotFoundError):
                bd.Timeline().add_caption('示例字幕', 0, 1000)


if __name__ == '__main__':
    unittest.main()
