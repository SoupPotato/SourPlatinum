import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE)
import underground_block_builder as ub

OUT = os.path.join(REPO, 'res', 'field', 'maps', 'texture_sets', 'map_texture_set_002.nsbtx')
WORK = os.path.join(REPO, 'build', 'underground_import')
TEXTURES = [
    ('himitu_floor', None), ('himitu_kiwa', None), ('himitu_wall', None), ('himitu_wall2', None),
    ('ug_floor', None), ('ug_map_wall', 48), ('ug_wall_stem', None), ('ug_wall_stem2', None),
    ('dun_dhole', None), ('dun_ent2', None),
]


def main():
    conv = ub.find_converter()
    if not conv:
        print('g3dcvtr.exe not found; set G3DCVTR to its path')
        return 1
    tex_xml, pal_xml, mat_xml, poly_xml, disp_xml = [], [], [], [], []
    for i, (name, oh) in enumerate(TEXTURES):
        tex, pal, w, h = ub.texture_xml(i, name, oh)
        tex_xml.append(tex)
        pal_xml.append(pal)
        mat_xml.append('      <material index="%d" name="m_%s" light0="off" light1="off" light2="off" light3="off" face="front" alpha="31" '
                       'wire_mode="off" polygon_mode="modulate" polygon_id="0" fog_flag="on" depth_test_decal="off" '
                       'translucent_update_depth="off" render_1_pixel="off" far_clipping="off" diffuse="31 31 31" ambient="0 0 0" '
                       'specular="0 0 0" emission="0 0 0" shininess_table_flag="off" tex_image_idx="%d" tex_palette_idx="%d" '
                       'tex_tiling="repeat repeat" tex_scale="1.000000 1.000000" tex_rotate="0.000000" tex_translate="0.000000 0.000000" '
                       'tex_gen_mode="none"/>' % (i, name, i, i))
        cmds = []
        for x, z, s, t in ((0.0, 0.0, 0.0, 0.0), (0.1, 0.0, 1.0, 0.0), (0.0, 0.1, 0.0, 1.0)):
            cmds.append('            <tex st="%f %f"/>' % (s, t))
            cmds.append('            <pos_xyz xyz="%f 0.000000 %f"/>' % (x, z))
        poly_xml.append('      <polygon index="%d" name="polygon%d" vertex_size="3" polygon_size="1" triangle_size="1" quad_size="0" '
                        'volume_min="0.000000 0.000000 0.000000" volume_max="0.000000 0.000000 0.000000" volume_r="0.000000" '
                        'mtx_prim_size="1" nrm_flag="off" clr_flag="off" tex_flag="on">\n        <mtx_prim index="0">\n'
                        '          <mtx_list size="1">0</mtx_list>\n          <primitive_array size="1">\n'
                        '            <primitive index="0" type="triangles" vertex_size="3">\n            <mtx idx="0"/>\n%s\n'
                        '            </primitive>\n          </primitive_array>\n        </mtx_prim>\n      </polygon>' % (i, i, '\n'.join(cmds)))
        disp_xml.append('        <display index="%d" material="%d" polygon="%d" priority="0"/>' % (i, i, i))
    n = len(TEXTURES)
    xml = '\n'.join([
        '<?xml version="1.0" encoding="UTF-8"?>', '<imd version="1.6.0">', '  <head>',
        '    <create user="unknown" host="unknown" date="2026-01-01T00:00:00" source="underground_textures"/>',
        '    <title>Model Data for NINTENDO NITRO-System</title>',
        '    <generator name="underground_block_builder" version="1.0"/>', '  </head>', '  <body>',
        '    <original_create user="unknown" host="unknown" date="2026-01-01T00:00:00" source="underground_textures"/>',
        '    <original_generator name="underground_block_builder" version="1.0"/>',
        '    <model_info pos_scale="0" scaling_rule="standard" vertex_style="direct" magnify="1.000000" tool_start_frame="1" '
        'tex_matrix_mode="maya" compress_node="merge" node_size="1 1" compress_material="off" material_size="%d %d" '
        'output_texture="used" force_full_weight="off" use_primitive_strip="on"/>' % (n, n),
        '    <box_test pos_scale="0" xyz="0.000000 0.000000 0.000000" whd="0.100000 0.000000 0.100000"/>',
        '    <tex_image_array size="%d">' % n, '\n'.join(tex_xml), '    </tex_image_array>',
        '    <tex_palette_array size="%d">' % n, '\n'.join(pal_xml), '    </tex_palette_array>',
        '    <material_array size="%d">' % n, '\n'.join(mat_xml), '    </material_array>',
        '    <matrix_array size="1">', '      <matrix index="0" mtx_weight="1" node_idx="0"/>', '    </matrix_array>',
        '    <polygon_array size="%d">' % n, '\n'.join(poly_xml), '    </polygon_array>',
        '    <node_array size="1">',
        '      <node index="0" name="world_root" kind="mesh" parent="-1" child="-1" brother_next="-1" brother_prev="-1" draw_mtx="on" '
        'billboard="off" scale="1.000000 1.000000 1.000000" rotate="0.000000 0.000000 0.000000" translate="0.000000 0.000000 0.000000" '
        'visibility="on" display_size="%d" vertex_size="%d" polygon_size="%d" triangle_size="%d" quad_size="0" '
        'volume_min="0.000000 0.000000 0.000000" volume_max="0.000000 0.000000 0.000000" volume_r="0.000000">' % (n, 3 * n, n, n),
        '\n'.join(disp_xml), '      </node>', '    </node_array>',
        '    <output_info vertex_size="%d" polygon_size="%d" triangle_size="%d" quad_size="0"/>' % (3 * n, n, n),
        '  </body>', '</imd>', ''])
    os.makedirs(WORK, exist_ok=True)
    imd = os.path.join(WORK, 'underground_textures.imd')
    out = os.path.join(WORK, 'underground_textures.nsbtx')
    open(imd, 'w', encoding='utf-8').write(xml)
    if os.path.exists(out):
        os.remove(out)
    run = subprocess.run([conv, imd, '-etex', '-o', out], cwd=os.path.dirname(conv), capture_output=True, text=True)
    if not os.path.exists(out):
        print(run.stdout)
        print(run.stderr)
        return 1
    open(OUT, 'wb').write(open(out, 'rb').read())
    print('wrote %s (%d bytes, %d textures)' % (os.path.relpath(OUT, REPO), os.path.getsize(OUT), n))
    return 0


if __name__ == '__main__':
    sys.exit(main())
