from opentrons import protocol_api

# metadata
metadata = {
    'protocolName': 'S3 Station C Version 1',
    'author': 'Nick <protocols@opentrons.com>, Sara <smonzon@isciii.es>, Miguel <mjuliam@isciii.es>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.1'
}

"""
NUM_SAMPLES is the number of samples, must be an integer number

ELUTION_LABWARE must be one of the following:
    opentrons plastic 2ml tubes
    opentrons plastic 1.5ml tubes
    opentrons aluminum 2ml tubes
    opentrons aluminum 1.5ml tubes
    covidwarriors aluminum 2ml tubes
    covidwarriors aluminum 1.5ml tubes
    opentrons aluminum biorad plate
    opentrons aluminum nest plate
    covidwarriors aluminum biorad plate
    opentrons aluminum strip alpha
    opentrons aluminum strip short
    covidwarriors aluminum biorad strip alpha
    covidwarriors aluminum biorad strip short

PCR_LABWARE must be one of the following:
    opentrons aluminum biorad plate
    opentrons aluminum nest plate
    covidwarriors aluminum biorad plate

MM_LABWARE must be one of the following:
    opentrons plastic block
    pentrons aluminum block
    covidwarriors aluminum block

PREPARE_MASTERMIX: True or False

TRANSFER_MASTERMIX: True or False

TRANSFER_SAMPLES: True or False

MM_TYPE must be one of the following:
    MM1
    MM2
    MM3
"""

NUM_SAMPLES = 96
ELUTION_LABWARE = 'opentrons aluminum strip short'
PCR_LABWARE = 'opentrons aluminum nest'
MM_LABWARE = 'opentrons aluminum block'
PREPARE_MASTERMIX = False
TRANSFER_MASTERMIX = False
TRANSFER_SAMPLES = True
MM_TYPE = 'MM3'

EL_LW_DICT = {
    # tubes
    'opentrons plastic 2ml tubes': 'opentrons_24_tuberack_generic_2ml_screwcap',
    'opentrons plastic 1.5ml tubes': 'opentrons_24_tuberack_nest_1.5ml_screwcap',
    'opentrons aluminum 2ml tubes': 'opentrons_24_aluminumblock_generic_2ml_screwcap',
    'opentrons aluminum 1.5ml tubes': 'opentrons_24_aluminumblock_nest_1.5ml_screwcap',
    'covidwarriors aluminum 2ml tubes': 'covidwarriors_aluminumblock_24_screwcap_2000ul',
    'covidwarriors aluminum 1.5ml tubes': 'covidwarriors_aluminumblock_24_screwcap_2000ul',
    # PCR plate
    'opentrons aluminum biorad plate': 'opentrons_96_aluminumblock_biorad_wellplate_200ul',
    'opentrons aluminum nest plate': 'opentrons_96_aluminumblock_nest_wellplate_100ul',
    'covidwarriors aluminum biorad plate': 'covidwarriors_aluminumblock_96_bioradwellplate_200ul',
    # Strips
    #'large strips': 'opentrons_96_aluminumblock_generic_pcr_strip_200ul',
    #'short strips': 'opentrons_96_aluminumblock_generic_pcr_strip_200ul',
    'opentrons aluminum strip alpha': 'opentrons_aluminumblock_96_pcrstripsalpha_200ul',
    'opentrons aluminum strip short': 'opentrons_aluminumblock_96_pcrstrips_100ul',
    'covidwarriors aluminum biorad strip alpha': 'covidwarriors_aluminumblock_96_bioradwellplate_pcrstripsalpha_200ul',
    'covidwarriors aluminum biorad strip short': 'covidwarriors_aluminumblock_96_bioradwellplate_pcrstrips_100ul'
}

PCR_LW_DICT = {
    'opentrons aluminum biorad': 'opentrons_96_aluminumblock_biorad_wellplate_200ul',
    'opentrons aluminum nest': 'opentrons_96_aluminumblock_nest_wellplate_100ul',
    'covidwarriors aluminum biorad': 'covidwarriors_aluminumblock_96_bioradwellplate_200ul'
}

MM_LW_DICT = {
    'opentrons plastic block': 'opentrons_24_tuberack_generic_2ml_screwcap',
    'opentrons aluminum block': 'opentrons_24_aluminumblock_generic_2ml_screwcap',
    'covidwarriors aluminum block': 'covidwarriors_aluminumblock_24_screwcap_2000ul'
}

def run(ctx: protocol_api.ProtocolContext):

    # check source (elution) labware type
    if ELUTION_LABWARE not in EL_LW_DICT:
        raise Exception('Invalid ELUTION_LABWARE. Must be one of the \
following:\nopentrons plastic 2ml tubes\nopentrons plastic 1.5ml tubes\nopentrons aluminum 2ml tubes\nopentrons aluminum 1.5ml tubes\ncovidwarriors aluminum 2ml tubes\ncovidwarriors aluminum 1.5ml tubes\nopentrons aluminum biorad plate\nopentrons aluminum nest plate\ncovidwarriors aluminum biorad plate\nopentrons aluminum strip alpha\nopentrons aluminum strip short\ncovidwarriors aluminum biorad strip alpha\ncovidwarriors aluminum biorad strip short')

    if 'plate' in ELUTION_LABWARE:
        source_racks = ctx.load_labware(
            EL_LW_DICT[ELUTION_LABWARE], '1',
            'RNA elution labware')
    else:
        source_racks = [
            ctx.load_labware(EL_LW_DICT[ELUTION_LABWARE], slot,
                            'RNA elution labware ' + str(i+1))
            for i, slot in enumerate(['4', '1', '5', '2'])
    ]

    # tips
    tips20 = [
        ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
        for slot in ['6', '9', '8', '7']
    ]
    tips300 = [ctx.load_labware('opentrons_96_filtertiprack_200ul', '3')]

    # tempdeck module
    tempdeck = ctx.load_module('tempdeck', '10')
    tempdeck.set_temperature(24)

    # check pcr plate
    if PCR_LABWARE not in PCR_LW_DICT:
        raise Exception('Invalid MM_LABWARE. Must be one of the \
following:\nopentrons aluminum biorad\nopentrons aluminum block\ncovidwarriors aluminum biorad')

    pcr_plate = tempdeck.load_labware(
        PCR_LW_DICT[PCR_LABWARE], 'PCR plate')

    # check mastermix labware type
    if MM_LABWARE not in MM_LW_DICT:
        raise Exception('Invalid MM_LABWARE. Must be one of the \
following:\nopentrons plastic block\nopentrons aluminum block\ncovidwarriors aluminum block')

    mm_rack = ctx.load_labware(
        MM_LW_DICT[MM_LABWARE], '11',
        MM_LABWARE)

    # pipette
    p20 = ctx.load_instrument('p20_single_gen2', 'right', tip_racks=tips20)
    p300 = ctx.load_instrument('p300_single_gen2', 'left', tip_racks=tips300)

    # setup up sample sources and destinations
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

    if PREPARE_MASTERMIX:
        """ mastermix component maps """
        mm1 = {
            tube: vol
            for tube, vol in zip(
                [well for col in mm_rack.columns()[2:5] for well in col][:10],
                [2.85, 12.5, 0.4, 1, 1, 0.25, 0.25, 0.5, 0.25, 1]
            )
        }
        mm2 = {
            tube: vol
            for tube, vol in zip(
                [mm_rack.wells_by_name()[well] for well in ['A3', 'C5', 'D5']],
                [10, 4, 1]
            )
        }
        mm3 = {
            tube: vol
            for tube, vol in zip(
                [mm_rack.wells_by_name()[well] for well in ['A6', 'B6']],
                [13, 2]
            )
        }
        mm_dict = {'MM1': mm1, 'MM2': mm2, 'MM3': mm3}

        # create mastermix
        if MM_TYPE == 'mm3':
            VOLUME_MMIX = 15
        else:
            VOLUME_MMIX = 20
        mm_tube = mm_rack.wells()[0]
        for tube, vol in mm_dict[MM_TYPE].items():
            mm_vol = vol*(NUM_SAMPLES+5)
            disp_loc = mm_tube.bottom(5) if mm_vol < 50 else mm_tube.top(-5)
            pip = p300 if mm_vol > 20 else p20
            pip.pick_up_tip()
            pip.transfer(mm_vol, tube.bottom(2), disp_loc, air_gap=1, new_tip='never')
            pip.blow_out(mm_tube.bottom(5))
            pip.aspirate(5, mm_tube.top(2))
            pip.drop_tip()
        p300.pick_up_tip()
        p300.mix(5, 200, mm_tube.bottom(2))
        p300.drop_tip()
    else:
        mm_tube = mm_rack.wells()[0]

    # transfer mastermix
    if TRANSFER_MASTERMIX:
        max_trans_per_asp = 8  #230//(VOLUME_MMIX+5)
        split_ind = [ind for ind in range(0, NUM_SAMPLES, max_trans_per_asp)]
        dest_sets = [dests[split_ind[i]:split_ind[i+1]]
                 for i in range(len(split_ind)-1)] + [dests[split_ind[-1]:]]

        pip = p300 if VOLUME_MMIX >= 20 else p20
        pip.pick_up_tip()
        for set in dest_sets:
            pip.distribute(VOLUME_MMIX, mm_tube, [d.bottom(2) for d in set],
                       air_gap=1, disposal_volume=0, new_tip='never')
        pip.drop_tip()

    # transfer samples to corresponding locations
    if TRANSFER_SAMPLES:
        for s, d in zip(sources, dests):
            p20.pick_up_tip()
            p20.transfer(5, s.bottom(1), d.bottom(2), air_gap=2, new_tip='never')
            #p20.mix(1, 10, d.bottom(2))
            #p20.blow_out(d.top(-2))
            p20.aspirate(1, d.top(2))
            p20.drop_tip()
