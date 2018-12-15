"""Test script to send control messages to a MQTT topic."""

import argparse
import asyncio
import logging
import logging.config
import os

from picamera_mqtt.deploy import (
    client_config_sample_localhost_name, client_configs_sample_path
)
from picamera_mqtt.imaging.mqtt_client_host import Host, topics
from picamera_mqtt.util import config
from picamera_mqtt.util.async import (
    register_keyboard_interrupt_signals, run_function
)
from picamera_mqtt.util.logging import logging_config


# Set up logging
logging.config.dictConfig(logging_config)
logger = logging.getLogger(__name__)


class MockHost(Host):
    """Sends messages to broker based on operator actions."""

    def __init__(self, *args, acquisition_interval=5, **kwargs):
        super().__init__(*args, **kwargs)
        self.acquisition_interval = acquisition_interval

    def save_captured_image(self, capture):
        logger.info('Mock saving acquired image {}.'.format(
            self.build_capture_filename(capture)
        ))

    def save_captured_metadata(self, capture):
        pass

    async def run_iteration(self):
        """Run one iteration of the run loop."""
        for target_name in self.target_names:
            self.request_image(target_name, extra_metadata={
                'host': 'mock_host'
            })
        await asyncio.sleep(self.acquisition_interval)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Send image acquisition messages and save acquired images.'
    )
    parser.add_argument(
        '--config', '-c', type=str,
        default=client_config_sample_localhost_name,
        help=('Name of client settings file in {}. Default: {}'.format(
            client_configs_sample_path, client_config_sample_localhost_name
        ))
    )
    parser.add_argument(
        '--interval', '-i', type=int, default=8,
        help='Image acquisition interval in seconds. Default: 8'
    )
    args = parser.parse_args()
    config_name = args.config
    register_keyboard_interrupt_signals()

    # Load configuration
    config_path = os.path.join(client_configs_sample_path, config_name)
    configuration = config.config_load(config_path)

    logger.info('Starting client...')
    loop = asyncio.get_event_loop()
    mqttc = MockHost(
        loop, **configuration['broker'], **configuration['host'],
        topics=topics, acquisition_interval=args.interval
    )
    run_function(mqttc.run)
    logger.info('Finished!')
