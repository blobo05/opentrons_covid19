from opentrons import protocol_api
from opentrons.drivers.rpi_drivers import gpio
import time
import math
import json
import os

# metadata
metadata = {
    'protocolName': 'S3 Station A Version 1',
    'author': 'Nick <protocols@opentrons.com>, Sara <smonzon@isciii.es>, Miguel <mjuliam@isciii.es>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.2'
}


# Parameters to adapt the protocol
NUM_SAMPLES = 96
BEADS_LABWARE = 'opentrons plastic 50 ml tubes'
PLATE_LABWARE = 'opentrons deep generic well plate'

"""
NUM_SAMPLES is the number of samples, must be an integer number

BEADS_LABWARE must be one of the following:
    opentrons plastic 50 ml tubes

PLATE_LABWARE must be one of the following:
    opentrons deep generic well plate
    nest deep generic well plate
    vwr deep generic well plate
"""

BD_LW_DICT = {
    'opentrons plastic 50 ml tubes': 'opentrons_6_tuberack_falcon_50ml_conical'
}

PL_LW_DICT = {
    'opentrons deep generic well plate': 'usascientific_96_wellplate_2.4ml_deep',
    'nest deep generic well plate': 'usascientific_96_wellplate_2.4ml_deep',
    'vwr deep generic well plate': 'usascientific_96_wellplate_2.4ml_deep'
}

# Function definitions
def check_door():
    return gpio.read_window_switches()

def confirm_door_is_closed(ctx):
    #Check if door is opened
    if check_door() == False:
        #Set light color to red and pause
        gpio.set_button_light(1,0,0)
        ctx.pause(f"Please, close the door")
        time.sleep(3)
        confirm_door_is_closed(ctx)
    else:
        #Set light color to green
        gpio.set_button_light(0,1,0)

def finish_run():
    #Set light color to blue
    gpio.set_button_light(0,0,1)

def retrieve_tip_info(pip,tipracks,file_path = '/data/A/tip_log.json'):
    global tip_log
    if not tip_log or pip not in tip_log['count']:
        if not robot.is_simulating():
            if os.path.isfile(file_path):
                with open(file_path) as json_file:
                    data = json.load(json_file)
                    if 'tips1000' in data:
                        tip_log['count'][pip] = data['tips1000']
                    else:
                        tip_log['count'][pip] = 0
                    if 'tips300' in data:
                        tip_log['count'][pip] = data['tips300']
                    else:
                        tip_log['count'][pip] = 0
            else:
                tip_log['count'][pip] = 0
        else:
            tip_log['count'][pip] = 0

        if "8-Channel" in str(pip):
            tip_log['tips'][pip] =  [tip for rack in tipracks for tip in rack.rows()[0]]
        else:
            tip_log['tips'][pip] = [tip for rack in tipracks for tip in rack.wells()]

        tip_log['max'][pip] = len(tip_log['tips'][pip])

    return tip_log

def save_tip_info(pip, file_path = '/data/A/tip_log.json'):
    if not robot.is_simulating():
        if "P1000" in str(pip):
            data = {'tips1000': tip_log['count'][pip]}
        elif "P300" in str(pip):
            data = {'tips300': tip_log['count'][pip]}

        with open(file_path, 'w') as outfile:
            json.dump(data, outfile)

def pick_up(pip,tiprack):
    ## retrieve tip_log
    global tip_log
    if not tip_log:
        tip_log = {}
    tip_log = retrieve_tip_info(pip,tiprack)
    if tip_log['count'][pip] == tip_log['max'][pip]:
        robot.pause('Replace ' + str(pip.max_volume) + 'µl tipracks before \
resuming.')
        pip.reset_tipracks()
        tip_log['count'][pip] = 0
    pip.pick_up_tip(tip_log['tips'][pip][tip_log['count'][pip]])
    tip_log['count'][pip] += 1

def get_source_dest_coordinates(ELUTION_LABWARE, source_racks, pcr_plate):
    if 'strip' in ELUTION_LABWARE:
        sources = [
            tube
            for i, rack in enumerate(source_racks)
            for col in [
                rack.columns()[c] if i < 2 else rack.columns()[c+1]
                for c in [0, 5, 10]
            ]
            for tube in col
        ][:NUM_SAMPLES]
        dests = pcr_plate.wells()[:NUM_SAMPLES]
    elif 'plate' in ELUTION_LABWARE:
        sources = source_racks.wells()[:NUM_SAMPLES]
        dests = pcr_plate.wells()[:NUM_SAMPLES]
    else:
        sources = [
            tube
            for rack in source_racks for tube in rack.wells()][:NUM_SAMPLES]
        dests = [
            well
            for v_block in range(2)
            for h_block in range(2)
            for col in pcr_plate.columns()[6*v_block:6*(v_block+1)]
            for well in col[4*h_block:4*(h_block+1)]][:NUM_SAMPLES]
    return sources, dests

def transfer_samples(ELUTION_LABWARE, sources, dests, pip, tiprack):
    # height for aspiration has to be different depending if you ar useing tubes or wells
    if 'strip' in ELUTION_LABWARE or 'plate' in ELUTION_LABWARE:
        height = 1.5
    else:
        height = 2
    # transfer
    for s, d in zip(sources, dests):
        pick_up(pip,tiprack)
        pip.transfer(400, s.bottom(height), d.bottom(15), air_gap=2, new_tip='never')
        pip.blow_out(d.top(-2))
        pip.aspirate(50, d.top(-2))
        pip.drop_tip()

# RUN PROTOCOL
def run(ctx: protocol_api.ProtocolContext):

    # confirm door is closed
    if not ctx.is_simulating():
        confirm_door_is_closed(ctx)

    tips1000 = [ctx.load_labware('opentrons_96_filtertiprack_1000ul',
                                     slot, '1000µl tiprack')
                    for slot in ['3', '6', '9', '8', '7']]

    # load pipette
    p1000 = ctx.load_instrument(
        'p1000_single_gen2', 'left', tip_racks=tips1000)

    # check source (elution) labware type
    if ELUTION_LABWARE not in EL_LW_DICT:
        raise Exception('Invalid ELUTION_LABWARE. Must be one of the \
following:\nopentrons plastic 2ml tubes')
    # load elution labware
    if 'plate' in ELUTION_LABWARE:
        source_racks = ctx.load_labware(
            EL_LW_DICT[ELUTION_LABWARE], '1',
            'RNA elution labware')
    else:
        source_racks = [
            ctx.load_labware(EL_LW_DICT[ELUTION_LABWARE], slot,
                            'sample elution labware ' + str(i+1))
            for i, slot in enumerate(['4', '1', '5', '2'])
    ]

    # check plate
    if PLATE_LABWARE not in PL_LW_DICT:
        raise Exception('Invalid PLATE_LABWARE. Must be one of the \
following:\nhigh generic well plate')
    # load pcr plate
    wells_plate = ctx.load_labware(PL_LW_DICT[PLATE_LABWARE], 10,
                    'sample elution well plate ')

    # setup samples
    sources, dests = get_source_dest_coordinates(ELUTION_LABWARE, source_racks, wells_plate)

    # transfer
    transfer_samples(ELUTION_LABWARE, sources, dests, p1000, tips1000)

    # track final used tip
    save_tip_info(p1000)

    finish_run()
