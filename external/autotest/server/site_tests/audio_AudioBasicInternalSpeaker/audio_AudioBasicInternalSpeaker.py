# Copyright 2015 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""This is a server side internal speaker test using the Chameleon board."""

import logging
import os
import time

from autotest_lib.client.cros.audio import audio_test_data
from autotest_lib.client.cros.chameleon import audio_test_utils
from autotest_lib.client.cros.chameleon import chameleon_audio_ids
from autotest_lib.server.cros.audio import audio_test


class audio_AudioBasicInternalSpeaker(audio_test.AudioTest):
    """Server side internal speaker audio test.

    This test talks to a Chameleon board and a Cros device to verify
    internal speaker audio function of the Cros device.

    """
    version = 1
    DELAY_BEFORE_RECORD_SECONDS = 0.5
    RECORD_SECONDS = 8

    def run_once(self):
        """Runs Basic Audio Speaker test."""
        if not audio_test_utils.has_internal_speaker(self.host):
            return

        golden_file = audio_test_data.GenerateAudioTestData(
                        path=os.path.join(self.bindir, 'fix_440_16_0.5.raw'),
                        duration_secs=10,
                        frequencies=[440, 440],
                        volume_scale=0.5)

        source = self.widget_factory.create_widget(
                chameleon_audio_ids.CrosIds.SPEAKER)

        recorder = self.widget_factory.create_widget(
                chameleon_audio_ids.ChameleonIds.MIC)

        audio_test_utils.dump_cros_audio_logs(self.host, self.facade,
                                              self.resultsdir, 'start')

        # Selects and checks the node selected by cras is correct.
        audio_test_utils.check_and_set_chrome_active_node_types(
                self.facade, 'INTERNAL_SPEAKER', None)

        self.facade.set_selected_output_volume(80)

        logging.info('Setting playback data on Cros device')
        source.set_playback_data(golden_file)

        # Starts playing, waits for some time, and then starts recording.
        # This is to avoid artifact caused by codec initialization.
        logging.info('Start playing %s on Cros device', golden_file.path)
        source.start_playback()

        time.sleep(self.DELAY_BEFORE_RECORD_SECONDS)
        logging.info('Start recording from Chameleon.')
        recorder.start_recording()

        time.sleep(self.RECORD_SECONDS)
        self.facade.check_audio_stream_at_selected_device()
        recorder.stop_recording()
        logging.info('Stopped recording from Chameleon.')

        audio_test_utils.dump_cros_audio_logs(
                self.host, self.facade, self.resultsdir, 'after_recording')

        recorder.read_recorded_binary()
        logging.info('Read recorded binary from Chameleon.')

        recorded_file = os.path.join(self.resultsdir, "recorded.raw")
        logging.info('Saving recorded data to %s', recorded_file)
        recorder.save_file(recorded_file)

        # Removes the beginning of recorded data. This is to avoid artifact
        # caused by Chameleon codec initialization in the beginning of
        # recording.
        recorder.remove_head(0.5)

        # Removes noise by a lowpass filter.
        recorder.lowpass_filter(1000)
        recorded_file = os.path.join(self.resultsdir, "recorded_filtered.raw")
        logging.info('Saving filtered data to %s', recorded_file)
        recorder.save_file(recorded_file)

        # Compares data by frequency. Audio signal recorded by microphone has
        # gone through analog processing and through the air.
        # This suffers from codec artifacts and noise on the path.
        # Comparing data by frequency is more robust than comparing by
        # correlation, which is suitable for fully-digital audio path like USB
        # and HDMI.
        audio_test_utils.check_recorded_frequency(
                golden_file,
                recorder,
                second_peak_ratio=0.1,
                ignore_frequencies=[50, 60])
