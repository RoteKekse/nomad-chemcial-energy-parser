#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb  7 08:51:56 2023

@author: a2853
"""
import os
import inspect


def set_multiple_data(
        mainfile,
        entry_multiple_class,
        entry_properties_class,
        get_properties_function):

    from baseclasses.helper.gamry_parser import get_header_and_data
    from baseclasses.helper.gamry_archive import get_meta_data

    measurement_base, measurement_name = os.path.split(mainfile)
    measurement_name_overall = measurement_name.replace("_#1", "")
    measurements = entry_multiple_class()
    measurements.measurements = []
    batch = [
        measurement_name.replace(
            "_#1",
            f"_#{i}") for i in range(1000) if os.path.isfile(
            os.path.join(
                measurement_base,
                measurement_name.replace(
                    "_#1",
                    f"_#{i}")))]
    for i, filename in enumerate(batch):
        metadata, data = get_header_and_data(
            filename=os.path.join(measurement_base, filename))

        if i == 0:
            get_meta_data(metadata, measurements)

        measurement = entry_properties_class()
        get_properties_function(metadata, data[0], filename, measurement)
        measurement.name = filename
        measurements.measurements.append(measurement)

    return measurement_name_overall, measurements


def set_data(
        mainfile,
        entry_class,
        entry_properties_class,
        get_properties_function=None):

    from baseclasses.helper.gamry_parser import get_header_and_data
    from baseclasses.helper.gamry_archive import get_meta_data, get_voltammetry_data, get_eis_data
    from baseclasses.chemical_energy import VoltammetryCycle
    import baseclasses

    assert baseclasses.chemical_energy.voltammetry.Voltammetry \
        in inspect.getmro(entry_class) or \
        baseclasses.chemical_energy.electorchemical_impedance_spectroscopy.ElectrochemicalImpedanceSpectroscopy \
        in inspect.getmro(entry_class)

    measurement_base, measurement_name = os.path.split(mainfile)

    measurement = entry_class()
    measurement.data_file = measurement_name

    metadata, data = get_header_and_data(
        filename=mainfile)

    if "RINGCURVE" in metadata and baseclasses.chemical_energy.chronoamperometry.Chronoamperometry \
            in inspect.getmro(entry_class):
        data = [metadata["RINGCURVE"]]
    get_meta_data(metadata, measurement)

    if baseclasses.chemical_energy.voltammetry.Voltammetry \
            in inspect.getmro(entry_class):
        data_function = get_voltammetry_data

    if baseclasses.chemical_energy.electorchemical_impedance_spectroscopy.ElectrochemicalImpedanceSpectroscopy \
            in inspect.getmro(entry_class):
        data_function = get_eis_data

    if len(data) > 1:
        measurement.cycles = []
        for curve in data:
            cycle = VoltammetryCycle()
            data_function(
                curve, cycle)
            measurement.cycles.append(cycle)

    if len(data) == 1:
        data_function(
            data[0], measurement)

    properties = entry_properties_class()
    if get_properties_function is not None:
        get_properties_function(metadata, properties)
        measurement.properties = properties

    return measurement_name, measurement
