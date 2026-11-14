"""Render matched source PBR maps for resource review, outside the game.

Uses the same Blender Principled/normal-node adaptation as the existing
environment render-review.py. No AI color image is paired with guessed maps.
"""
from pathlib import Path
import json
import math
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'assets/materials/chapter-one-v3'
OUTPUT = BASE / 'review'


def look_at(obj, point):
    obj.rotation_euler = (Vector(point) - obj.location).to_track_quat('-Z', 'Y').to_euler()


def plain(name, color, roughness=0.8):
    material = bpy.data.materials.new(name)
    material.diffuse_color = (*color, 1)
    material.use_nodes = True
    principled = material.node_tree.nodes.get('Principled BSDF')
    principled.inputs['Base Color'].default_value = (*color, 1)
    principled.inputs['Roughness'].default_value = roughness
    return material


def pbr(definition, folder):
    material = bpy.data.materials.new(definition['id'])
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    principled = nodes.get('Principled BSDF')
    principled.inputs['Metallic'].default_value = definition.get('metallic', 0)
    texcoord = nodes.new('ShaderNodeTexCoord')
    mapping = nodes.new('ShaderNodeMapping')
    # Planes are exactly two metres across. Preserve the official material scale.
    tile = definition.get('tileMetres') or definition.get('previewTileMetres') or [2, 2]
    mapping.inputs['Scale'].default_value = (2 / tile[0], 2 / tile[1], 1)
    links.new(texcoord.outputs['UV'], mapping.inputs['Vector'])
    channels = {entry['role']: entry for entry in definition['maps']}
    for role, socket in [('albedo', 'Base Color'), ('roughness', 'Roughness'), ('normal', None)]:
        image = nodes.new('ShaderNodeTexImage')
        image.image = bpy.data.images.load(str(folder / channels[role]['file']), check_existing=True)
        image.image.colorspace_settings.name = 'sRGB' if role == 'albedo' else 'Non-Color'
        image.extension = 'REPEAT'
        links.new(mapping.outputs['Vector'], image.inputs['Vector'])
        if role == 'normal':
            normal = nodes.new('ShaderNodeNormalMap')
            normal.inputs['Strength'].default_value = 1
            links.new(image.outputs['Color'], normal.inputs['Color'])
            links.new(normal.outputs['Normal'], principled.inputs['Normal'])
        else:
            links.new(image.outputs['Color'], principled.inputs[socket])
    # AO is presented independently in the HTML review; do not bake it into albedo.
    return material


def label(value, x, y, material, size=.14):
    curve = bpy.data.curves.new('Label', 'FONT')
    curve.body = value
    curve.size = size
    curve.align_x = 'CENTER'
    obj = bpy.data.objects.new('Label:' + value, curve)
    bpy.context.collection.objects.link(obj)
    obj.location = (x, y, .025)
    obj.data.materials.append(material)
    return obj


def main():
    OUTPUT.mkdir(exist_ok=True)
    definitions = []
    for group in ['pbr-library', 'terrain-library']:
        manifest_file = BASE / group / 'manifest.json'
        if not manifest_file.exists():
            continue
        manifest = json.loads(manifest_file.read_text(encoding='utf8'))
        definitions += [(definition, manifest_file.parent) for definition in manifest['materials']
                        if definition.get('selected', True)]
    if not definitions:
        raise ValueError('No source-complete material manifests')
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    floor = plain('Neutral studio', (.025, .027, .027))
    ink = plain('Ivory labels', (.65, .61, .52))
    bpy.ops.mesh.primitive_plane_add(size=200)
    bpy.context.object.data.materials.append(floor)
    render_records = []
    rows = math.ceil(len(definitions) / 3)
    for index, (definition, folder) in enumerate(definitions):
        x, y = (index % 3 - 1) * 3, (rows - 1 - index // 3) * 3.4
        material = pbr(definition, folder)
        bpy.ops.mesh.primitive_plane_add(size=2, location=(x, y, .035))
        plane = bpy.context.object
        plane.name = definition['id'] + ':two-metre-plane'
        plane.data.materials.append(material)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=.36,
                                           location=(x + .52, y + .40, .40))
        sphere = bpy.context.object
        sphere.data.materials.append(material)
        for polygon in sphere.data.polygons:
            polygon.use_smooth = True
        label(definition['id'], x, y - 1.32, ink)
        if not definition.get('tileMetres'):
            proposed = definition.get('previewTileMetres') or [2, 2]
            label('Tile ' + str(proposed[0]) + 'm (design only)', x, y - 1.55, ink, .10)
        # A real 50cm bar is separate geometry; no ruler painted onto a texture.
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y - 1.12, .03))
        bar = bpy.context.object
        bar.dimensions = (.5, .013, .01)
        bar.data.materials.append(ink)
        render_records.append({'id': definition['id'], 'sourceAsset': definition.get('sourceAsset'),
                               'planeMetres': [2, 2], 'rulerMetres': .5,
                               'tileMetres': definition.get('tileMetres'),
                               'previewTileMetres': definition.get('previewTileMetres'),
                               'scaleSource': 'official' if definition.get('tileMetres') else 'design-proposal',
                               'normalStrength': 1})
    for name, location, energy, size in [('Neutral key', (-3, -4, 10), 1800, 7),
                                         ('Neutral fill', (4, 6, 7), 900, 5)]:
        light = bpy.data.lights.new(name, 'AREA')
        light.energy = energy
        light.shape = 'DISK'
        light.size = size
        obj = bpy.data.objects.new(name, light)
        bpy.context.collection.objects.link(obj)
        obj.location = location
        look_at(obj, (0, 1, 0))
    scene.world = bpy.data.worlds.new('Neutral world')
    scene.world.use_nodes = True
    scene.world.node_tree.nodes.get('Background').inputs['Color'].default_value = (.2, .2, .2, 1)
    scene.world.node_tree.nodes.get('Background').inputs['Strength'].default_value = .4
    bpy.ops.object.camera_add(location=(0, -10, 15))
    scene.camera = bpy.context.object
    look_at(scene.camera, (0, (rows - 1) * 1.7, 0))
    scene.camera.data.type = 'ORTHO'
    scene.camera.data.ortho_scale = max(10.5, rows * 4.2)
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 24
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 1500
    scene.render.resolution_y = 1100
    scene.render.resolution_percentage = 100
    scene.view_settings.view_transform = 'AgX'
    scene.render.image_settings.file_format = 'PNG'
    scene.render.filepath = str(OUTPUT / 'matched-pbr-neutral.png')
    (OUTPUT / 'render-record.json').write_text(json.dumps({
        'purpose': 'offline source-material review; not a Cocos gameplay screenshot',
        'renderer': 'Blender Cycles, AgX, 24 samples, neutral area lights',
        'ao': 'available in HTML review, not multiplied into albedo',
        'materials': render_records}, indent=2), encoding='utf8')
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / 'source-art/materials/chapter-one-v3/material-review.blend'))
    bpy.ops.render.render(write_still=True)


if __name__ == '__main__':
    main()
