import bpy
import math
import os

def reset_scene():
    """シーン内の既存オブジェクトを消去して初期化"""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if "Camera" in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects["Camera"], do_unlink=True)
    if "Light" in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects["Light"], do_unlink=True)

def create_anime_pbr_material(name, color_hex, metallic=0.0, roughness=0.5, emissive_hex=None, emissive_strength=1.0):
    """AAAスタイルのPBR/Toonハイブリッドマテリアルノードを自動構築"""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    # Principled BSDF ノード構築
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)

    # カラー変換 (HEX to RGBA)
    def hex_to_rgb(hex_str):
        hex_str = hex_str.lstrip('#')
        return [int(hex_str[i:i+2], 16) / 255.0 for i in (0, 2, 4)] + [1.0]

    bsdf.inputs['Base Color'].default_value = hex_to_rgb(color_hex)
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Roughness'].default_value = roughness

    if emissive_hex:
        bsdf.inputs['Emissive Color'].default_value = hex_to_rgb(emissive_hex)
        if 'Emissive Strength' in bsdf.inputs:
            bsdf.inputs['Emissive Strength'].default_value = emissive_strength

    # Output ノード
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (300, 0)
    links.new(bsdf.outputs['Surface'], output.inputs['Surface'])

    return mat

def build_wuthering_character():
    """キャラクターの各パーツを幾何学的にモデリング・構築"""
    reset_scene()

    # マテリアル構築
    m_skin = create_anime_pbr_material("M_Skin", "#FACDBE", 0.0, 0.65)
    m_eyes = create_anime_pbr_material("M_Eyes", "#1ACDEB", 0.1, 0.15, "#0D99B0", 2.0)
    m_hair = create_anime_pbr_material("M_Hair", "#CCEAFA", 0.05, 0.35)
    m_coat = create_anime_pbr_material("M_Tactical_Outfit", "#1F242E", 0.1, 0.50)
    m_armor = create_anime_pbr_material("M_Gold_Armor", "#F2C759", 0.92, 0.22)
    m_boots = create_anime_pbr_material("M_Boots_Leather", "#0D0E12", 0.18, 0.40)
    m_glow = create_anime_pbr_material("M_Tacet_Resonance", "#00F0FF", 0.0, 0.10, "#00F0FF", 4.5)

    # ルートオブジェクト
    root_obj = bpy.data.objects.new("Wuthering_Character_Root", None)
    bpy.context.collection.objects.link(root_obj)

    # 1. 頭部・顔 (Face_Head)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=32, radius=0.22, location=(0, 0, 1.55))
    head = bpy.context.active_object
    head.name = "Face_Head"
    head.scale = (0.95, 1.0, 1.15)
    head.data.materials.append(m_skin)
    head.parent = root_obj

    # 2. 瞳・眼球 (Eyes)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=20, radius=0.045, location=(-0.075, -0.17, 1.58))
    eye_l = bpy.context.active_object
    eye_l.scale = (1.0, 0.4, 1.0)
    eye_l.data.materials.append(m_eyes)

    bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=20, radius=0.045, location=(0.075, -0.17, 1.58))
    eye_r = bpy.context.active_object
    eye_r.scale = (1.0, 0.4, 1.0)
    eye_r.data.materials.append(m_eyes)

    # Eyesを統合
    bpy.ops.object.select_all(action='DESELECT')
    eye_l.select_set(True)
    eye_r.select_set(True)
    bpy.context.view_layer.objects.active = eye_l
    bpy.ops.object.join()
    eyes_obj = bpy.context.active_object
    eyes_obj.name = "Eyes"
    eyes_obj.parent = root_obj

    # 3. 前髪・サイド・ロングヘア (Hair)
    hair_parts = []
    # 前髪バンズ (Front Bangs)
    for i in range(7):
        offset_x = (i - 3) * 0.045
        bpy.ops.curve.primitive_bezier_curve_add(location=(offset_x, -0.10, 1.70))
        curve = bpy.context.active_object
        curve.data.bevel_depth = 0.025
        curve.data.bevel_resolution = 4
        hair_parts.append(curve)

    # 4. 戦術コート (Tactical Coat)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.22, depth=0.65, location=(0, 0, 1.0))
    coat = bpy.context.active_object
    coat.name = "Tactical_Coat"
    coat.data.materials.append(m_coat)
    coat.parent = root_obj

    # 5. 金具・アーマー (Armor Accents)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.20, minor_radius=0.03, location=(0, 0, 0.95))
    belt = bpy.context.active_object
    belt.name = "Armor_Accents"
    belt.data.materials.append(m_armor)
    belt.parent = root_obj

    # 6. 共鳴発光結晶 (Emissive Crystals)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=0.04, location=(0, -0.16, 1.25))
    crystal = bpy.context.active_object
    crystal.name = "Emissive_Crystals"
    crystal.data.materials.append(m_glow)
    crystal.parent = root_obj

    # 全メッシュのスムーズシェーディング
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            for poly in obj.data.polygons:
                poly.use_smooth = True

    print("キャラクター構築完了。")

def export_glb(output_path="wuthering_waves_character.glb"):
    """GLB (glTF 2.0 Binary) 形式でエクスポート"""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.gltf(
        filepath=output_path,
        export_format='GLB',
        use_selection=True,
        export_texcoords=True,
        export_normals=True,
        export_materials='EXPORT',
        export_colors=True
    )
    print(f"GLBファイル出力成功: {output_path}")

if __name__ == "__main__":
    build_wuthering_character()
    # Blenderコマンドライン実行時の出力パス設定
    out_file = os.path.join(os.path.dirname(bpy.data.filepath) if bpy.data.filepath else ".", "wuthering_waves_character.glb")
    export_glb(out_file)
