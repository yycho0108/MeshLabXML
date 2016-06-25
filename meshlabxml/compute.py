""" MeshLabXML measurement and computation functions """

from . import util


def section(script='TEMP3D_default.mlx', axis='z', offset=0.0,
            surface=False, custom_axis=None, planeref=2,
            current_layer=None, last_layer=None):

    # TIP: surfaces can also be simplified after generation
    # Recommended output formats:
    # surface: stl, obj
    # line: dxf, obj (need to process obj) - note: creates a 1D outline composed
    # of line segments (not a continuous polyline but individual segments)
    # points: xyz (for measuring size)

    # Convert axis name into number
    if axis.lower() == 'x':
        axis_num = 0
    elif axis.lower() == 'y':
        axis_num = 1
    elif axis.lower() == 'z':
        axis_num = 2
    else:  # custom axis
        axis_num = 3
        if custom_axis is None:
            print('WARNING: a custom axis was selected, however',
                  '"custom_axis" was not provided. Using default (Z).')
    if custom_axis is None:
        custom_axis = [0.0, 0.0, 1.0]
    script_file = open(script, 'a')
    script_file.write('  <filter name="Compute Planar Section">\n' +

                      '    <Param name="planeAxis" ' +
                      'value="%d" ' % axis_num +
                      'description="Plane perpendicular to" ' +
                      'enum_val0="X Axis" ' +
                      'enum_val1="Y Axis" ' +
                      'enum_val2="Z Axis" ' +
                      'enum_val3="Custom Axis" ' +
                      'enum_cardinality="4" ' +
                      'type="RichEnum" ' +
                      'tooltip="The Slicing plane will be done perpendicular to the' +
                      ' axis"/>\n' +

                      '    <Param name="customAxis" ' +
                      'x="%s" y="%s" z="%s" ' % (custom_axis[0], custom_axis[1],
                                                 custom_axis[2]) +
                      'description="Custom axis" ' +
                      'type="RichPoint3f" ' +
                      'tooltip="Specify a custom axis, this is only valid if the' +
                      ' above parameter is set to Custom"/>\n' +

                      '    <Param name="planeOffset" ' +
                      'value="%s" ' % offset +
                      'description="Cross plane offset" ' +
                      'type="RichFloat" ' +
                      'tooltip="Specify an offset of the cross-plane. The offset' +
                      ' corresponds to the distance from the point specified in the' +
                      ' plane reference parameter."/>\n' +

                      '    <Param name="relativeTo" ' +
                      'value="%s" ' % planeref +
                      'description="plane reference" ' +
                      'enum_val0="Bounding box center" ' +
                      'enum_val1="Bounding box min" ' +
                      'enum_val2="Origin" ' +
                      'enum_cardinality="3" ' +
                      'type="RichEnum" ' +
                      'tooltip="Specify the reference from which the planes are' +
                      ' shifted"/>\n' +

                      '    <Param name="createSectionSurface" ' +
                      'value="%s" ' % str(surface).lower() +
                      'description="Create also section surface" ' +
                      'type="RichBool" ' +
                      'tooltip="If selected, in addition to a layer with the section' +
                      ' polyline, it will be created also a layer with a' +
                      ' triangulated version of the section polyline. This only' +
                      ' works if the section polyline is closed"/>\n' +

                      '  </filter>\n')
    script_file.close()
    return current_layer, last_layer


def measure_geometry(script='TEMP3D_default.mlx',
                     current_layer=None, last_layer=None):
    script_file = open(script, 'a')
    script_file.write('  <xmlfilter name="Compute Geometric Measures"/>\n')
    script_file.close()
    return current_layer, last_layer


def measure_topology(script='TEMP3D_default.mlx',
                     current_layer=None, last_layer=None):
    script_file = open(script, 'a')
    script_file.write('  <xmlfilter name="Compute Topological Measures"/>\n')
    script_file.close()
    return current_layer, last_layer


def parse_geometry(ml_log, log=None):
    """Parse the ml_log file generated by the measure_geometry function.

    Warnings: Not all keys may exist if mesh is not watertight or manifold"""
    geometry = {}
    with open(ml_log) as fread:
        for line in fread:
            if 'Mesh Volume' in line:
                line = ' '.join(line.split())  # remove extra whitespace
                geometry['volume_mm3'] = util.to_float(line.split()[3])
                geometry['volume_cm3'] = geometry['volume_mm3'] * 0.001
            if 'Mesh Surface' in line:
                line = ' '.join(line.split())  # remove extra whitespace
                geometry['area_mm2'] = util.to_float(line.split()[3])
                geometry['area_cm2'] = geometry['area_mm2'] * 0.01
            if 'Mesh Total Len of' in line:
                line = ' '.join(line.split())  # remove extra whitespace
                #print(line.split(' '))
                if 'including faux edges' in line:
                    geometry['total_edge_length_incl_faux'] = util.to_float(
                        line.split()[7])
                else:
                    geometry['total_edge_length'] = util.to_float(
                        line.split()[7])
            if 'Thin shell barycenter' in line:
                line = ' '.join(line.split())  # remove extra whitespace
                geometry['barycenter'] = (line.split()[3:6])
                geometry['barycenter'] = [
                    util.to_float(val) for val in geometry['barycenter']]
            if 'Center of Mass' in line:
                line = ' '.join(line.split())  # remove extra whitespace
                geometry['center_of_mass'] = (line.split()[4:7])
                geometry['center_of_mass'] = [
                    util.to_float(val) for val in geometry['center_of_mass']]
            if 'Inertia Tensor' in line:
                geometry['inertia_tensor'] = []
                for val in range(3):
                    # remove extra whitespace
                    row = ' '.join(next(fread, val).split())
                    row = (row.split(' ')[1:4])
                    row = [util.to_float(b) for b in row]
                    geometry['inertia_tensor'].append(row)
            if 'Principal axes' in line:
                geometry['principal_axes'] = []
                for val in range(3):
                    # remove extra whitespace
                    row = ' '.join(next(fread, val).split())
                    row = (row.split(' ')[1:4])
                    row = [util.to_float(b) for b in row]
                    geometry['principal_axes'].append(row)
            if 'axis momenta' in line:
                line = ' '.join(next(fread).split())  # remove extra whitespace
                geometry['axis_momenta'] = (line.split(' ')[1:4])
                geometry['axis_momenta'] = [
                    util.to_float(val) for val in geometry['axis_momenta']]
                break  # stop after we find the first match
    if log is None:
        print('volume_mm3 =', geometry['volume_mm3'],
              'volume_cm3 =', geometry['volume_cm3'])
        print('area_mm2 =', geometry['area_mm2'],
              'area_cm2 =', geometry['area_cm2'])
        print('barycenter =', geometry['barycenter'])
        print('center_of_mass =', geometry['center_of_mass'])
        print('inertia_tensor =', geometry['inertia_tensor'])
        print('principal_axes =', geometry['principal_axes'])
        print('axis_momenta =', geometry['axis_momenta'])
        print('total_edge_length_incl_faux =',
              geometry['total_edge_length_incl_faux'])
        print('total_edge_length =', geometry['total_edge_length'])
    else:
        log_file = open(log, 'a')
        if 'volume_mm3' in geometry:
            log_file.write('volume_mm3 = %s, volume_cm3 = %s\n'
                           % (geometry['volume_mm3'], geometry['volume_cm3']))
        if 'area_mm2' in geometry:
            log_file.write(''.join(['area_mm2 = %s, area_cm2 = %s\n'
                           % (geometry['area_mm2'], geometry['area_cm2']),
                           'total_edge_length = %s\n'
                           % geometry['total_edge_length'],
                           'total_edge_length_incl_faux = %s\n'
                           % geometry['total_edge_length_incl_faux']]))
        if 'barycenter' in geometry:
            log_file.write('barycenter = %s\n' % geometry['barycenter'])
        if 'center_of_mass' in geometry:
            log_file.write('center_of_mass = %s\n'
                           % geometry['center_of_mass'])
        if 'inertia_tensor' in geometry:
            log_file.write(''.join(['inertia_tensor =\n',
                           '  %s\n' % geometry['inertia_tensor'][0],
                           '  %s\n' % geometry['inertia_tensor'][1],
                           '  %s\n' % geometry['inertia_tensor'][2]]))
        if 'principal_axes' in geometry:
            log_file.write(''.join(['principal_axes =\n',
                           '  %s\n' % geometry['principal_axes'][0],
                           '  %s\n' % geometry['principal_axes'][1],
                           '  %s\n' % geometry['principal_axes'][2]]))
        if 'axis_momenta' in geometry:
            log_file.write('axis_momenta = %s\n' % geometry['axis_momenta'])
        if 'total_edge_length_incl_faux' in geometry:
            log_file.write('total_edge_length_incl_faux = %s\n'
                           % geometry['total_edge_length_incl_faux'])
        if 'total_edge_length' in geometry:
            log_file.write('total_edge_length = %s\n\n'
                           % geometry['total_edge_length'])
        log_file.close()
    return geometry


def parse_topology(ml_log, log=None):
    """Parse the ml_log file generated by the measure_topology function.

    Warnings: Not all keys may exist"""
    topology = {'manifold': True, 'non_manifold_E': 0, 'non_manifold_V': 0}
    with open(ml_log) as fread:
        for line in fread:
            if 'V:' in line:
                line = ' '.join(line.split())  # remove extra whitespace
                topology['vert_num'] = int(line.split()[1])
                topology['edge_num'] = int(line.split()[3])
                topology['face_num'] = int(line.split()[5])
            if 'Unreferenced Vertices' in line:
                line = ' '.join(line.split())  # remove extra whitespace
                topology['unref_vert_num'] = int(line.split()[2])
            if 'Boundary Edges' in line:
                line = ' '.join(line.split())  # remove extra whitespace
                topology['boundry_edge_num'] = int(line.split()[2])
            if 'Mesh is composed by' in line:
                line = ' '.join(line.split())  # remove extra whitespace
                topology['part_num'] = int(line.split()[4])
            if 'non 2-manifold mesh' in line:
                topology['manifold'] = False
            if 'non two manifold edges' in line:
                line = ' '.join(line.split())  # remove extra whitespace
                topology['non_manifold_edge'] = int(line.split()[2])
            if 'non two manifold vertexes' in line:
                line = ' '.join(line.split())  # remove extra whitespace
                topology['non_manifold_vert'] = int(line.split()[2])
            if 'Genus is' in line:  # undefined or int
                line = ' '.join(line.split())  # remove extra whitespace
                topology['genus'] = line.split()[2]
                if topology['genus'] != 'undefined':
                    topology['genus'] = int(topology['genus'])
            if 'holes' in line:
                line = ' '.join(line.split())  # remove extra whitespace
                topology['hole_num'] = line.split()[2]
                if topology['hole_num'] == 'a':
                    topology['hole_num'] = 'undefined'
                else:
                    topology['hole_num'] = int(topology['hole_num'])
    if log is None:
        print('\nvert_num = %d, ' % topology['vert_num'],
              'edge_num = %d, ' % topology['edge_num'],
              'face_num = %d' % topology['face_num'])
        print('part_num = %d\n' % topology['part_num'])
        print('manifold (two-manifold) = %s\n' % topology['manifold'])
        print('hole_num = %d\n' % topology['hole_num'])
        print('boundry_edge_num = %d\n' % topology['boundry_edge_num'])
        print('unref_vert_num = %d\n' % topology['unref_vert_num'])
        print('non_manifold_vert = %d\n' % topology['non_manifold_vert'])
        print('non_manifold_edge = %d\n' % topology['non_manifold_edge'])
        print('genus = %d\n' % topology['genus'])
    else:
        log_file = open(log, 'a')
        if 'vert_num' in topology:
            log_file.write('vert_num = %d\n' % topology['vert_num'])
            log_file.write('edge_num = %d\n' % topology['edge_num'])
            log_file.write('face_num = %d\n' % topology['face_num'])
        if 'part_num' in topology:
            log_file.write('part_num = %d\n' % topology['part_num'])
        if 'manifold' in topology:
            log_file.write('manifold (two-manifold) = %s\n'
                           % topology['manifold'])
        if 'hole_num' in topology:
            log_file.write('hole_num = %d\n' % topology['hole_num'])
        if 'boundry_edge_num' in topology:
            log_file.write('boundry_edge_num = %d\n'
                           % topology['boundry_edge_num'])
        if 'unref_vert_num' in topology:
            log_file.write('unref_vert_num = %d\n'
                           % topology['unref_vert_num'])
        if 'non_manifold_vert' in topology:
            log_file.write('non_manifold_vert = %d\n'
                           % topology['non_manifold_vert'])
        if 'non_manifold_edge' in topology:
            log_file.write('non_manifold_edge = %d\n'
                           % topology['non_manifold_edge'])
        if 'genus' in topology:
            log_file.write('genus = %d\n' % topology['genus'])
    return topology
