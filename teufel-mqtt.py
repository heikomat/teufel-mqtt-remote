#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import paho.mqtt.client as mqtt
import subprocess
import time
import re
import configparser as ConfigParser
import threading
import os
import RPi.GPIO as GPIO
from threading import Timer

def debounce(wait):
    """ Decorator that will postpone a functions
        execution until after wait seconds
        have elapsed since the last time it was invoked. """
    def decorator(fn):
        def debounced(*args, **kwargs):
            def call_it():
                fn(*args, **kwargs)
            try:
                debounced.t.cancel()
            except(AttributeError):
                pass
            debounced.t = Timer(wait, call_it)
            debounced.t.start()
        return debounced
    return decorator

old_a = 1
old_b = 1

# Default configuration
config = {
  'mqtt': {
    'broker': 'localhost',
    'devicename': 'teufel-mqtt',
    'port': 1883,
    'user': os.environ.get('MQTT_USER'),
    'password': os.environ.get('MQTT_PASSWORD'),
    'tls': 0,
  },
  'teufel': {
    'out_a': 22,
    'out_b': 17,
    'out_shared': 27,
    'button_read': 24,
    'button_value': 23
  }
}

def set_new_values(new_a, new_b):
    global old_a, old_b
    GPIO.output([
        config['teufel']['button_read'],
        config['teufel']['button_value'],
        config['teufel']['out_a'],
        config['teufel']['out_b'],
        config['teufel']['out_shared']
    ], [0, 1, new_a, new_b, 0])
    old_a = new_a
    old_b = new_b

def volume_up():
    print('vol. up')
    global old_a, old_b
    if old_a == 1:
        set_new_values(1, 0)
        time.sleep(0.01)
        set_new_values(0, 0)
    else:
        set_new_values(0, 1)
        time.sleep(0.01)
        set_new_values(1, 1)

def volume_down():
    print('vol. down')
    global old_a, old_b
    for i in range(2):
        if old_b == 1:
            set_new_values(0, 1)
            time.sleep(0.01)
            set_new_values(0, 0)
        else:
            set_new_values(1, 0)
            time.sleep(0.01)
            set_new_values(1, 1)

def button_press():
    print('button_press')
    GPIO.output([
      config['teufel']['out_shared'],
      config['teufel']['button_value'],
      config['teufel']['button_read']
    ], [1, 0, 0])
    button_release()

@debounce(0.2)
def button_release():
    print('button_release')
    GPIO.output([
        config['teufel']['out_shared'],
        config['teufel']['button_value'],
        config['teufel']['button_read']
    ], [1, 1, 0])

def mqtt_on_connect(client, userdata, flags, rc):
    """@type client: paho.mqtt.client """
    print("Connection returned result: " + str(rc))
    client.subscribe('teufel/command', 0)

def mqtt_on_message(client, userdata, message):
    """@type client: paho.mqtt.client """

    try:
        action = message.payload.decode()
        if action == 'volume_up':
            volume_up()
            return

        if action == 'volume_down':
            volume_down()
            return

        if action == 'power_button_pressed':
            button_press()
            return

        if action == 'power_button_released':
            button_release()
            return

        raise Exception("Unknown command (%s)" % action)

    except Exception as e:
        print("Error during processing of message: ", message.topic, message.payload, str(e))

def cleanup():
    mqtt_client.loop_stop()
    mqtt_client.disconnect()
    GPIO.cleanup()

try:
    ### Parse config ###
    try:
        Config = ConfigParser.SafeConfigParser()
        if Config.read("config.ini"):

            # Load all sections and overwrite default configuration
            for section in Config.sections():
                config[section].update(dict(Config.items(section)))

        # Environment variables
        for section in config:
            for key, value in config[section].items():
                env = os.getenv(section.upper() + '_' + key.upper());
                if env:
                    config[section][key] = type(value)(env)

    except Exception as e:
        print("ERROR: Could not configure:", str(e))
        exit(1)

    ### Setup Teufel ###
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(config['teufel']['out_a'], GPIO.OUT, initial=1)
    GPIO.setup(config['teufel']['out_b'], GPIO.OUT, initial=1)
    GPIO.setup(config['teufel']['out_shared'], GPIO.OUT, initial=1)
    GPIO.setup(config['teufel']['button_read'], GPIO.OUT, initial=1)
    GPIO.setup(config['teufel']['button_value'], GPIO.OUT, initial=1)

    ### Setup MQTT ###
    print("Initialising MQTT...")
    mqtt_client = mqtt.Client(config['mqtt']['devicename'])
    mqtt_client.on_connect = mqtt_on_connect
    mqtt_client.on_message = mqtt_on_message
    if config['mqtt']['user']:
        mqtt_client.username_pw_set(config['mqtt']['user'], password=config['mqtt']['password']);
    if int(config['mqtt']['tls']) == 1:
        mqtt_client.tls_set();
    mqtt_client.connect(config['mqtt']['broker'], int(config['mqtt']['port']), 60)
    mqtt_client.loop_forever()
    print("Starting main loop...")
    while True:
        time.sleep(10)

except KeyboardInterrupt:
    cleanup()

except RuntimeError:
    cleanup()
