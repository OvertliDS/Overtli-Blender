from __future__ import annotations

from ..core import *
from ..services.context import *
from ..services.scene import *
from ..services.verification import *
from ..services.assets import *
from ..services.materials import *
from ..services.modeling import *
from ..services.spatial import *
from ..services.sculpt import *
from ..services.animation import *
from ..services.workspace import *
from ..services.diagnostics import *
from ..services.geometry_nodes import *
from ..services.addon_management import *
from ..services.knowledge import *
from ..services.baking import *
from ..services.product_ux import *

class BlenderMCPServer:
    def __init__(self, host='localhost', port=9876):
        self.host = host
        self.port = port
        self.running = False
        self.socket = None
        self.server_thread = None
        # Shared context storage for persistent variables between tool calls
        self.shared_context = {
            'variables': {},  # User-defined variables
            'objects': {},    # Object references by handle
            'materials': {},  # Material references by handle
            'operations': {}, # Operation results by ID
            'history': []     # Operation history
        }
        self.shared_context_service = SharedContextService(self.shared_context)
        self.script_registry_service = ScriptRegistryService()
        self.scene_observation_service = SceneObservationService(self)
        self.viewport_screenshot_service = ViewportScreenshotService(self)
        self.scene_intelligence_service = SceneIntelligenceService(self)
        self.verification_artifact_service = VerificationArtifactService(self)
        self.scene_edit_service = SceneEditService(self)
        self.material_authoring_service = MaterialAuthoringService(self)
        self.material_intelligence_service = MaterialIntelligenceService(self)
        self.material_template_service = MaterialTemplateService(self)
        self.advanced_material_authoring_service = AdvancedMaterialAuthoringService(self)
        self.shader_graph_service = ShaderGraphService(self)
        self.material_texture_slot_service = MaterialTextureSlotService(self)
        self.procedural_texture_service = ProceduralTextureService(self)
        self.material_preview_service = MaterialPreviewService(self)
        self.material_workflow_batch_service = MaterialWorkflowBatchService(self)
        self.selection_intelligence_service = SelectionIntelligenceService(self)
        self.vertex_group_service = VertexGroupService(self)
        self.shape_key_service = ShapeKeyService(self)
        self.lattice_deformation_service = LatticeDeformationService(self)
        self.deformation_modifier_service = DeformationModifierService(self)
        self.direct_mesh_edit_service = DirectMeshEditService(self)
        self.deformation_workflow_batch_service = DeformationWorkflowBatchService(self)
        self.method_intelligence_service = MethodIntelligenceService(self)
        self.asset_material_workflow_service = AssetMaterialWorkflowService(self)
        self.uv_selection_measurement_service = UVSelectionMeasurementService(self)
        self.sculpt_workflow_service = SculptWorkflowService(self)
        self.animation_intelligence_service = AnimationIntelligenceService(self)
        self.animation_authoring_service = AnimationAuthoringService(self)
        self.camera_composition_service = CameraCompositionService(self)
        self.lighting_setup_service = LightingSetupService(self)
        self.render_settings_service = RenderSettingsService(self)
        self.render_artifact_service = RenderArtifactService(self)
        self.compositor_pass_service = CompositorPassService(self)
        self.presentation_workflow_batch_service = PresentationWorkflowBatchService(self)
        self.asset_library_intelligence_service = AssetLibraryIntelligenceService(self)
        self.asset_dependency_service = AssetDependencyService(self)
        self.asset_import_service = AssetImportService(self)
        self.asset_export_service = AssetExportService(self)
        self.blend_library_service = BlendLibraryService(self)
        self.scene_kit_service = SceneKitService(self)
        self.asset_preview_service = AssetPreviewService(self)
        self.asset_workflow_batch_service = AssetWorkflowBatchService(self)
        self.rigging_simulation_service = RiggingSimulationService(self)
        self.modifier_service = ModifierService(self)
        self.collection_organization_service = CollectionOrganizationService(self)
        self.verified_edit_batch_service = VerifiedEditBatchService(self)
        self.workspace_safety_diff_service = WorkspaceSafetyDiffService(self)
        self.provider_status_service = ProviderStatusService(self)
        self.polyhaven_service = PolyHavenService(self)
        self.sketchfab_service = SketchfabService(self)
        self.hyper3d_service = Hyper3DService(self)
        self.safety_policy_service = SafetyPolicyService(self)
        self.raw_code_execution_service = RawCodeExecutionService(self)
        self.geometry_nodes_intelligence_service = GeometryNodesIntelligenceService(self)
        self.geometry_nodes_template_service = GeometryNodesTemplateService(self)
        self.geometry_nodes_recipe_service = GeometryNodesRecipeService(self)
        self.geometry_nodes_modifier_service = GeometryNodesModifierService(self)
        self.procedural_asset_generator_service = ProceduralAssetGeneratorService(self)
        self.geometry_nodes_validation_service = GeometryNodesValidationService(self)
        self.geometry_nodes_preview_service = GeometryNodesPreviewService(self)
        self.geometry_nodes_workflow_batch_service = GeometryNodesWorkflowBatchService(self)
        self.geometry_nodes_service = GeometryNodesService(self)
        self.addon_management_service = AddonManagementService(self)
        self.addon_development_service = AddonDevelopmentService(self)
        self.blender_api_knowledge_service = BlenderApiKnowledgeService(self)
        self.verified_snippet_library_service = VerifiedSnippetLibraryService(self)
        self.skill_pack_service = SkillPackService(self)
        self.review_package_export_service = ReviewPackageExportService(self)
        self.advanced_knowledge_workflow_batch_service = AdvancedKnowledgeWorkflowBatchService(self)
        self.project_workspace_service = ProjectWorkspaceService(self)
        self.file_access_policy_service = FileAccessPolicyService(self)
        self.cache_retention_service = CacheRetentionService(self)
        self.task_graph_service = TaskGraphService(self)
        self.time_revision_service = TimeRevisionService(self)
        self.reference_image_service = ReferenceImageService(self)
        self.spatial_measurement_service = SpatialMeasurementService(self)
        self.safe_rename_relocation_service = SafeRenameRelocationService(self)
        self._phase8a_temp_nodes = []
        self._phase8a_temp_images = []
        self.bake_capabilities_service = BakeCapabilitiesService(self)
        self.bake_preflight_service = BakePreflightService(self)
        self.bake_image_target_service = BakeImageTargetService(self)
        self.texture_bake_service = TextureBakeService(self)
        self.derived_bake_service = DerivedBakeService(self)
        self.channel_pack_service = ChannelPackService(self)
        self.baked_texture_validation_service = BakedTextureValidationService(self)
        self.bake_workflow_batch_service = BakeWorkflowBatchService(self)
        self.mesh_schema_construction_service = MeshSchemaConstructionService(self)
        self.profile_modeling_service = ProfileModelingService(self)
        self.modifier_construction_service = ModifierConstructionService(self)
        self.reference_driven_construction_service = ReferenceDrivenConstructionService(self)
        self.sculpt_phase8b_workflow_service = SculptWorkflowPhase8BService(self)
        self.cloth_pattern_workflow_service = ClothPatternWorkflowService(self)
        self.construction_validation_service = ConstructionValidationService(self)
        self.advanced_modeling_workflow_batch_service = AdvancedModelingWorkflowBatchService(self)
        self.animation_intelligence_advanced_service = AnimationIntelligenceAdvancedService(self)
        self.action_library_service = ActionLibraryService(self)
        self.fcurve_editing_service = FCurveEditingService(self)
        self.nla_workflow_service = NLAWorkflowService(self)
        self.driver_dsl_service = DriverDSLService(self)
        self.rig_template_service = RigTemplateService(self)
        self.rig_validation_service = RigValidationService(self)
        self.pose_library_workflow_service = PoseLibraryWorkflowService(self)
        self.shot_workflow_service = ShotWorkflowService(self)
        self.simulation_workflow_service = SimulationWorkflowService(self)
        self.motion_validation_service = MotionValidationService(self)
        self.animation_rigging_workflow_batch_service = AnimationRiggingWorkflowBatchService(self)
        self.preferences_configuration_service = PreferencesConfigurationService(self)
        self.tool_profile_service = ToolProfileService(self)
        self.bundled_skill_pack_service = BundledSkillPackService(self)
        self.addon_interop_inspection_service = AddonInteropInspectionService(self)
        self.user_facing_error_service = UserFacingErrorService(self)
        self.onboarding_workflow_service = OnboardingWorkflowService(self)
        self.runtime_ux_status_service = RuntimeUXStatusService(self)
        self.product_polish_workflow_batch_service = ProductPolishWorkflowBatchService(self)

        for _name, _service in {
            "get_modeling_capabilities": self.mesh_schema_construction_service,
            "validate_mesh_schema": self.mesh_schema_construction_service,
            "create_mesh_from_schema": self.mesh_schema_construction_service,
            "create_profile_curve": self.profile_modeling_service,
            "extrude_profile": self.profile_modeling_service,
            "lathe_profile": self.profile_modeling_service,
            "loft_profiles": self.profile_modeling_service,
            "bridge_profile_loops": self.profile_modeling_service,
            "create_curve_path_object": self.profile_modeling_service,
            "create_beveled_curve_object": self.profile_modeling_service,
            "create_modifier_stack": self.modifier_construction_service,
            "create_hard_surface_panel": self.modifier_construction_service,
            "create_pipe_or_rail": self.modifier_construction_service,
            "create_modular_assembly": self.modifier_construction_service,
            "plan_reference_construction": self.reference_driven_construction_service,
            "run_reference_construction_step": self.reference_driven_construction_service,
            "validate_reference_alignment": self.reference_driven_construction_service,
            "configure_sculpt_session": self.sculpt_phase8b_workflow_service,
            "create_sculpt_mask": self.sculpt_phase8b_workflow_service,
            "create_face_set": self.sculpt_phase8b_workflow_service,
            "apply_sculpt_stroke_batch": self.sculpt_phase8b_workflow_service,
            "create_shape_key_sculpt_variant": self.sculpt_phase8b_workflow_service,
            "validate_sculpt_result": self.sculpt_phase8b_workflow_service,
            "create_cloth_pattern_panel": self.cloth_pattern_workflow_service,
            "define_cloth_seam_pair": self.cloth_pattern_workflow_service,
            "create_cloth_setup": self.cloth_pattern_workflow_service,
            "create_cloth_pin_group": self.cloth_pattern_workflow_service,
            "create_cloth_collision_setup": self.cloth_pattern_workflow_service,
            "simulate_cloth_preview": self.cloth_pattern_workflow_service,
            "bake_cloth_cache": self.cloth_pattern_workflow_service,
            "clear_cloth_cache": self.cloth_pattern_workflow_service,
            "convert_cloth_result": self.cloth_pattern_workflow_service,
            "validate_construction_geometry": self.construction_validation_service,
            "plan_construction_cleanup": self.construction_validation_service,
            "execute_construction_cleanup": self.construction_validation_service,
            "run_advanced_modeling_workflow_batch": self.advanced_modeling_workflow_batch_service,
            "get_animation_system_capabilities": self.animation_intelligence_advanced_service,
            "inspect_animation_system": self.animation_intelligence_advanced_service,
            "list_actions": self.action_library_service,
            "get_action_deep_info": self.action_library_service,
            "create_action": self.action_library_service,
            "duplicate_action": self.action_library_service,
            "rename_action": self.action_library_service,
            "assign_action": self.action_library_service,
            "delete_actions": self.action_library_service,
            "insert_keyframe_batch": self.fcurve_editing_service,
            "edit_keyframes": self.fcurve_editing_service,
            "retime_action": self.fcurve_editing_service,
            "set_fcurve_interpolation": self.fcurve_editing_service,
            "add_fcurve_modifier": self.fcurve_editing_service,
            "remove_fcurve_modifier": self.fcurve_editing_service,
            "validate_fcurves": self.fcurve_editing_service,
            "create_nla_track": self.nla_workflow_service,
            "add_action_to_nla": self.nla_workflow_service,
            "edit_nla_strip": self.nla_workflow_service,
            "mute_nla_track": self.nla_workflow_service,
            "delete_nla_tracks": self.nla_workflow_service,
            "validate_nla_stack": self.nla_workflow_service,
            "create_driver_from_dsl": self.driver_dsl_service,
            "validate_driver_dsl": self.driver_dsl_service,
            "list_drivers": self.driver_dsl_service,
            "get_driver_info": self.driver_dsl_service,
            "remove_drivers": self.driver_dsl_service,
            "create_rig_template": self.rig_template_service,
            "create_control_bones": self.rig_template_service,
            "create_ik_chain": self.rig_template_service,
            "add_rig_constraint": self.rig_validation_service,
            "remove_rig_constraints": self.rig_validation_service,
            "add_custom_rig_properties": self.rig_template_service,
            "validate_rig": self.rig_validation_service,
            "inspect_pose": self.pose_library_workflow_service,
            "create_pose_snapshot": self.pose_library_workflow_service,
            "apply_pose_snapshot": self.pose_library_workflow_service,
            "create_pose_asset": self.pose_library_workflow_service,
            "list_pose_assets": self.pose_library_workflow_service,
            "compare_poses": self.pose_library_workflow_service,
            "delete_pose_assets": self.pose_library_workflow_service,
            "create_shot_range": self.shot_workflow_service,
            "create_camera_cut": self.shot_workflow_service,
            "create_timeline_marker": self.shot_workflow_service,
            "create_shot_plan": self.shot_workflow_service,
            "validate_shot_plan": self.shot_workflow_service,
            "create_motion_path_preview": self.motion_validation_service,
            "validate_motion": self.motion_validation_service,
            "get_simulation_capabilities": self.simulation_workflow_service,
            "inspect_simulation_state": self.simulation_workflow_service,
            "configure_rigidbody_basic": self.simulation_workflow_service,
            "configure_cloth_simulation_advanced": self.simulation_workflow_service,
            "configure_softbody_basic": self.simulation_workflow_service,
            "configure_hair_curve_dynamics_basic": self.simulation_workflow_service,
            "get_simulation_cache_status": self.simulation_workflow_service,
            "simulate_preview_range": self.simulation_workflow_service,
            "bake_simulation_cache": self.simulation_workflow_service,
            "clear_simulation_cache": self.simulation_workflow_service,
            "run_animation_rigging_workflow_batch": self.animation_rigging_workflow_batch_service,
            "get_preferences_schema": self.preferences_configuration_service,
            "get_runtime_preferences": self.preferences_configuration_service,
            "update_runtime_preferences": self.preferences_configuration_service,
            "validate_runtime_preferences": self.preferences_configuration_service,
            "reset_runtime_preferences": self.preferences_configuration_service,
            "get_tool_profiles": self.tool_profile_service,
            "get_active_tool_profile": self.tool_profile_service,
            "set_active_tool_profile": self.tool_profile_service,
            "preview_tool_profile": self.tool_profile_service,
            "get_visible_tool_budget": self.tool_profile_service,
            "get_enabled_tool_packs": self.tool_profile_service,
            "set_enabled_tool_packs": self.tool_profile_service,
            "recommend_tool_profile": self.tool_profile_service,
            "list_bundled_skill_packs": self.bundled_skill_pack_service,
            "get_bundled_skill_pack": self.bundled_skill_pack_service,
            "search_bundled_skill_packs": self.bundled_skill_pack_service,
            "activate_skill_pack": self.bundled_skill_pack_service,
            "deactivate_skill_pack": self.bundled_skill_pack_service,
            "recommend_skill_packs": self.bundled_skill_pack_service,
            "validate_skill_pack_readiness": self.bundled_skill_pack_service,
            "list_addon_source_roots": self.addon_interop_inspection_service,
            "scan_addon_sources_readonly": self.addon_interop_inspection_service,
            "get_addon_source_summary": self.addon_interop_inspection_service,
            "search_addon_operators": self.addon_interop_inspection_service,
            "search_addon_panels": self.addon_interop_inspection_service,
            "search_addon_properties": self.addon_interop_inspection_service,
            "plan_addon_operator_invocation": self.addon_interop_inspection_service,
            "execute_approved_addon_operator": self.addon_interop_inspection_service,
            "get_error_catalog": self.user_facing_error_service,
            "explain_error": self.user_facing_error_service,
            "get_remediation_steps": self.user_facing_error_service,
            "get_runtime_dashboard": self.runtime_ux_status_service,
            "get_approval_queue_summary": self.runtime_ux_status_service,
            "get_recent_operation_summary": self.runtime_ux_status_service,
            "get_setup_status": self.onboarding_workflow_service,
            "run_onboarding_checklist": self.onboarding_workflow_service,
            "run_product_polish_workflow_batch": self.product_polish_workflow_batch_service,
            "get_bake_capabilities": self.bake_capabilities_service,
            "validate_bake_setup": self.bake_preflight_service,
            "estimate_bake_cost": self.bake_preflight_service,
            "create_bake_target_images": self.bake_image_target_service,
            "assign_bake_targets": self.bake_image_target_service,
            "list_bake_targets": self.bake_image_target_service,
            "list_project_images": self.bake_image_target_service,
            "get_image_resource_info": self.bake_image_target_service,
            "rename_image_resource": self.bake_image_target_service,
            "bake_material_maps": self.texture_bake_service,
            "bake_selected_to_active": self.texture_bake_service,
            "bake_procedural_material": self.derived_bake_service,
            "bake_derived_map": self.derived_bake_service,
            "bake_curvature_map": self.derived_bake_service,
            "bake_thickness_map": self.derived_bake_service,
            "pack_texture_channels": self.channel_pack_service,
            "unpack_texture_channels": self.channel_pack_service,
            "validate_packed_texture": self.channel_pack_service,
            "save_baked_textures": self.baked_texture_validation_service,
            "validate_baked_textures": self.baked_texture_validation_service,
            "relink_baked_textures": self.baked_texture_validation_service,
            "create_baked_material": self.baked_texture_validation_service,
            "plan_bake_cleanup": self.bake_workflow_batch_service,
            "execute_bake_cleanup": self.bake_workflow_batch_service,
            "run_verified_bake_workflow": self.bake_workflow_batch_service,
            "get_loaded_project_folder": self.project_workspace_service,
            "resolve_project_workspace": self.project_workspace_service,
            "initialize_temp_workspace": self.project_workspace_service,
            "promote_temp_workspace_to_project": self.project_workspace_service,
            "initialize_project_workspace": self.project_workspace_service,
            "validate_project_layout": self.project_workspace_service,
            "repair_project_layout": self.project_workspace_service,
            "register_blend_file": self.project_workspace_service,
            "save_project_as": self.project_workspace_service,
            "resave_project_folder": self.project_workspace_service,
            "plan_project_folder_move": self.project_workspace_service,
            "move_project_folder": self.project_workspace_service,
            "create_project_backup": self.project_workspace_service,
            "restore_project_backup": self.project_workspace_service,
            "collect_project_dependencies": self.project_workspace_service,
            "get_file_access_policy": self.file_access_policy_service,
            "set_file_access_policy": self.file_access_policy_service,
            "validate_path_access": self.file_access_policy_service,
            "list_approved_roots": self.file_access_policy_service,
            "add_approved_root": self.file_access_policy_service,
            "remove_approved_root": self.file_access_policy_service,
            "detect_drive_roots": self.file_access_policy_service,
            "approve_drive_roots": self.file_access_policy_service,
            "scan_project_files": self.file_access_policy_service,
            "read_project_text_file": self.file_access_policy_service,
            "write_project_text_file": self.file_access_policy_service,
            "copy_file_into_project": self.file_access_policy_service,
            "plan_file_delete": self.file_access_policy_service,
            "execute_approved_file_delete": self.file_access_policy_service,
            "get_cache_status": self.cache_retention_service,
            "plan_cache_cleanup": self.cache_retention_service,
            "execute_cache_cleanup": self.cache_retention_service,
            "pin_artifact": self.cache_retention_service,
            "unpin_artifact": self.cache_retention_service,
            "find_orphaned_artifacts": self.cache_retention_service,
            "compact_operation_history": self.cache_retention_service,
            "create_task": self.task_graph_service,
            "update_task": self.task_graph_service,
            "list_tasks": self.task_graph_service,
            "get_task": self.task_graph_service,
            "set_task_status": self.task_graph_service,
            "link_task_artifact": self.task_graph_service,
            "link_task_target": self.task_graph_service,
            "mark_task_verified": self.task_graph_service,
            "mark_task_stale": self.task_graph_service,
            "archive_tasks": self.task_graph_service,
            "get_task_graph": self.task_graph_service,
            "detect_stale_tasks": self.task_graph_service,
            "get_session_time": self.time_revision_service,
            "get_scene_revision": self.time_revision_service,
            "get_recent_operations": self.time_revision_service,
            "get_changes_since_revision": self.time_revision_service,
            "get_operation_duration": self.time_revision_service,
            "create_scene_revision_marker": self.time_revision_service,
            "import_reference_image": self.reference_image_service,
            "create_reference_set": self.reference_image_service,
            "place_reference_view": self.reference_image_service,
            "calibrate_reference_scale": self.reference_image_service,
            "set_reference_opacity": self.reference_image_service,
            "set_reference_depth": self.reference_image_service,
            "lock_reference": self.reference_image_service,
            "set_reference_view_visibility": self.reference_image_service,
            "add_reference_landmark": self.reference_image_service,
            "measure_reference_landmarks": self.reference_image_service,
            "capture_reference_overlay": self.reference_image_service,
            "list_reference_images": self.reference_image_service,
            "relink_reference_image": self.reference_image_service,
            "remove_reference_image": self.reference_image_service,
            "calculate_distance": self.spatial_measurement_service,
            "calculate_angle": self.spatial_measurement_service,
            "calculate_area": self.spatial_measurement_service,
            "calculate_volume": self.spatial_measurement_service,
            "calculate_curve_length": self.spatial_measurement_service,
            "calculate_clearance": self.spatial_measurement_service,
            "calculate_alignment": self.spatial_measurement_service,
            "convert_units": self.spatial_measurement_service,
            "calculate_scale_ratio": self.spatial_measurement_service,
            "compare_measurements": self.spatial_measurement_service,
            "get_oriented_bounds": self.spatial_measurement_service,
            "raycast_scene": self.spatial_measurement_service,
            "find_nearest_objects": self.spatial_measurement_service,
            "detect_object_intersections": self.spatial_measurement_service,
            "measure_object_to_reference": self.spatial_measurement_service,
            "plan_rename": self.safe_rename_relocation_service,
            "execute_rename": self.safe_rename_relocation_service,
            "batch_rename_datablocks": self.safe_rename_relocation_service,
            "batch_rename_files": self.safe_rename_relocation_service,
            "rename_project": self.safe_rename_relocation_service,
            "repair_references_after_rename": self.safe_rename_relocation_service,
        }.items():
            setattr(self, _name, getattr(_service, _name))

        self.get_scene_info = self.scene_observation_service.get_scene_info
        self.get_object_info = self.scene_observation_service.get_object_info
        self.get_viewport_screenshot = self.viewport_screenshot_service.get_viewport_screenshot
        self.get_scene_index = self.scene_intelligence_service.get_scene_index
        self.get_object_deep_info = self.scene_intelligence_service.get_object_deep_info
        self.get_selection_info = self.scene_intelligence_service.get_selection_info
        self.get_scene_health = self.scene_intelligence_service.get_scene_health
        self.capture_viewport_pack = self.verification_artifact_service.capture_viewport_pack
        self.create_verification_snapshot = self.verification_artifact_service.create_verification_snapshot
        self.list_verification_snapshots = self.verification_artifact_service.list_verification_snapshots
        self.get_supported_edit_operations = self.scene_edit_service.get_supported_edit_operations
        self.create_primitive_object = self.scene_edit_service.create_primitive_object
        self.create_box = self.scene_edit_service.create_box
        self.transform_object = self.scene_edit_service.transform_object
        self.transform_object_dimensions = self.scene_edit_service.transform_object_dimensions
        self.duplicate_object = self.scene_edit_service.duplicate_object
        self.delete_objects = self.scene_edit_service.delete_objects
        self.clear_scene = self.scene_edit_service.clear_scene
        self.scene_cleanup_plan = self.scene_edit_service.scene_cleanup_plan
        self.validate_ground_contact = self.scene_edit_service.validate_ground_contact
        self.align_object_to_surface = self.scene_edit_service.align_object_to_surface
        self.validate_scene_composition = self.scene_edit_service.validate_scene_composition
        self.set_object_visibility = self.scene_edit_service.set_object_visibility
        self.create_basic_material = self.material_authoring_service.create_basic_material
        self.assign_material = self.material_authoring_service.assign_material
        self.update_material_properties = self.material_authoring_service.update_material_properties
        self.get_material_channel_schema = self.material_intelligence_service.get_material_channel_schema
        self.get_supported_material_templates = self.material_template_service.get_supported_material_templates
        self.list_materials_deep = self.material_intelligence_service.list_materials_deep
        self.get_material_deep_info = self.material_intelligence_service.get_material_deep_info
        self.get_shader_graph = self.shader_graph_service.get_shader_graph
        self.create_material_from_template = self.material_template_service.create_material_from_template
        self.create_custom_material = self.advanced_material_authoring_service.create_custom_material
        self.create_procedural_material = self.procedural_texture_service.create_procedural_material
        self.create_material_variant = self.advanced_material_authoring_service.create_material_variant
        self.apply_material_to_objects = self.advanced_material_authoring_service.apply_material_to_objects
        self.bind_material_texture_map = self.material_texture_slot_service.bind_material_texture_map
        self.set_material_node_input = self.shader_graph_service.set_material_node_input
        self.add_material_node = self.shader_graph_service.add_material_node
        self.connect_material_nodes = self.shader_graph_service.connect_material_nodes
        self.remove_material_node = self.shader_graph_service.remove_material_node
        self.create_material_preview = self.material_preview_service.create_material_preview
        self.run_material_workflow_batch = self.material_workflow_batch_service.run_material_workflow_batch
        self.delete_materials = self.advanced_material_authoring_service.delete_materials
        self.get_selection_deep_info = self.selection_intelligence_service.get_selection_deep_info
        self.get_mesh_component_summary = self.selection_intelligence_service.get_mesh_component_summary
        self.create_vertex_group = self.vertex_group_service.create_vertex_group
        self.update_vertex_group_weights = self.vertex_group_service.update_vertex_group_weights
        self.list_vertex_groups = self.vertex_group_service.list_vertex_groups
        self.delete_vertex_groups = self.vertex_group_service.delete_vertex_groups
        self.create_shape_key = self.shape_key_service.create_shape_key
        self.update_shape_key_value = self.shape_key_service.update_shape_key_value
        self.edit_shape_key_offsets = self.shape_key_service.edit_shape_key_offsets
        self.list_shape_keys = self.shape_key_service.list_shape_keys
        self.delete_shape_keys = self.shape_key_service.delete_shape_keys
        self.create_lattice_deformer = self.lattice_deformation_service.create_lattice_deformer
        self.update_lattice_deformer = self.lattice_deformation_service.update_lattice_deformer
        self.apply_lattice_to_object = self.lattice_deformation_service.apply_lattice_to_object
        self.remove_lattice_deformer = self.lattice_deformation_service.remove_lattice_deformer
        self.add_deformation_modifier = self.deformation_modifier_service.add_deformation_modifier
        self.update_deformation_modifier = self.deformation_modifier_service.update_deformation_modifier
        self.create_region_deformation = self.deformation_workflow_batch_service.create_region_deformation
        self.run_deformation_workflow_batch = self.deformation_workflow_batch_service.run_deformation_workflow_batch
        self.get_method_plan = self.method_intelligence_service.get_method_plan
        self.list_operation_playbooks = self.method_intelligence_service.list_operation_playbooks
        self.get_tricks_knowledge_base = self.method_intelligence_service.get_tricks_knowledge_base
        self.get_anti_pattern_rules = self.method_intelligence_service.get_anti_pattern_rules
        self.get_modifier_recipes = self.method_intelligence_service.get_modifier_recipes
        self.score_selection_confidence = self.method_intelligence_service.score_selection_confidence
        self.scan_blender_asset_libraries = self.asset_material_workflow_service.scan_blender_asset_libraries
        self.preview_asset = self.asset_material_workflow_service.preview_asset
        self.import_texture_folder = self.asset_material_workflow_service.import_texture_folder
        self.create_style_material = self.asset_material_workflow_service.create_style_material
        self.create_paintable_texture = self.asset_material_workflow_service.create_paintable_texture
        self.delete_images = self.asset_material_workflow_service.delete_images
        self.list_uv_maps = self.uv_selection_measurement_service.list_uv_maps
        self.create_vertex_group_from_uv_island = self.uv_selection_measurement_service.create_vertex_group_from_uv_island
        self.measure_object = self.uv_selection_measurement_service.measure_object
        self.measure_distance = self.uv_selection_measurement_service.measure_distance
        self.create_proportional_deformation = self.uv_selection_measurement_service.create_proportional_deformation
        self.get_sculpt_status = self.sculpt_workflow_service.get_sculpt_status
        self.configure_sculpt_brush = self.sculpt_workflow_service.configure_sculpt_brush
        self.create_sculpt_mask_from_vertex_group = self.sculpt_workflow_service.create_sculpt_mask_from_vertex_group
        self.run_shape_key_sculpt_workflow = self.sculpt_workflow_service.run_shape_key_sculpt_workflow
        self.get_modeling_capabilities = self.mesh_schema_construction_service.get_modeling_capabilities
        self.validate_mesh_schema = self.mesh_schema_construction_service.validate_mesh_schema
        self.create_mesh_from_schema = self.mesh_schema_construction_service.create_mesh_from_schema
        self.create_profile_curve = self.profile_modeling_service.create_profile_curve
        self.extrude_profile = self.profile_modeling_service.extrude_profile
        self.lathe_profile = self.profile_modeling_service.lathe_profile
        self.loft_profiles = self.profile_modeling_service.loft_profiles
        self.bridge_profile_loops = self.profile_modeling_service.bridge_profile_loops
        self.create_curve_path_object = self.profile_modeling_service.create_curve_path_object
        self.create_beveled_curve_object = self.profile_modeling_service.create_beveled_curve_object
        self.create_modifier_stack = self.modifier_construction_service.create_modifier_stack
        self.create_hard_surface_panel = self.modifier_construction_service.create_hard_surface_panel
        self.create_pipe_or_rail = self.modifier_construction_service.create_pipe_or_rail
        self.create_modular_assembly = self.modifier_construction_service.create_modular_assembly
        self.plan_reference_construction = self.reference_driven_construction_service.plan_reference_construction
        self.run_reference_construction_step = self.reference_driven_construction_service.run_reference_construction_step
        self.validate_reference_alignment = self.reference_driven_construction_service.validate_reference_alignment
        self.configure_sculpt_session = self.sculpt_phase8b_workflow_service.configure_sculpt_session
        self.create_sculpt_mask = self.sculpt_phase8b_workflow_service.create_sculpt_mask
        self.create_face_set = self.sculpt_phase8b_workflow_service.create_face_set
        self.apply_sculpt_stroke_batch = self.sculpt_phase8b_workflow_service.apply_sculpt_stroke_batch
        self.create_shape_key_sculpt_variant = self.sculpt_phase8b_workflow_service.create_shape_key_sculpt_variant
        self.validate_sculpt_result = self.sculpt_phase8b_workflow_service.validate_sculpt_result
        self.create_cloth_pattern_panel = self.cloth_pattern_workflow_service.create_cloth_pattern_panel
        self.define_cloth_seam_pair = self.cloth_pattern_workflow_service.define_cloth_seam_pair
        self.create_cloth_setup = self.cloth_pattern_workflow_service.create_cloth_setup
        self.create_cloth_pin_group = self.cloth_pattern_workflow_service.create_cloth_pin_group
        self.create_cloth_collision_setup = self.cloth_pattern_workflow_service.create_cloth_collision_setup
        self.simulate_cloth_preview = self.cloth_pattern_workflow_service.simulate_cloth_preview
        self.bake_cloth_cache = self.cloth_pattern_workflow_service.bake_cloth_cache
        self.clear_cloth_cache = self.cloth_pattern_workflow_service.clear_cloth_cache
        self.convert_cloth_result = self.cloth_pattern_workflow_service.convert_cloth_result
        self.validate_construction_geometry = self.construction_validation_service.validate_construction_geometry
        self.plan_construction_cleanup = self.construction_validation_service.plan_construction_cleanup
        self.execute_construction_cleanup = self.construction_validation_service.execute_construction_cleanup
        self.run_advanced_modeling_workflow_batch = self.advanced_modeling_workflow_batch_service.run_advanced_modeling_workflow_batch
        self.get_timeline_info = self.animation_intelligence_service.get_timeline_info
        self.list_animated_objects = self.animation_intelligence_service.list_animated_objects
        self.get_animation_deep_info = self.animation_intelligence_service.get_animation_deep_info
        self.set_timeline_range = self.animation_intelligence_service.set_timeline_range
        self.set_current_frame = self.animation_intelligence_service.set_current_frame
        self.insert_transform_keyframes = self.animation_authoring_service.insert_transform_keyframes
        self.animate_object_transform = self.animation_authoring_service.animate_object_transform
        self.animate_camera_transform = self.animation_authoring_service.animate_camera_transform
        self.animate_light_property = self.animation_authoring_service.animate_light_property
        self.animate_material_property = self.animation_authoring_service.animate_material_property
        self.animate_shape_key_value = self.animation_authoring_service.animate_shape_key_value
        self.delete_animation_data = self.animation_authoring_service.delete_animation_data
        self.create_camera = self.camera_composition_service.create_camera
        self.frame_camera_to_objects = self.camera_composition_service.frame_camera_to_objects
        self.set_active_camera = self.camera_composition_service.set_active_camera
        self.create_light = self.lighting_setup_service.create_light
        self.create_lighting_setup = self.lighting_setup_service.create_lighting_setup
        self.update_light = self.lighting_setup_service.update_light
        self.set_world_lighting = self.lighting_setup_service.set_world_lighting
        self.get_render_settings = self.render_settings_service.get_render_settings
        self.set_render_settings = self.render_settings_service.set_render_settings
        self.get_supported_color_management = self.render_settings_service.get_supported_color_management
        self.set_output_path = self.render_settings_service.set_output_path
        self.render_still = self.render_artifact_service.render_still
        self.render_contact_sheet = self.render_artifact_service.render_contact_sheet
        self.create_turntable_animation = self.render_artifact_service.create_turntable_animation
        self.render_preview_animation = self.render_artifact_service.render_preview_animation
        self.get_compositor_status = self.compositor_pass_service.get_compositor_status
        self.set_compositor_preset = self.compositor_pass_service.set_compositor_preset
        self.set_render_passes = self.compositor_pass_service.set_render_passes
        self.run_presentation_workflow_batch = self.presentation_workflow_batch_service.run_presentation_workflow_batch
        self.cleanup_presentation_artifacts = self.presentation_workflow_batch_service.cleanup_presentation_artifacts
        self.get_supported_asset_formats = self.asset_library_intelligence_service.get_supported_asset_formats
        self.scan_asset_folder = self.asset_library_intelligence_service.scan_asset_folder
        self.list_asset_libraries = self.asset_library_intelligence_service.list_asset_libraries
        self.list_scene_assets = self.asset_library_intelligence_service.list_scene_assets
        self.get_asset_file_info = self.asset_library_intelligence_service.get_asset_file_info
        self.get_asset_dependency_report = self.asset_dependency_service.get_asset_dependency_report
        self.create_asset_manifest = self.asset_dependency_service.create_asset_manifest
        self.collect_external_dependencies = self.asset_dependency_service.collect_external_dependencies
        self.validate_external_dependencies = self.asset_dependency_service.validate_external_dependencies
        self.pack_external_data = self.asset_dependency_service.pack_external_data
        self.make_paths_relative = self.asset_dependency_service.make_paths_relative
        self.append_blend_asset = self.blend_library_service.append_blend_asset
        self.import_model_file = self.asset_import_service.import_model_file
        self.export_selected_objects = self.asset_export_service.export_selected_objects
        self.export_scene = self.asset_export_service.export_scene
        self.create_asset_preview = self.asset_preview_service.create_asset_preview
        self.create_asset_contact_sheet = self.asset_preview_service.create_asset_contact_sheet
        self.create_scene_kit = self.scene_kit_service.create_scene_kit
        self.import_scene_kit = self.scene_kit_service.import_scene_kit
        self.validate_scene_kit = self.scene_kit_service.validate_scene_kit
        self.list_scene_kits = self.scene_kit_service.list_scene_kits
        self.cleanup_asset_artifacts = self.asset_workflow_batch_service.cleanup_asset_artifacts
        self.run_asset_workflow_batch = self.asset_workflow_batch_service.run_asset_workflow_batch
        self.inspect_rigging = self.rigging_simulation_service.inspect_rigging
        self.create_armature = self.rigging_simulation_service.create_armature
        self.parent_mesh_to_armature = self.rigging_simulation_service.parent_mesh_to_armature
        self.pose_bone_transform = self.rigging_simulation_service.pose_bone_transform
        self.add_driver = self.rigging_simulation_service.add_driver
        self.remove_driver = self.rigging_simulation_service.remove_driver
        self.add_physics_basic = self.rigging_simulation_service.add_physics_basic
        self.add_object_modifier = self.modifier_service.add_object_modifier
        self.update_object_modifier = self.modifier_service.update_object_modifier
        self.remove_object_modifier = self.modifier_service.remove_object_modifier
        self.create_collection = self.collection_organization_service.create_collection
        self.move_objects_to_collection = self.collection_organization_service.move_objects_to_collection
        self.delete_collection = self.collection_organization_service.delete_collection
        self.run_verified_edit_batch = self.verified_edit_batch_service.run_verified_edit_batch
        self.get_task_workspace = self.workspace_safety_diff_service.get_task_workspace
        self.create_workspace_task = self.workspace_safety_diff_service.create_workspace_task
        self.update_workspace_task = self.workspace_safety_diff_service.update_workspace_task
        self.complete_workspace_task = self.workspace_safety_diff_service.complete_workspace_task
        self.create_scene_plan = self.workspace_safety_diff_service.create_scene_plan
        self.list_scene_plan = self.workspace_safety_diff_service.list_scene_plan
        self.list_workspace_tasks = self.workspace_safety_diff_service.list_workspace_tasks
        self.add_workspace_todo = self.workspace_safety_diff_service.add_workspace_todo
        self.update_workspace_todo = self.workspace_safety_diff_service.update_workspace_todo
        self.list_workspace_todos = self.workspace_safety_diff_service.list_workspace_todos
        self.record_operation_journal_entry = self.workspace_safety_diff_service.record_operation_journal_entry
        self.get_operation_journal = self.workspace_safety_diff_service.get_operation_journal
        self.create_scene_snapshot = self.workspace_safety_diff_service.create_scene_snapshot
        self.list_scene_snapshots = self.workspace_safety_diff_service.list_scene_snapshots
        self.diff_scene_snapshots = self.workspace_safety_diff_service.diff_scene_snapshots
        self.detect_user_changes = self.workspace_safety_diff_service.detect_user_changes
        self.rollback_to_scene_snapshot = self.workspace_safety_diff_service.rollback_to_scene_snapshot
        self.undo_last_blender_operation = self.workspace_safety_diff_service.undo_last_blender_operation
        self.get_safety_status = self.safety_policy_service.get_safety_status
        self.execute_code = self.raw_code_execution_service.execute_code
        self.get_polyhaven_status = self.provider_status_service.get_polyhaven_status
        self.get_hyper3d_status = self.provider_status_service.get_hyper3d_status
        self.get_sketchfab_status = self.provider_status_service.get_sketchfab_status
        self.get_polyhaven_categories = self.polyhaven_service.get_polyhaven_categories
        self.search_polyhaven_assets = self.polyhaven_service.search_polyhaven_assets
        self.download_polyhaven_asset = self.polyhaven_service.download_polyhaven_asset
        self.set_texture = self.polyhaven_service.set_texture
        self.search_sketchfab_models = self.sketchfab_service.search_sketchfab_models
        self.download_sketchfab_model = self.sketchfab_service.download_sketchfab_model
        self.create_rodin_job = self.hyper3d_service.create_rodin_job
        self.poll_rodin_job_status = self.hyper3d_service.poll_rodin_job_status
        self.import_generated_asset = self.hyper3d_service.import_generated_asset
        self.get_geometry_nodes_capabilities = self.geometry_nodes_intelligence_service.get_geometry_nodes_capabilities
        self.list_geometry_node_groups = self.geometry_nodes_intelligence_service.list_geometry_node_groups
        self.get_geometry_node_group_deep_info = self.geometry_nodes_intelligence_service.get_geometry_node_group_deep_info
        self.list_geometry_nodes_modifiers = self.geometry_nodes_intelligence_service.list_geometry_nodes_modifiers
        self.get_geometry_nodes_modifier_info = self.geometry_nodes_intelligence_service.get_geometry_nodes_modifier_info
        self.get_supported_geometry_node_templates = self.geometry_nodes_template_service.get_supported_geometry_node_templates
        self.create_geometry_node_group_from_template = self.geometry_nodes_template_service.create_geometry_node_group_from_template
        self.create_custom_geometry_node_recipe = self.geometry_nodes_recipe_service.create_custom_geometry_node_recipe
        self.apply_geometry_nodes_modifier = self.geometry_nodes_modifier_service.apply_geometry_nodes_modifier
        self.set_geometry_nodes_modifier_input = self.geometry_nodes_modifier_service.set_geometry_nodes_modifier_input
        self.create_procedural_asset = self.procedural_asset_generator_service.create_procedural_asset
        self.create_scatter_system = self.procedural_asset_generator_service.create_scatter_system
        self.create_curve_generator = self.procedural_asset_generator_service.create_curve_generator
        self.create_radial_array_system = self.procedural_asset_generator_service.create_radial_array_system
        self.create_panel_generator = self.procedural_asset_generator_service.create_panel_generator
        self.create_cable_or_rope_generator = self.procedural_asset_generator_service.create_cable_or_rope_generator
        self.create_terrain_noise_system = self.procedural_asset_generator_service.create_terrain_noise_system
        self.validate_geometry_node_group = self.geometry_nodes_validation_service.validate_geometry_node_group
        self.create_geometry_nodes_preview = self.geometry_nodes_preview_service.create_geometry_nodes_preview
        self.create_geometry_nodes_scene_kit = self.geometry_nodes_preview_service.create_geometry_nodes_scene_kit
        self.delete_geometry_node_groups = self.geometry_nodes_validation_service.delete_geometry_node_groups
        self.remove_geometry_nodes_modifiers = self.geometry_nodes_modifier_service.remove_geometry_nodes_modifiers
        self.run_geometry_nodes_workflow_batch = self.geometry_nodes_workflow_batch_service.run_geometry_nodes_workflow_batch
        self.complete_geometry_node = self.geometry_nodes_service.complete_geometry_node
        self.get_geometry_nodes_status = self.geometry_nodes_service.get_geometry_nodes_status
        self.get_addon_management_status = self.addon_management_service.get_addon_management_status
        self.list_blender_addons = self.addon_management_service.list_blender_addons
        self.get_blender_addon_info = self.addon_management_service.get_blender_addon_info
        self.install_local_addon = self.addon_management_service.install_local_addon
        self.enable_blender_addon = self.addon_management_service.enable_blender_addon
        self.disable_blender_addon = self.addon_management_service.disable_blender_addon
        self.remove_blender_addon = self.addon_management_service.remove_blender_addon
        self.create_addon_skeleton = self.addon_development_service.create_addon_skeleton
        self.validate_addon_skeleton = self.addon_development_service.validate_addon_skeleton
        self.package_addon_zip = self.addon_development_service.package_addon_zip
        self.inspect_blender_api_docs = self.blender_api_knowledge_service.inspect_blender_api_docs
        self.build_blender_api_index = self.blender_api_knowledge_service.build_blender_api_index
        self.search_blender_api_docs = self.blender_api_knowledge_service.search_blender_api_docs
        self.get_blender_api_topic = self.blender_api_knowledge_service.get_blender_api_topic
        self.create_verified_snippet = self.verified_snippet_library_service.create_verified_snippet
        self.validate_verified_snippet = self.verified_snippet_library_service.validate_verified_snippet
        self.list_verified_snippets = self.verified_snippet_library_service.list_verified_snippets
        self.search_verified_snippets = self.verified_snippet_library_service.search_verified_snippets
        self.get_verified_snippet = self.verified_snippet_library_service.get_verified_snippet
        self.run_verified_snippet_smoke = self.verified_snippet_library_service.run_verified_snippet_smoke
        self.delete_verified_snippets = self.verified_snippet_library_service.delete_verified_snippets
        self.create_skill_pack = self.skill_pack_service.create_skill_pack
        self.validate_skill_pack = self.skill_pack_service.validate_skill_pack
        self.list_skill_packs = self.skill_pack_service.list_skill_packs
        self.get_skill_pack = self.skill_pack_service.get_skill_pack
        self.run_skill_pack = self.skill_pack_service.run_skill_pack
        self.delete_skill_packs = self.skill_pack_service.delete_skill_packs
        self.export_project_review_package = self.review_package_export_service.export_project_review_package
        self.validate_review_package = self.review_package_export_service.validate_review_package
        self.run_advanced_knowledge_workflow_batch = self.advanced_knowledge_workflow_batch_service.run_advanced_knowledge_workflow_batch
        self.get_preferences_schema = self.preferences_configuration_service.get_preferences_schema
        self.get_runtime_preferences = self.preferences_configuration_service.get_runtime_preferences
        self.update_runtime_preferences = self.preferences_configuration_service.update_runtime_preferences
        self.validate_runtime_preferences = self.preferences_configuration_service.validate_runtime_preferences
        self.reset_runtime_preferences = self.preferences_configuration_service.reset_runtime_preferences
        self.get_tool_profiles = self.tool_profile_service.get_tool_profiles
        self.get_active_tool_profile = self.tool_profile_service.get_active_tool_profile
        self.set_active_tool_profile = self.tool_profile_service.set_active_tool_profile
        self.preview_tool_profile = self.tool_profile_service.preview_tool_profile
        self.get_visible_tool_budget = self.tool_profile_service.get_visible_tool_budget
        self.get_enabled_tool_packs = self.tool_profile_service.get_enabled_tool_packs
        self.set_enabled_tool_packs = self.tool_profile_service.set_enabled_tool_packs
        self.recommend_tool_profile = self.tool_profile_service.recommend_tool_profile
        self.list_bundled_skill_packs = self.bundled_skill_pack_service.list_bundled_skill_packs
        self.get_bundled_skill_pack = self.bundled_skill_pack_service.get_bundled_skill_pack
        self.search_bundled_skill_packs = self.bundled_skill_pack_service.search_bundled_skill_packs
        self.activate_skill_pack = self.bundled_skill_pack_service.activate_skill_pack
        self.deactivate_skill_pack = self.bundled_skill_pack_service.deactivate_skill_pack
        self.recommend_skill_packs = self.bundled_skill_pack_service.recommend_skill_packs
        self.validate_skill_pack_readiness = self.bundled_skill_pack_service.validate_skill_pack_readiness
        self.list_addon_source_roots = self.addon_interop_inspection_service.list_addon_source_roots
        self.scan_addon_sources_readonly = self.addon_interop_inspection_service.scan_addon_sources_readonly
        self.get_addon_source_summary = self.addon_interop_inspection_service.get_addon_source_summary
        self.search_addon_operators = self.addon_interop_inspection_service.search_addon_operators
        self.search_addon_panels = self.addon_interop_inspection_service.search_addon_panels
        self.search_addon_properties = self.addon_interop_inspection_service.search_addon_properties
        self.plan_addon_operator_invocation = self.addon_interop_inspection_service.plan_addon_operator_invocation
        self.execute_approved_addon_operator = self.addon_interop_inspection_service.execute_approved_addon_operator
        self.get_error_catalog = self.user_facing_error_service.get_error_catalog
        self.explain_error = self.user_facing_error_service.explain_error
        self.get_remediation_steps = self.user_facing_error_service.get_remediation_steps
        self.get_runtime_dashboard = self.runtime_ux_status_service.get_runtime_dashboard
        self.get_approval_queue_summary = self.runtime_ux_status_service.get_approval_queue_summary
        self.get_recent_operation_summary = self.runtime_ux_status_service.get_recent_operation_summary
        self.get_setup_status = self.onboarding_workflow_service.get_setup_status
        self.run_onboarding_checklist = self.onboarding_workflow_service.run_onboarding_checklist
        self.run_product_polish_workflow_batch = self.product_polish_workflow_batch_service.run_product_polish_workflow_batch

    def start(self):
        if self.running:
            print("Server is already running")
            return

        self.running = True

        try:
            # Create socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(1)

            # Start server thread
            self.server_thread = threading.Thread(target=self._server_loop)
            self.server_thread.daemon = True
            self.server_thread.start()

            print(f"Overtli-Blender server started on {self.host}:{self.port}")
        except Exception as e:
            print(f"Failed to start server: {str(e)}")
            self.stop()

    def stop(self):
        self.running = False

        # Close socket
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None

        # Wait for thread to finish
        if self.server_thread:
            try:
                if self.server_thread.is_alive():
                    self.server_thread.join(timeout=1.0)
            except:
                pass
            self.server_thread = None

        print("Overtli-Blender server stopped")

    def _server_loop(self):
        """Main server loop in a separate thread"""
        print("Server thread started")
        self.socket.settimeout(1.0)  # Timeout to allow for stopping

        while self.running:
            try:
                # Accept new connection
                try:
                    client, address = self.socket.accept()
                    print(f"Connected to client: {address}")

                    # Handle client in a separate thread
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client,)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                except socket.timeout:
                    # Just check running condition
                    continue
                except Exception as e:
                    print(f"Error accepting connection: {str(e)}")
                    time.sleep(0.5)
            except Exception as e:
                print(f"Error in server loop: {str(e)}")
                if not self.running:
                    break
                time.sleep(0.5)

        print("Server thread stopped")

    def _handle_client(self, client):
        """Handle connected client"""
        print("Client handler started")
        client.settimeout(None)  # No timeout
        buffer = b''

        try:
            while self.running:
                # Receive data
                try:
                    data = client.recv(8192)
                    if not data:
                        print("Client disconnected")
                        break

                    buffer += data
                    try:
                        # Try to parse command
                        command = json.loads(buffer.decode('utf-8'))
                        buffer = b''

                        # Execute command in Blender's main thread
                        def execute_wrapper():
                            try:
                                response = self.execute_command(command)
                                response_json = json.dumps(response)
                                try:
                                    client.sendall(response_json.encode('utf-8'))
                                except:
                                    print("Failed to send response - client disconnected")
                            except Exception as e:
                                print(f"Error executing command: {str(e)}")
                                traceback.print_exc()
                                try:
                                    error_response = {
                                        "status": "error",
                                        "message": str(e)
                                    }
                                    client.sendall(json.dumps(error_response).encode('utf-8'))
                                except:
                                    pass
                            return None

                        # Schedule execution in main thread
                        bpy.app.timers.register(execute_wrapper, first_interval=0.0)
                    except json.JSONDecodeError:
                        # Incomplete data, wait for more
                        pass
                except Exception as e:
                    print(f"Error receiving data: {str(e)}")
                    break
        except Exception as e:
            print(f"Error in client handler: {str(e)}")
        finally:
            try:
                client.close()
            except:
                pass
            print("Client handler stopped")

    def execute_command(self, command):
        """Execute a command in the main Blender thread"""
        try:
            return self._execute_command_internal(command)

        except Exception as e:
            print(f"Error executing command: {str(e)}")
            traceback.print_exc()
            return {"status": "error", "message": str(e)}

    def _execute_command_internal(self, command):
        """Internal command execution with proper context"""
        return self._dispatch_command(command)

    def _build_command_handlers(self):
        """Build the command-to-handler registry for the current addon state."""
        handlers = {
            "get_scene_info": self.get_scene_info,
            "get_object_info": self.get_object_info,
            "get_viewport_screenshot": self.get_viewport_screenshot,
            "get_scene_index": self.get_scene_index,
            "get_object_deep_info": self.get_object_deep_info,
            "get_selection_info": self.get_selection_info,
            "get_scene_health": self.get_scene_health,
            "capture_viewport_pack": self.capture_viewport_pack,
            "create_verification_snapshot": self.create_verification_snapshot,
            "list_verification_snapshots": self.list_verification_snapshots,
            "get_supported_edit_operations": self.get_supported_edit_operations,
            "create_primitive_object": self.create_primitive_object,
            "create_box": self.create_box,
            "transform_object": self.transform_object,
            "transform_object_dimensions": self.transform_object_dimensions,
            "duplicate_object": self.duplicate_object,
            "delete_objects": self.delete_objects,
            "clear_scene": self.clear_scene,
            "scene_cleanup_plan": self.scene_cleanup_plan,
            "validate_ground_contact": self.validate_ground_contact,
            "align_object_to_surface": self.align_object_to_surface,
            "validate_scene_composition": self.validate_scene_composition,
            "set_object_visibility": self.set_object_visibility,
            "create_basic_material": self.create_basic_material,
            "assign_material": self.assign_material,
            "update_material_properties": self.update_material_properties,
            "get_material_channel_schema": self.get_material_channel_schema,
            "get_supported_material_templates": self.get_supported_material_templates,
            "list_materials_deep": self.list_materials_deep,
            "get_material_deep_info": self.get_material_deep_info,
            "get_shader_graph": self.get_shader_graph,
            "create_material_from_template": self.create_material_from_template,
            "create_custom_material": self.create_custom_material,
            "create_procedural_material": self.create_procedural_material,
            "create_material_variant": self.create_material_variant,
            "apply_material_to_objects": self.apply_material_to_objects,
            "bind_material_texture_map": self.bind_material_texture_map,
            "get_bake_capabilities": self.get_bake_capabilities,
            "validate_bake_setup": self.validate_bake_setup,
            "estimate_bake_cost": self.estimate_bake_cost,
            "create_bake_target_images": self.create_bake_target_images,
            "assign_bake_targets": self.assign_bake_targets,
            "list_bake_targets": self.list_bake_targets,
            "bake_material_maps": self.bake_material_maps,
            "bake_selected_to_active": self.bake_selected_to_active,
            "bake_procedural_material": self.bake_procedural_material,
            "bake_derived_map": self.bake_derived_map,
            "bake_curvature_map": self.bake_curvature_map,
            "bake_thickness_map": self.bake_thickness_map,
            "pack_texture_channels": self.pack_texture_channels,
            "unpack_texture_channels": self.unpack_texture_channels,
            "validate_packed_texture": self.validate_packed_texture,
            "save_baked_textures": self.save_baked_textures,
            "validate_baked_textures": self.validate_baked_textures,
            "relink_baked_textures": self.relink_baked_textures,
            "create_baked_material": self.create_baked_material,
            "plan_bake_cleanup": self.plan_bake_cleanup,
            "execute_bake_cleanup": self.execute_bake_cleanup,
            "run_verified_bake_workflow": self.run_verified_bake_workflow,
            "list_project_images": self.list_project_images,
            "get_image_resource_info": self.get_image_resource_info,
            "rename_image_resource": self.rename_image_resource,
            "set_material_node_input": self.set_material_node_input,
            "add_material_node": self.add_material_node,
            "connect_material_nodes": self.connect_material_nodes,
            "remove_material_node": self.remove_material_node,
            "create_material_preview": self.create_material_preview,
            "run_material_workflow_batch": self.run_material_workflow_batch,
            "delete_materials": self.delete_materials,
            "get_selection_deep_info": self.get_selection_deep_info,
            "get_mesh_component_summary": self.get_mesh_component_summary,
            "create_vertex_group": self.create_vertex_group,
            "update_vertex_group_weights": self.update_vertex_group_weights,
            "list_vertex_groups": self.list_vertex_groups,
            "delete_vertex_groups": self.delete_vertex_groups,
            "create_shape_key": self.create_shape_key,
            "update_shape_key_value": self.update_shape_key_value,
            "edit_shape_key_offsets": self.edit_shape_key_offsets,
            "list_shape_keys": self.list_shape_keys,
            "delete_shape_keys": self.delete_shape_keys,
            "create_lattice_deformer": self.create_lattice_deformer,
            "update_lattice_deformer": self.update_lattice_deformer,
            "apply_lattice_to_object": self.apply_lattice_to_object,
            "remove_lattice_deformer": self.remove_lattice_deformer,
            "add_deformation_modifier": self.add_deformation_modifier,
            "update_deformation_modifier": self.update_deformation_modifier,
            "create_region_deformation": self.create_region_deformation,
            "run_deformation_workflow_batch": self.run_deformation_workflow_batch,
            "get_method_plan": self.get_method_plan,
            "list_operation_playbooks": self.list_operation_playbooks,
            "get_tricks_knowledge_base": self.get_tricks_knowledge_base,
            "get_anti_pattern_rules": self.get_anti_pattern_rules,
            "get_modifier_recipes": self.get_modifier_recipes,
            "score_selection_confidence": self.score_selection_confidence,
            "scan_blender_asset_libraries": self.scan_blender_asset_libraries,
            "preview_asset": self.preview_asset,
            "import_texture_folder": self.import_texture_folder,
            "create_style_material": self.create_style_material,
            "create_paintable_texture": self.create_paintable_texture,
            "delete_images": self.delete_images,
            "list_uv_maps": self.list_uv_maps,
            "create_vertex_group_from_uv_island": self.create_vertex_group_from_uv_island,
            "measure_object": self.measure_object,
            "measure_distance": self.measure_distance,
            "create_proportional_deformation": self.create_proportional_deformation,
            "get_sculpt_status": self.get_sculpt_status,
            "configure_sculpt_brush": self.configure_sculpt_brush,
            "create_sculpt_mask_from_vertex_group": self.create_sculpt_mask_from_vertex_group,
            "run_shape_key_sculpt_workflow": self.run_shape_key_sculpt_workflow,
            "get_modeling_capabilities": self.get_modeling_capabilities,
            "validate_mesh_schema": self.validate_mesh_schema,
            "create_mesh_from_schema": self.create_mesh_from_schema,
            "create_profile_curve": self.create_profile_curve,
            "extrude_profile": self.extrude_profile,
            "lathe_profile": self.lathe_profile,
            "loft_profiles": self.loft_profiles,
            "bridge_profile_loops": self.bridge_profile_loops,
            "create_curve_path_object": self.create_curve_path_object,
            "create_beveled_curve_object": self.create_beveled_curve_object,
            "create_modifier_stack": self.create_modifier_stack,
            "create_hard_surface_panel": self.create_hard_surface_panel,
            "create_pipe_or_rail": self.create_pipe_or_rail,
            "create_modular_assembly": self.create_modular_assembly,
            "plan_reference_construction": self.plan_reference_construction,
            "run_reference_construction_step": self.run_reference_construction_step,
            "validate_reference_alignment": self.validate_reference_alignment,
            "configure_sculpt_session": self.configure_sculpt_session,
            "create_sculpt_mask": self.create_sculpt_mask,
            "create_face_set": self.create_face_set,
            "apply_sculpt_stroke_batch": self.apply_sculpt_stroke_batch,
            "create_shape_key_sculpt_variant": self.create_shape_key_sculpt_variant,
            "validate_sculpt_result": self.validate_sculpt_result,
            "create_cloth_pattern_panel": self.create_cloth_pattern_panel,
            "define_cloth_seam_pair": self.define_cloth_seam_pair,
            "create_cloth_setup": self.create_cloth_setup,
            "create_cloth_pin_group": self.create_cloth_pin_group,
            "create_cloth_collision_setup": self.create_cloth_collision_setup,
            "simulate_cloth_preview": self.simulate_cloth_preview,
            "bake_cloth_cache": self.bake_cloth_cache,
            "clear_cloth_cache": self.clear_cloth_cache,
            "convert_cloth_result": self.convert_cloth_result,
            "validate_construction_geometry": self.validate_construction_geometry,
            "plan_construction_cleanup": self.plan_construction_cleanup,
            "execute_construction_cleanup": self.execute_construction_cleanup,
            "run_advanced_modeling_workflow_batch": self.run_advanced_modeling_workflow_batch,
            "get_animation_system_capabilities": self.get_animation_system_capabilities,
            "inspect_animation_system": self.inspect_animation_system,
            "list_actions": self.list_actions,
            "get_action_deep_info": self.get_action_deep_info,
            "create_action": self.create_action,
            "duplicate_action": self.duplicate_action,
            "rename_action": self.rename_action,
            "assign_action": self.assign_action,
            "delete_actions": self.delete_actions,
            "insert_keyframe_batch": self.insert_keyframe_batch,
            "edit_keyframes": self.edit_keyframes,
            "retime_action": self.retime_action,
            "set_fcurve_interpolation": self.set_fcurve_interpolation,
            "add_fcurve_modifier": self.add_fcurve_modifier,
            "remove_fcurve_modifier": self.remove_fcurve_modifier,
            "validate_fcurves": self.validate_fcurves,
            "create_nla_track": self.create_nla_track,
            "add_action_to_nla": self.add_action_to_nla,
            "edit_nla_strip": self.edit_nla_strip,
            "mute_nla_track": self.mute_nla_track,
            "delete_nla_tracks": self.delete_nla_tracks,
            "validate_nla_stack": self.validate_nla_stack,
            "create_driver_from_dsl": self.create_driver_from_dsl,
            "validate_driver_dsl": self.validate_driver_dsl,
            "list_drivers": self.list_drivers,
            "get_driver_info": self.get_driver_info,
            "remove_drivers": self.remove_drivers,
            "create_rig_template": self.create_rig_template,
            "create_control_bones": self.create_control_bones,
            "create_ik_chain": self.create_ik_chain,
            "add_rig_constraint": self.add_rig_constraint,
            "remove_rig_constraints": self.remove_rig_constraints,
            "add_custom_rig_properties": self.add_custom_rig_properties,
            "validate_rig": self.validate_rig,
            "inspect_pose": self.inspect_pose,
            "create_pose_snapshot": self.create_pose_snapshot,
            "apply_pose_snapshot": self.apply_pose_snapshot,
            "create_pose_asset": self.create_pose_asset,
            "list_pose_assets": self.list_pose_assets,
            "compare_poses": self.compare_poses,
            "delete_pose_assets": self.delete_pose_assets,
            "create_shot_range": self.create_shot_range,
            "create_camera_cut": self.create_camera_cut,
            "create_timeline_marker": self.create_timeline_marker,
            "create_shot_plan": self.create_shot_plan,
            "validate_shot_plan": self.validate_shot_plan,
            "create_motion_path_preview": self.create_motion_path_preview,
            "validate_motion": self.validate_motion,
            "get_simulation_capabilities": self.get_simulation_capabilities,
            "inspect_simulation_state": self.inspect_simulation_state,
            "configure_rigidbody_basic": self.configure_rigidbody_basic,
            "configure_cloth_simulation_advanced": self.configure_cloth_simulation_advanced,
            "configure_softbody_basic": self.configure_softbody_basic,
            "configure_hair_curve_dynamics_basic": self.configure_hair_curve_dynamics_basic,
            "get_simulation_cache_status": self.get_simulation_cache_status,
            "simulate_preview_range": self.simulate_preview_range,
            "bake_simulation_cache": self.bake_simulation_cache,
            "clear_simulation_cache": self.clear_simulation_cache,
            "run_animation_rigging_workflow_batch": self.run_animation_rigging_workflow_batch,
            "get_preferences_schema": self.get_preferences_schema,
            "get_runtime_preferences": self.get_runtime_preferences,
            "update_runtime_preferences": self.update_runtime_preferences,
            "validate_runtime_preferences": self.validate_runtime_preferences,
            "reset_runtime_preferences": self.reset_runtime_preferences,
            "get_tool_profiles": self.get_tool_profiles,
            "get_active_tool_profile": self.get_active_tool_profile,
            "set_active_tool_profile": self.set_active_tool_profile,
            "preview_tool_profile": self.preview_tool_profile,
            "get_visible_tool_budget": self.get_visible_tool_budget,
            "get_enabled_tool_packs": self.get_enabled_tool_packs,
            "set_enabled_tool_packs": self.set_enabled_tool_packs,
            "recommend_tool_profile": self.recommend_tool_profile,
            "list_bundled_skill_packs": self.list_bundled_skill_packs,
            "get_bundled_skill_pack": self.get_bundled_skill_pack,
            "search_bundled_skill_packs": self.search_bundled_skill_packs,
            "activate_skill_pack": self.activate_skill_pack,
            "deactivate_skill_pack": self.deactivate_skill_pack,
            "recommend_skill_packs": self.recommend_skill_packs,
            "validate_skill_pack_readiness": self.validate_skill_pack_readiness,
            "list_addon_source_roots": self.list_addon_source_roots,
            "scan_addon_sources_readonly": self.scan_addon_sources_readonly,
            "get_addon_source_summary": self.get_addon_source_summary,
            "search_addon_operators": self.search_addon_operators,
            "search_addon_panels": self.search_addon_panels,
            "search_addon_properties": self.search_addon_properties,
            "plan_addon_operator_invocation": self.plan_addon_operator_invocation,
            "execute_approved_addon_operator": self.execute_approved_addon_operator,
            "get_error_catalog": self.get_error_catalog,
            "explain_error": self.explain_error,
            "get_remediation_steps": self.get_remediation_steps,
            "get_runtime_dashboard": self.get_runtime_dashboard,
            "get_approval_queue_summary": self.get_approval_queue_summary,
            "get_recent_operation_summary": self.get_recent_operation_summary,
            "get_setup_status": self.get_setup_status,
            "run_onboarding_checklist": self.run_onboarding_checklist,
            "run_product_polish_workflow_batch": self.run_product_polish_workflow_batch,
            "get_timeline_info": self.get_timeline_info,
            "list_animated_objects": self.list_animated_objects,
            "get_animation_deep_info": self.get_animation_deep_info,
            "set_timeline_range": self.set_timeline_range,
            "set_current_frame": self.set_current_frame,
            "insert_transform_keyframes": self.insert_transform_keyframes,
            "animate_object_transform": self.animate_object_transform,
            "animate_camera_transform": self.animate_camera_transform,
            "animate_light_property": self.animate_light_property,
            "animate_material_property": self.animate_material_property,
            "animate_shape_key_value": self.animate_shape_key_value,
            "delete_animation_data": self.delete_animation_data,
            "create_camera": self.create_camera,
            "frame_camera_to_objects": self.frame_camera_to_objects,
            "set_active_camera": self.set_active_camera,
            "create_light": self.create_light,
            "create_lighting_setup": self.create_lighting_setup,
            "update_light": self.update_light,
            "set_world_lighting": self.set_world_lighting,
            "get_render_settings": self.get_render_settings,
            "set_render_settings": self.set_render_settings,
            "get_supported_color_management": self.get_supported_color_management,
            "set_output_path": self.set_output_path,
            "render_still": self.render_still,
            "render_contact_sheet": self.render_contact_sheet,
            "create_turntable_animation": self.create_turntable_animation,
            "render_preview_animation": self.render_preview_animation,
            "get_compositor_status": self.get_compositor_status,
            "set_compositor_preset": self.set_compositor_preset,
            "set_render_passes": self.set_render_passes,
            "run_presentation_workflow_batch": self.run_presentation_workflow_batch,
            "cleanup_presentation_artifacts": self.cleanup_presentation_artifacts,
            "get_supported_asset_formats": self.get_supported_asset_formats,
            "scan_asset_folder": self.scan_asset_folder,
            "list_asset_libraries": self.list_asset_libraries,
            "list_scene_assets": self.list_scene_assets,
            "get_asset_file_info": self.get_asset_file_info,
            "get_asset_dependency_report": self.get_asset_dependency_report,
            "create_asset_manifest": self.create_asset_manifest,
            "append_blend_asset": self.append_blend_asset,
            "import_model_file": self.import_model_file,
            "export_selected_objects": self.export_selected_objects,
            "export_scene": self.export_scene,
            "create_asset_preview": self.create_asset_preview,
            "create_asset_contact_sheet": self.create_asset_contact_sheet,
            "create_scene_kit": self.create_scene_kit,
            "import_scene_kit": self.import_scene_kit,
            "validate_scene_kit": self.validate_scene_kit,
            "list_scene_kits": self.list_scene_kits,
            "collect_external_dependencies": self.collect_external_dependencies,
            "validate_external_dependencies": self.validate_external_dependencies,
            "pack_external_data": self.pack_external_data,
            "make_paths_relative": self.make_paths_relative,
            "cleanup_asset_artifacts": self.cleanup_asset_artifacts,
            "run_asset_workflow_batch": self.run_asset_workflow_batch,
            "inspect_rigging": self.inspect_rigging,
            "create_armature": self.create_armature,
            "parent_mesh_to_armature": self.parent_mesh_to_armature,
            "pose_bone_transform": self.pose_bone_transform,
            "add_driver": self.add_driver,
            "remove_driver": self.remove_driver,
            "add_physics_basic": self.add_physics_basic,
            "add_object_modifier": self.add_object_modifier,
            "update_object_modifier": self.update_object_modifier,
            "remove_object_modifier": self.remove_object_modifier,
            "create_collection": self.create_collection,
            "move_objects_to_collection": self.move_objects_to_collection,
            "delete_collection": self.delete_collection,
            "run_verified_edit_batch": self.run_verified_edit_batch,
            "get_task_workspace": self.get_task_workspace,
            "create_workspace_task": self.create_workspace_task,
            "update_workspace_task": self.update_workspace_task,
            "complete_workspace_task": self.complete_workspace_task,
            "create_scene_plan": self.create_scene_plan,
            "list_scene_plan": self.list_scene_plan,
            "list_workspace_tasks": self.list_workspace_tasks,
            "add_workspace_todo": self.add_workspace_todo,
            "update_workspace_todo": self.update_workspace_todo,
            "list_workspace_todos": self.list_workspace_todos,
            "record_operation_journal_entry": self.record_operation_journal_entry,
            "get_operation_journal": self.get_operation_journal,
            "create_scene_snapshot": self.create_scene_snapshot,
            "list_scene_snapshots": self.list_scene_snapshots,
            "diff_scene_snapshots": self.diff_scene_snapshots,
            "detect_user_changes": self.detect_user_changes,
            "rollback_to_scene_snapshot": self.rollback_to_scene_snapshot,
            "undo_last_blender_operation": self.undo_last_blender_operation,
            "get_safety_status": self.get_safety_status,
            "get_system_status": self.get_system_status,
            "get_project_status": self.get_project_status,
            "get_loaded_project_folder": self.get_loaded_project_folder,
            "resolve_project_workspace": self.resolve_project_workspace,
            "initialize_temp_workspace": self.initialize_temp_workspace,
            "promote_temp_workspace_to_project": self.promote_temp_workspace_to_project,
            "initialize_project_workspace": self.initialize_project_workspace,
            "validate_project_layout": self.validate_project_layout,
            "repair_project_layout": self.repair_project_layout,
            "register_blend_file": self.register_blend_file,
            "save_project_as": self.save_project_as,
            "resave_project_folder": self.resave_project_folder,
            "plan_project_folder_move": self.plan_project_folder_move,
            "move_project_folder": self.move_project_folder,
            "create_project_backup": self.create_project_backup,
            "restore_project_backup": self.restore_project_backup,
            "collect_project_dependencies": self.collect_project_dependencies,
            "get_file_access_policy": self.get_file_access_policy,
            "set_file_access_policy": self.set_file_access_policy,
            "validate_path_access": self.validate_path_access,
            "list_approved_roots": self.list_approved_roots,
            "add_approved_root": self.add_approved_root,
            "remove_approved_root": self.remove_approved_root,
            "detect_drive_roots": self.detect_drive_roots,
            "approve_drive_roots": self.approve_drive_roots,
            "scan_project_files": self.scan_project_files,
            "read_project_text_file": self.read_project_text_file,
            "write_project_text_file": self.write_project_text_file,
            "copy_file_into_project": self.copy_file_into_project,
            "plan_file_delete": self.plan_file_delete,
            "execute_approved_file_delete": self.execute_approved_file_delete,
            "get_cache_status": self.get_cache_status,
            "plan_cache_cleanup": self.plan_cache_cleanup,
            "execute_cache_cleanup": self.execute_cache_cleanup,
            "pin_artifact": self.pin_artifact,
            "unpin_artifact": self.unpin_artifact,
            "find_orphaned_artifacts": self.find_orphaned_artifacts,
            "compact_operation_history": self.compact_operation_history,
            "create_task": self.create_task,
            "update_task": self.update_task,
            "list_tasks": self.list_tasks,
            "get_task": self.get_task,
            "set_task_status": self.set_task_status,
            "link_task_artifact": self.link_task_artifact,
            "link_task_target": self.link_task_target,
            "mark_task_verified": self.mark_task_verified,
            "mark_task_stale": self.mark_task_stale,
            "archive_tasks": self.archive_tasks,
            "get_task_graph": self.get_task_graph,
            "detect_stale_tasks": self.detect_stale_tasks,
            "get_session_time": self.get_session_time,
            "get_scene_revision": self.get_scene_revision,
            "get_recent_operations": self.get_recent_operations,
            "get_changes_since_revision": self.get_changes_since_revision,
            "get_operation_duration": self.get_operation_duration,
            "create_scene_revision_marker": self.create_scene_revision_marker,
            "import_reference_image": self.import_reference_image,
            "create_reference_set": self.create_reference_set,
            "place_reference_view": self.place_reference_view,
            "calibrate_reference_scale": self.calibrate_reference_scale,
            "set_reference_opacity": self.set_reference_opacity,
            "set_reference_depth": self.set_reference_depth,
            "lock_reference": self.lock_reference,
            "set_reference_view_visibility": self.set_reference_view_visibility,
            "add_reference_landmark": self.add_reference_landmark,
            "measure_reference_landmarks": self.measure_reference_landmarks,
            "capture_reference_overlay": self.capture_reference_overlay,
            "list_reference_images": self.list_reference_images,
            "relink_reference_image": self.relink_reference_image,
            "remove_reference_image": self.remove_reference_image,
            "calculate_distance": self.calculate_distance,
            "calculate_angle": self.calculate_angle,
            "calculate_area": self.calculate_area,
            "calculate_volume": self.calculate_volume,
            "calculate_curve_length": self.calculate_curve_length,
            "calculate_clearance": self.calculate_clearance,
            "calculate_alignment": self.calculate_alignment,
            "convert_units": self.convert_units,
            "calculate_scale_ratio": self.calculate_scale_ratio,
            "compare_measurements": self.compare_measurements,
            "get_oriented_bounds": self.get_oriented_bounds,
            "raycast_scene": self.raycast_scene,
            "find_nearest_objects": self.find_nearest_objects,
            "detect_object_intersections": self.detect_object_intersections,
            "measure_object_to_reference": self.measure_object_to_reference,
            "plan_rename": self.plan_rename,
            "execute_rename": self.execute_rename,
            "batch_rename_datablocks": self.batch_rename_datablocks,
            "batch_rename_files": self.batch_rename_files,
            "rename_project": self.rename_project,
            "repair_references_after_rename": self.repair_references_after_rename,
            "discover_tool_packs": self.discover_tool_packs,
            "get_tool_pack": self.get_tool_pack,
            "search_tools": self.search_tools,
            "get_tool_spec": self.get_tool_spec,
            "get_recommended_tools_for_task": self.get_recommended_tools_for_task,
            "prepare_operation": self.prepare_operation,
            "get_pending_approvals": self.get_pending_approvals,
            "approve_operation": self.approve_operation,
            "deny_operation": self.deny_operation,
            "execute_approved_operation": self.execute_approved_operation,
            "approve_and_execute_operation": self.approve_and_execute_operation,
            "expire_approval": self.expire_approval,
            "get_operation_status": self.get_operation_status,
            "list_recent_operations": self.list_recent_operations,
            "cancel_operation": self.cancel_operation,
            "get_operation_log": self.get_operation_log,
            "get_permission_profile": self.get_permission_profile,
            "set_permission_profile": self.set_permission_profile,
            "get_capability_policy": self.get_capability_policy,
            "validate_command_capabilities": self.validate_command_capabilities,
            "get_log_status": self.get_log_status,
            "export_operation_log": self.export_operation_log,
            "get_command_registry_report": self.get_command_registry_report,
            "execute_code": self.execute_code,
            "get_polyhaven_status": self.get_polyhaven_status,
            "get_hyper3d_status": self.get_hyper3d_status,
            "get_sketchfab_status": self.get_sketchfab_status,
            # New composition tools
            "get_shared_context": self.get_shared_context,
            "clear_shared_context": self.clear_shared_context,
            "get_operation_history": self.get_operation_history,
            "create_object_handle": self.create_object_handle,
            "create_material_handle": self.create_material_handle,
            "list_object_handles": self.list_object_handles,
            "list_material_handles": self.list_material_handles,
            # Geometry Nodes tools
            "get_geometry_nodes_capabilities": self.get_geometry_nodes_capabilities,
            "list_geometry_node_groups": self.list_geometry_node_groups,
            "get_geometry_node_group_deep_info": self.get_geometry_node_group_deep_info,
            "list_geometry_nodes_modifiers": self.list_geometry_nodes_modifiers,
            "get_geometry_nodes_modifier_info": self.get_geometry_nodes_modifier_info,
            "get_supported_geometry_node_templates": self.get_supported_geometry_node_templates,
            "create_geometry_node_group_from_template": self.create_geometry_node_group_from_template,
            "create_custom_geometry_node_recipe": self.create_custom_geometry_node_recipe,
            "apply_geometry_nodes_modifier": self.apply_geometry_nodes_modifier,
            "set_geometry_nodes_modifier_input": self.set_geometry_nodes_modifier_input,
            "create_procedural_asset": self.create_procedural_asset,
            "create_scatter_system": self.create_scatter_system,
            "create_curve_generator": self.create_curve_generator,
            "create_radial_array_system": self.create_radial_array_system,
            "create_panel_generator": self.create_panel_generator,
            "create_cable_or_rope_generator": self.create_cable_or_rope_generator,
            "create_terrain_noise_system": self.create_terrain_noise_system,
            "validate_geometry_node_group": self.validate_geometry_node_group,
            "create_geometry_nodes_preview": self.create_geometry_nodes_preview,
            "create_geometry_nodes_scene_kit": self.create_geometry_nodes_scene_kit,
            "delete_geometry_node_groups": self.delete_geometry_node_groups,
            "remove_geometry_nodes_modifiers": self.remove_geometry_nodes_modifiers,
            "run_geometry_nodes_workflow_batch": self.run_geometry_nodes_workflow_batch,
            "complete_geometry_node": self.complete_geometry_node,
            "get_geometry_nodes_status": self.get_geometry_nodes_status,
            # Phase 6B addon, docs, snippet, skill pack, and review tools
            "get_addon_management_status": self.get_addon_management_status,
            "list_blender_addons": self.list_blender_addons,
            "get_blender_addon_info": self.get_blender_addon_info,
            "install_local_addon": self.install_local_addon,
            "enable_blender_addon": self.enable_blender_addon,
            "disable_blender_addon": self.disable_blender_addon,
            "remove_blender_addon": self.remove_blender_addon,
            "create_addon_skeleton": self.create_addon_skeleton,
            "validate_addon_skeleton": self.validate_addon_skeleton,
            "package_addon_zip": self.package_addon_zip,
            "inspect_blender_api_docs": self.inspect_blender_api_docs,
            "build_blender_api_index": self.build_blender_api_index,
            "search_blender_api_docs": self.search_blender_api_docs,
            "get_blender_api_topic": self.get_blender_api_topic,
            "create_verified_snippet": self.create_verified_snippet,
            "validate_verified_snippet": self.validate_verified_snippet,
            "list_verified_snippets": self.list_verified_snippets,
            "search_verified_snippets": self.search_verified_snippets,
            "get_verified_snippet": self.get_verified_snippet,
            "run_verified_snippet_smoke": self.run_verified_snippet_smoke,
            "delete_verified_snippets": self.delete_verified_snippets,
            "create_skill_pack": self.create_skill_pack,
            "validate_skill_pack": self.validate_skill_pack,
            "list_skill_packs": self.list_skill_packs,
            "get_skill_pack": self.get_skill_pack,
            "run_skill_pack": self.run_skill_pack,
            "delete_skill_packs": self.delete_skill_packs,
            "export_project_review_package": self.export_project_review_package,
            "validate_review_package": self.validate_review_package,
            "run_advanced_knowledge_workflow_batch": self.run_advanced_knowledge_workflow_batch,
            # Script Registry tools
            "register_context_script": self.register_context_script,
            "execute_context_script": self.execute_context_script,
            "list_context_scripts": self.list_context_scripts,
            "clear_context_scripts": self.clear_context_scripts,
        }

        # Add Polyhaven handlers only if enabled
        if bpy.context.scene.blendermcp_use_polyhaven:
            polyhaven_handlers = {
                "get_polyhaven_categories": self.get_polyhaven_categories,
                "search_polyhaven_assets": self.search_polyhaven_assets,
                "download_polyhaven_asset": self.download_polyhaven_asset,
                "set_texture": self.set_texture,
            }
            handlers.update(polyhaven_handlers)

        # Add Hyper3d handlers only if enabled
        if bpy.context.scene.blendermcp_use_hyper3d:
            polyhaven_handlers = {
                "create_rodin_job": self.create_rodin_job,
                "poll_rodin_job_status": self.poll_rodin_job_status,
                "import_generated_asset": self.import_generated_asset,
            }
            handlers.update(polyhaven_handlers)

        # Add Sketchfab handlers only if enabled
        if bpy.context.scene.blendermcp_use_sketchfab:
            sketchfab_handlers = {
                "search_sketchfab_models": self.search_sketchfab_models,
                "download_sketchfab_model": self.download_sketchfab_model,
            }
            handlers.update(sketchfab_handlers)

        return handlers

    def _dispatch_command(self, command):
        """Dispatch a command using the current handler registry."""
        cmd_type = command.get("type")
        params = self._strip_transport_metadata(command.get("params", {}))

        safety_decision = self.safety_policy_service.evaluate_command(cmd_type, params)
        if not safety_decision["allowed"]:
            return {
                "status": "error",
                "message": "Command blocked by safety policy",
                "safety": safety_decision,
            }

        # Add a handler for checking PolyHaven status
        if cmd_type == "get_polyhaven_status":
            response = {"status": "success", "result": self.get_polyhaven_status()}
            if self.safety_policy_service.mode == SAFETY_MODE_AUDIT:
                response["safety"] = safety_decision
            return response

        if cmd_type == "get_safety_status":
            return {"status": "success", "result": self.get_safety_status()}

        handlers = self._build_command_handlers()

        handler = handlers.get(cmd_type)
        if handler:
            try:
                print(f"Executing handler for {cmd_type}")
                result = self._normalize_handler_result(cmd_type, handler(**params))
                print(f"Handler execution complete")
                response = {"status": "success", "result": result}
                if self.safety_policy_service.mode == SAFETY_MODE_AUDIT:
                    response["safety"] = safety_decision
                return response
            except Exception as e:
                print(f"Error in handler: {str(e)}")
                traceback.print_exc()
                return {"status": "error", "message": str(e)}
        else:
            return {"status": "error", "message": f"Unknown command type: {cmd_type}"}

    @staticmethod
    def _strip_transport_metadata(params):
        if not isinstance(params, dict):
            return {}
        clean = dict(params)
        for key in ("ctx", "context", "_ctx", "_context", "request_context", "tool_context"):
            clean.pop(key, None)
        return clean

    @staticmethod
    def _normalize_handler_result(cmd_type, result):
        if not isinstance(result, dict):
            return result
        status = result.get("status")
        message = str(result.get("message", ""))
        if status == "error" and ("requires confirm=True" in message or "requires confirmation" in message):
            normalized = dict(result)
            normalized["status"] = "requires_approval"
            normalized["approval_required"] = True
            normalized.setdefault("command_name", cmd_type)
            normalized.setdefault("warnings", [])
            return normalized
        return result



    def get_system_status(self):
        return build_operation_response(
            status="success",
            tool="get_system_status",
            result={
                "addon": "Overtli-Blender",
                "safety_mode": self.safety_policy_service.mode,
                "blender_version": ".".join(str(part) for part in bpy.app.version),
                "governance": "phase7b",
            },
        )

    def get_project_status(self):
        return build_operation_response(
            status="success",
            tool="get_project_status",
            result=self.project_workspace_service.get_project_status(),
        )

    def discover_tool_packs(self):
        return build_operation_response(status="success", tool="discover_tool_packs", result=runtime_discover_tool_packs())

    def get_tool_pack(self, name):
        return build_operation_response(status="success", tool="get_tool_pack", result=runtime_get_tool_pack(name))

    def search_tools(self, query, category=None, tool_pack=None, risk_max=None, limit=20):
        return build_operation_response(status="success", tool="search_tools", result=runtime_search_tools(query, category=category, tool_pack=tool_pack, risk_max=risk_max, limit=limit))

    def get_tool_spec(self, name):
        return build_operation_response(status="success", tool="get_tool_spec", result=runtime_get_tool_spec(name))

    def get_recommended_tools_for_task(self, task, limit=8):
        return build_operation_response(status="success", tool="get_recommended_tools_for_task", result=runtime_get_recommended_tools_for_task(task, limit=limit))

    def prepare_operation(self, command_name, params=None):
        clean_params = self._strip_transport_metadata(params or {})
        return build_operation_response(status="requires_approval", tool="prepare_operation", result=DEFAULT_APPROVAL_RUNTIME.prepare_operation(command_name, clean_params, scene_revision=len(getattr(bpy.context.scene, "objects", []))))

    def get_pending_approvals(self):
        return build_operation_response(status="success", tool="get_pending_approvals", result=DEFAULT_APPROVAL_RUNTIME.get_pending_approvals())

    def approve_operation(self, approval_id, execute_after_approval=True, approve_only=False):
        if execute_after_approval and not approve_only:
            return self.approve_and_execute_operation(approval_id, reason="execute_after_approval requested")
        return build_operation_response(status="success", tool="approve_operation", result=DEFAULT_APPROVAL_RUNTIME.approve_operation(approval_id))

    def deny_operation(self, approval_id, reason=None):
        return build_operation_response(status="success", tool="deny_operation", result=DEFAULT_APPROVAL_RUNTIME.deny_operation(approval_id, reason=reason))

    def execute_approved_operation(self, approval_id, command_name=None, params=None):
        if not command_name:
            getter = getattr(DEFAULT_APPROVAL_RUNTIME, "get_approval_record", None)
            record_result = getter(approval_id) if getter else {"status": "error", "message": "Approval runtime cannot load stored command metadata."}
            if record_result.get("status") != "success":
                return build_operation_response(status=record_result.get("status", "error"), tool="execute_approved_operation", result=record_result)
            approval_record = record_result.get("approval", {})
            command_name = approval_record.get("command_name")
            params = approval_record.get("params") if params is None else self._strip_transport_metadata(params)
            if not command_name:
                result = {"status": "error", "message": "Approval record does not include a command name.", "approval": approval_record}
                return build_operation_response(status="error", tool="execute_approved_operation", result=result)
        if command_name in {
            "prepare_operation",
            "approve_operation",
            "deny_operation",
            "execute_approved_operation",
            "approve_and_execute_operation",
            "expire_approval",
        }:
            result = {"status": "error", "message": f"Approval executor cannot dispatch governance command: {command_name}"}
            return build_operation_response(status="error", tool="execute_approved_operation", result=result)
        validator = getattr(DEFAULT_APPROVAL_RUNTIME, "validate_approved_operation", None)
        if validator:
            params = self._strip_transport_metadata(params or {})
            validation = validator(approval_id, command_name, params)
        else:
            params = self._strip_transport_metadata(params or {})
            validation = DEFAULT_APPROVAL_RUNTIME.execute_approved_operation(approval_id, command_name, params)
        if validation.get("status") != "success":
            return build_operation_response(status=validation.get("status", "error"), tool="execute_approved_operation", result=validation)
        dispatch_result = self._dispatch_command({"type": command_name, "params": params or {}})
        if dispatch_result.get("status") == "success":
            marker = getattr(DEFAULT_APPROVAL_RUNTIME, "mark_executed", None)
            if marker:
                marker(approval_id)
        result = {
            "status": dispatch_result.get("status", "error"),
            "approval": validation.get("approval"),
            "dispatch": dispatch_result,
        }
        return build_operation_response(status=result["status"], tool="execute_approved_operation", result=result)

    def approve_and_execute_operation(self, approval_id, expected_command_name=None, expected_params_hash=None, reason=None):
        validator = getattr(DEFAULT_APPROVAL_RUNTIME, "approve_and_validate_operation", None)
        if validator:
            validation = validator(approval_id, expected_command_name, expected_params_hash)
        else:
            approved = DEFAULT_APPROVAL_RUNTIME.approve_operation(approval_id)
            if approved.get("status") != "success":
                return build_operation_response(status=approved.get("status", "error"), tool="approve_and_execute_operation", result=approved)
            validation = approved
        if validation.get("status") != "success":
            return build_operation_response(status=validation.get("status", "error"), tool="approve_and_execute_operation", result=validation)
        approval = validation.get("approval", {})
        command_name = approval.get("command_name")
        params = approval.get("params") or {}
        if not command_name:
            result = {"status": "error", "message": "Approval record does not include a command name.", "approval": approval}
            return build_operation_response(status="error", tool="approve_and_execute_operation", result=result)
        executed = self.execute_approved_operation(approval_id, command_name, params)
        if isinstance(executed, dict):
            executed.setdefault("result", {}).setdefault("reason", reason)
        return executed

    def expire_approval(self, approval_id=None):
        return build_operation_response(status="success", tool="expire_approval", result=DEFAULT_APPROVAL_RUNTIME.expire_approval(approval_id))

    def get_operation_status(self, operation_id=None):
        return build_operation_response(status="success", tool="get_operation_status", result=DEFAULT_OPERATION_RUNTIME.get_operation_status(operation_id))

    def list_recent_operations(self, limit=20):
        return build_operation_response(status="success", tool="list_recent_operations", result=DEFAULT_OPERATION_RUNTIME.list_recent_operations(limit))

    def cancel_operation(self, operation_id):
        result = DEFAULT_OPERATION_RUNTIME.cancel_operation(operation_id)
        return build_operation_response(status=result.get("status", "success"), tool="cancel_operation", result=result)

    def get_operation_log(self, operation_id=None):
        return build_operation_response(status="success", tool="get_operation_log", result=DEFAULT_OPERATION_RUNTIME.get_operation_log(operation_id))

    def get_permission_profile(self):
        return build_operation_response(status="success", tool="get_permission_profile", result=runtime_get_permission_profile())

    def set_permission_profile(self, profile, confirm=False):
        result = runtime_set_permission_profile(profile, confirm=confirm)
        return build_operation_response(status=result.get("status", "success"), tool="set_permission_profile", result=result)

    def get_capability_policy(self):
        return build_operation_response(status="success", tool="get_capability_policy", result=runtime_get_capability_policy())

    def validate_command_capabilities(self, command_name, profile=None):
        result = runtime_validate_command_capabilities(command_name, profile=profile)
        return build_operation_response(status=result.get("status", "success"), tool="validate_command_capabilities", result=result)

    def get_log_status(self):
        return build_operation_response(status="success", tool="get_log_status", result=runtime_get_log_status())

    def export_operation_log(self, operation_id=None):
        return build_operation_response(status="success", tool="export_operation_log", result=runtime_export_operation_log(operation_id))

    def get_command_registry_report(self):
        return build_operation_response(status="success", tool="get_command_registry_report", result=command_registry_report())

    def get_scene_info(self):
        """Get information about the current Blender scene"""
        return self.scene_observation_service.get_scene_info()

    @staticmethod
    def _get_aabb(obj):
        """ Returns the world-space axis-aligned bounding box (AABB) of an object. """
        if obj.type != 'MESH':
            raise TypeError("Object must be a mesh")

        # Get the bounding box corners in local space
        local_bbox_corners = [mathutils.Vector(corner) for corner in obj.bound_box]

        # Convert to world coordinates
        world_bbox_corners = [obj.matrix_world @ corner for corner in local_bbox_corners]

        # Compute axis-aligned min/max coordinates
        min_corner = mathutils.Vector(map(min, zip(*world_bbox_corners)))
        max_corner = mathutils.Vector(map(max, zip(*world_bbox_corners)))

        return [
            [*min_corner], [*max_corner]
        ]



    def get_object_info(self, name):
        """Get detailed information about a specific object"""
        return self.scene_observation_service.get_object_info(name)

    def get_viewport_screenshot(self, max_size=800, filepath=None, format="png"):
        """
        Capture a screenshot of the current 3D viewport and save it to the specified path.

        Parameters:
        - max_size: Maximum size in pixels for the largest dimension of the image
        - filepath: Path where to save the screenshot file
        - format: Image format (png, jpg, etc.)

        Returns success/error status
        """
        return self.viewport_screenshot_service.get_viewport_screenshot(max_size, filepath, format)

    def get_scene_index(self, include_hidden=True, include_materials=True, include_modifiers=True, include_constraints=True, include_collections=True, max_objects=None):
        """Get a bounded, JSON-serializable index of the current scene."""
        return self.scene_intelligence_service.get_scene_index(include_hidden, include_materials, include_modifiers, include_constraints, include_collections, max_objects)

    def get_object_deep_info(self, object_name=None, name=None, include_mesh_stats=True, include_material_slots=True, include_modifiers=True, include_constraints=True, include_animation=True, include_custom_properties=True):
        """Get deep, bounded inspection data for a single object."""
        return self.scene_intelligence_service.get_object_deep_info(object_name, name, include_mesh_stats, include_material_slots, include_modifiers, include_constraints, include_animation, include_custom_properties)

    def get_selection_info(self):
        """Get active object and selection details without mutating selection."""
        return self.scene_intelligence_service.get_selection_info()

    def get_scene_health(self):
        """Get a non-destructive scene metrics and health summary."""
        return self.scene_intelligence_service.get_scene_health()

    def capture_viewport_pack(self, views=None, max_size=800, include_manifest=True, snapshot_name=None, artifact_root=None):
        """Capture a local multi-view screenshot pack under the generated artifact directory."""
        return self.verification_artifact_service.capture_viewport_pack(views, max_size, include_manifest, snapshot_name, artifact_root=artifact_root)

    def create_verification_snapshot(self, label=None, include_scene_index=True, include_scene_health=True, include_selection=True, include_screenshots=True, views=None, max_size=800, artifact_root=None):
        """Create a local verification snapshot manifest and requested artifacts."""
        return self.verification_artifact_service.create_verification_snapshot(label, include_scene_index, include_scene_health, include_selection, include_screenshots, views, max_size, artifact_root)

    def list_verification_snapshots(self):
        """List local verification snapshots generated by Phase 2 tools."""
        return self.verification_artifact_service.list_verification_snapshots()

    def get_supported_edit_operations(self):
        """List Phase 3 supported edit operations and safety metadata."""
        return self.scene_edit_service.get_supported_edit_operations()

    def create_primitive_object(self, primitive_type, name=None, location=None, rotation=None, scale=None, collection_name=None, material_name=None, verify=False, dimensions=None, anchor="center", origin_mode=None, snap_to=None, clearance=0.0):
        """Create a supported primitive object with explicit parameters."""
        return self.scene_edit_service.create_primitive_object(primitive_type, name, location, rotation, scale, collection_name, material_name, verify, dimensions, anchor, origin_mode, snap_to, clearance)

    def create_box(self, name=None, dimensions=None, location=None, anchor="bottom_center", collection_name=None, material_name=None, verify=False):
        """Create a box using final dimensions and anchor semantics."""
        return self.scene_edit_service.create_box(name, dimensions, location, anchor, collection_name, material_name, verify)

    def transform_object(self, object_name, location=None, rotation=None, scale=None, relative=False, verify=False, dimensions=None, anchor=None, preserve_anchor=True):
        """Transform one explicitly named object."""
        return self.scene_edit_service.transform_object(object_name, location, rotation, scale, relative, verify, dimensions, anchor, preserve_anchor)

    def transform_object_dimensions(self, object_name, dimensions, preserve_anchor=True, anchor="bottom_center", verify=False):
        """Resize an object to final dimensions while preserving an anchor."""
        return self.scene_edit_service.transform_object_dimensions(object_name, dimensions, preserve_anchor, anchor, verify)

    def duplicate_object(self, object_name, new_name=None, linked=False, location_offset=None, collection_name=None, verify=False):
        """Duplicate one explicitly named object."""
        return self.scene_edit_service.duplicate_object(object_name, new_name, linked, location_offset, collection_name, verify)

    def delete_objects(self, object_names, confirm=False, allow_missing=False, verify=False):
        """Delete only explicitly named objects after confirmation."""
        return self.scene_edit_service.delete_objects(object_names, confirm, allow_missing, verify)

    def clear_scene(self, scope="prefix", prefix="OVERTLI_", collection_name=None, delete_objects=True, delete_empty_collections=True, delete_unused_materials=True, delete_unused_images=False, delete_cameras_lights=False, dry_run=True, confirm=False, create_before_snapshot=True):
        """Plan or execute a bounded scene cleanup/reset."""
        return self.scene_edit_service.clear_scene(scope, prefix, collection_name, delete_objects, delete_empty_collections, delete_unused_materials, delete_unused_images, delete_cameras_lights, dry_run, confirm, create_before_snapshot)

    def scene_cleanup_plan(self, scope="prefix", prefix="OVERTLI_", collection_name=None, delete_objects=True, delete_empty_collections=True, delete_unused_materials=True, delete_unused_images=False, delete_cameras_lights=False, create_before_snapshot=True):
        """Return a dry-run cleanup plan."""
        return self.scene_edit_service.scene_cleanup_plan(scope=scope, prefix=prefix, collection_name=collection_name, delete_objects=delete_objects, delete_empty_collections=delete_empty_collections, delete_unused_materials=delete_unused_materials, delete_unused_images=delete_unused_images, delete_cameras_lights=delete_cameras_lights, create_before_snapshot=create_before_snapshot)

    def validate_ground_contact(self, object_names, ground_object, expected_relation="on_top", tolerance=0.01):
        """Validate that objects contact or clear a ground object."""
        return self.scene_edit_service.validate_ground_contact(object_names, ground_object, expected_relation, tolerance)

    def align_object_to_surface(self, object_name, target_object, target_face="top", anchor="bottom_center", clearance=0.0):
        """Move an object anchor to a target object surface."""
        return self.scene_edit_service.align_object_to_surface(object_name, target_object, target_face, anchor, clearance)

    def validate_scene_composition(self, generated_prefix="OVERTLI_", expected_collection=None, ground_object=None, tolerance=0.01, allow_below_ground=False):
        """Run structural composition checks for generated scene content."""
        return self.scene_edit_service.validate_scene_composition(generated_prefix, expected_collection, ground_object, tolerance, allow_below_ground)

    def set_object_visibility(self, object_name, hide_viewport=None, hide_render=None, verify=False):
        """Set viewport/render visibility on one explicitly named object."""
        return self.scene_edit_service.set_object_visibility(object_name, hide_viewport, hide_render, verify)

    def create_basic_material(self, name, base_color=None, metallic=None, roughness=None, alpha=None, use_nodes=True, replace_existing=False):
        """Create or update a basic material."""
        return self.material_authoring_service.create_basic_material(name, base_color, metallic, roughness, alpha, use_nodes, replace_existing)

    def assign_material(self, object_name, material_name, slot_index=None, replace=True, verify=False):
        """Assign an existing material to one explicitly named object."""
        return self.material_authoring_service.assign_material(object_name, material_name, slot_index, replace, verify)

    def update_material_properties(self, material_name, base_color=None, metallic=None, roughness=None, alpha=None, verify=False):
        """Update supported properties on an existing material."""
        return self.material_authoring_service.update_material_properties(material_name, base_color, metallic, roughness, alpha, verify)

    def get_timeline_info(self, include_markers=True, include_playback=True):
        return self.animation_intelligence_service.get_timeline_info(include_markers, include_playback)

    def list_animated_objects(self, include_material_animation=True, include_shape_key_animation=True, include_drivers=True, max_objects=None):
        return self.animation_intelligence_service.list_animated_objects(include_material_animation, include_shape_key_animation, include_drivers, max_objects)

    def get_animation_deep_info(self, object_name=None, material_name=None, include_keyframes=True, include_fcurves=True, include_drivers=True, max_keyframes=200):
        return self.animation_intelligence_service.get_animation_deep_info(object_name, material_name, include_keyframes, include_fcurves, include_drivers, max_keyframes)

    def set_timeline_range(self, frame_start, frame_end, fps=None, current_frame=None):
        return self.animation_intelligence_service.set_timeline_range(frame_start, frame_end, fps, current_frame)

    def set_current_frame(self, frame):
        return self.animation_intelligence_service.set_current_frame(frame)

    def insert_transform_keyframes(self, object_name, frames, properties=None):
        return self.animation_authoring_service.insert_transform_keyframes(object_name, frames, properties)

    def animate_object_transform(self, object_name, keyframes, interpolation="BEZIER", clear_existing=False, confirm_clear_existing=False, verify=False):
        return self.animation_authoring_service.animate_object_transform(object_name, keyframes, interpolation, clear_existing, confirm_clear_existing, verify)

    def animate_camera_transform(self, camera_name, keyframes, interpolation="BEZIER", clear_existing=False, confirm_clear_existing=False, verify=False):
        return self.animation_authoring_service.animate_camera_transform(camera_name, keyframes, interpolation, clear_existing, confirm_clear_existing, verify)

    def animate_light_property(self, light_name, property_name, keyframes, interpolation="BEZIER"):
        return self.animation_authoring_service.animate_light_property(light_name, property_name, keyframes, interpolation)

    def animate_material_property(self, material_name, channel, keyframes, interpolation="BEZIER"):
        return self.animation_authoring_service.animate_material_property(material_name, channel, keyframes, interpolation)

    def animate_shape_key_value(self, object_name, shape_key_name, keyframes, interpolation="BEZIER"):
        return self.animation_authoring_service.animate_shape_key_value(object_name, shape_key_name, keyframes, interpolation)

    def delete_animation_data(self, target_type, target_name, data_paths=None, confirm=False):
        return self.animation_authoring_service.delete_animation_data(target_type, target_name, data_paths, confirm)

    def create_camera(self, camera_name=None, location=None, rotation=None, lens=None, sensor_width=None, clip_start=None, clip_end=None, collection_name=None, set_active=False, verify=False):
        return self.camera_composition_service.create_camera(camera_name, location, rotation, lens, sensor_width, clip_start, clip_end, collection_name, set_active, verify)

    def frame_camera_to_objects(self, camera_name, object_names, view="front_perspective", margin=1.25, distance_multiplier=1.0, look_at=True, set_active=True, verify=False):
        return self.camera_composition_service.frame_camera_to_objects(camera_name, object_names, view, margin, distance_multiplier, look_at, set_active, verify)

    def set_active_camera(self, camera_name):
        return self.camera_composition_service.set_active_camera(camera_name)

    def create_light(self, light_name=None, light_type="AREA", location=None, rotation=None, energy=None, color=None, size=None, collection_name=None, verify=False):
        return self.lighting_setup_service.create_light(light_name, light_type, location, rotation, energy, color, size, collection_name, verify)

    def create_lighting_setup(self, setup_name, target_object_names=None, preset="three_point", collection_name=None, replace_existing_with_prefix=False, confirm_replace=False, verify=False):
        return self.lighting_setup_service.create_lighting_setup(setup_name, target_object_names, preset, collection_name, replace_existing_with_prefix, confirm_replace, verify)

    def update_light(self, light_name, energy=None, color=None, size=None, location=None, rotation=None, verify=False):
        return self.lighting_setup_service.update_light(light_name, energy, color, size, location, rotation, verify)

    def set_world_lighting(self, color=None, strength=None, verify=False):
        return self.lighting_setup_service.set_world_lighting(color, strength, verify)

    def get_render_settings(self):
        return self.render_settings_service.get_render_settings()

    def set_render_settings(self, engine=None, resolution_x=None, resolution_y=None, resolution_percentage=None, samples=None, image_format=None, transparent=None, color_management=None, clamp_for_smoke=False, auto_compatible=False):
        return self.render_settings_service.set_render_settings(engine, resolution_x, resolution_y, resolution_percentage, samples, image_format, transparent, color_management, clamp_for_smoke, auto_compatible)

    def get_supported_color_management(self):
        return self.render_settings_service.get_supported_color_management()

    def set_output_path(self, output_path=None, artifact_root=None, subdir="renders/stills", filename=None):
        return self.render_settings_service.set_output_path(output_path, artifact_root, subdir, filename)

    def render_still(self, output_path=None, artifact_root=None, filename=None, camera_name=None, frame=None, clamp_for_smoke=True, write_manifest=True):
        return self.render_artifact_service.render_still(output_path, artifact_root, filename, camera_name, frame, clamp_for_smoke, write_manifest)

    def render_contact_sheet(self, object_names=None, camera_name=None, views=None, artifact_root=None, filename=None, clamp_for_smoke=True):
        return self.render_artifact_service.render_contact_sheet(object_names, camera_name, views, artifact_root, filename, clamp_for_smoke)

    def create_turntable_animation(self, object_name, frame_start=1, frame_end=48, axis="Z", rotations=1.0, empty_name=None, camera_name=None, confirm_clear_existing=False):
        return self.render_artifact_service.create_turntable_animation(object_name, frame_start, frame_end, axis, rotations, empty_name, camera_name, confirm_clear_existing)

    def render_preview_animation(self, output_dir=None, artifact_root=None, frame_start=None, frame_end=None, step=1, max_frames=24, camera_name=None, clamp_for_smoke=True):
        return self.render_artifact_service.render_preview_animation(output_dir, artifact_root, frame_start, frame_end, step, max_frames, camera_name, clamp_for_smoke)

    def get_compositor_status(self):
        return self.compositor_pass_service.get_compositor_status()

    def set_compositor_preset(self, preset="basic_viewer", confirm_replace=False):
        return self.compositor_pass_service.set_compositor_preset(preset, confirm_replace)

    def set_render_passes(self, use_pass_z=None, use_pass_mist=None, use_pass_normal=None, use_pass_diffuse_color=None):
        return self.compositor_pass_service.set_render_passes(use_pass_z, use_pass_mist, use_pass_normal, use_pass_diffuse_color)

    def run_presentation_workflow_batch(self, label=None, operations=None, create_before_snapshot=True, create_after_snapshot=True, stop_on_error=True, max_operations=20, batch_allow_destructive=False, artifact_root=None):
        return self.presentation_workflow_batch_service.run_presentation_workflow_batch(label, operations, create_before_snapshot, create_after_snapshot, stop_on_error, max_operations, batch_allow_destructive, artifact_root)

    def cleanup_presentation_artifacts(self, prefix, confirm=False, cleanup_scene_data=True, cleanup_render_artifacts=False, artifact_root=None):
        return self.presentation_workflow_batch_service.cleanup_presentation_artifacts(prefix, confirm, cleanup_scene_data, cleanup_render_artifacts, artifact_root)

    def add_object_modifier(self, object_name, modifier_type, name=None, properties=None, verify=False):
        """Add an allowlisted modifier to one explicitly named object."""
        return self.modifier_service.add_object_modifier(object_name, modifier_type, name, properties, verify)

    def update_object_modifier(self, object_name, modifier_name, properties, verify=False):
        """Update allowlisted properties on an existing modifier."""
        return self.modifier_service.update_object_modifier(object_name, modifier_name, properties, verify)

    def remove_object_modifier(self, object_name, modifier_name, confirm=False, verify=False):
        """Remove one named modifier after confirmation."""
        return self.modifier_service.remove_object_modifier(object_name, modifier_name, confirm, verify)

    def create_collection(self, collection_name, parent_collection_name=None, replace_existing=False):
        """Create a collection without deleting existing collections."""
        return self.collection_organization_service.create_collection(collection_name, parent_collection_name, replace_existing)

    def move_objects_to_collection(self, object_names, collection_name, unlink_from_other_collections=False, create_collection=False):
        """Move or link explicitly named objects to an existing collection."""
        return self.collection_organization_service.move_objects_to_collection(object_names, collection_name, unlink_from_other_collections, create_collection)

    def delete_collection(self, collection_name, confirm=False, require_empty=True):
        """Delete one explicitly named collection after confirmation; empty-only by default."""
        return self.collection_organization_service.delete_collection(collection_name, confirm, require_empty)

    def run_verified_edit_batch(self, label=None, operations=None, create_before_snapshot=True, create_after_snapshot=True, stop_on_error=True, max_operations=20, batch_allow_destructive=False, artifact_root=None, prevalidate_only=False, prevalidate_all=True):
        """Run a controlled allowlisted edit batch with before/after verification."""
        return self.verified_edit_batch_service.run_verified_edit_batch(label, operations, create_before_snapshot, create_after_snapshot, stop_on_error, max_operations, batch_allow_destructive, artifact_root, prevalidate_only, prevalidate_all)

    def get_task_workspace(self, artifact_root=None):
        """Get the persistent Phase 3 task workspace summary."""
        return self.workspace_safety_diff_service.get_task_workspace(artifact_root)

    def create_workspace_task(self, title, goal=None, assumptions=None, status="pending", task_id=None, artifact_root=None):
        """Create a persistent task workspace entry."""
        return self.workspace_safety_diff_service.create_workspace_task(title, goal, assumptions, status, task_id, artifact_root)

    def update_workspace_task(self, task_id, status=None, goal=None, assumptions=None, rollback_status=None, verification=None, artifact_root=None):
        """Update a persistent task workspace entry."""
        return self.workspace_safety_diff_service.update_workspace_task(task_id, status, goal, assumptions, rollback_status, verification, artifact_root)

    def complete_workspace_task(self, task_id, verified=False, evidence=None, artifact_root=None):
        """Complete a persistent task workspace entry."""
        return self.workspace_safety_diff_service.complete_workspace_task(task_id, verified, evidence, artifact_root)

    def create_scene_plan(self, title="Scene build plan", goal=None, steps=None, artifact_root=None):
        """Create a scene build task and todo checklist."""
        return self.workspace_safety_diff_service.create_scene_plan(title, goal, steps, artifact_root)

    def list_scene_plan(self, task_id=None, artifact_root=None):
        """List scene build task and todo checklist state."""
        return self.workspace_safety_diff_service.list_scene_plan(task_id, artifact_root)

    def list_workspace_tasks(self, status=None, artifact_root=None):
        """List persistent task workspace entries."""
        return self.workspace_safety_diff_service.list_workspace_tasks(status, artifact_root)

    def add_workspace_todo(self, text, task_id=None, state="pending", todo_id=None, artifact_root=None):
        """Add a persistent todo entry."""
        return self.workspace_safety_diff_service.add_workspace_todo(text, task_id, state, todo_id, artifact_root)

    def update_workspace_todo(self, todo_id, state=None, text=None, evidence=None, artifact_root=None):
        """Update a persistent todo entry."""
        return self.workspace_safety_diff_service.update_workspace_todo(todo_id, state, text, evidence, artifact_root)

    def list_workspace_todos(self, task_id=None, state=None, artifact_root=None):
        """List persistent todo entries."""
        return self.workspace_safety_diff_service.list_workspace_todos(task_id, state, artifact_root)

    def record_operation_journal_entry(self, operation_type, task_id=None, target=None, summary=None, risk_level="LOW", rollback_status="unknown", before_snapshot_id=None, after_snapshot_id=None, metadata=None, artifact_root=None):
        """Record a durable operation journal entry."""
        return self.workspace_safety_diff_service.record_operation_journal_entry(operation_type, task_id, target, summary, risk_level, rollback_status, before_snapshot_id, after_snapshot_id, metadata, artifact_root)

    def get_operation_journal(self, task_id=None, limit=50, artifact_root=None):
        """Read durable operation journal entries."""
        return self.workspace_safety_diff_service.get_operation_journal(task_id, limit, artifact_root)

    def create_scene_snapshot(self, label=None, task_id=None, include_verification_snapshot=False, artifact_root=None):
        """Create a lightweight durable scene state snapshot."""
        return self.workspace_safety_diff_service.create_scene_snapshot(label, task_id, include_verification_snapshot, artifact_root)

    def list_scene_snapshots(self, artifact_root=None):
        """List durable scene state snapshots."""
        return self.workspace_safety_diff_service.list_scene_snapshots(artifact_root)

    def diff_scene_snapshots(self, before_snapshot_id, after_snapshot_id, artifact_root=None):
        """Diff two durable scene state snapshots."""
        return self.workspace_safety_diff_service.diff_scene_snapshots(before_snapshot_id, after_snapshot_id, artifact_root)

    def detect_user_changes(self, baseline_snapshot_id=None, artifact_root=None):
        """Detect scene changes relative to a baseline snapshot."""
        return self.workspace_safety_diff_service.detect_user_changes(baseline_snapshot_id, artifact_root)

    def rollback_to_scene_snapshot(self, snapshot_id, confirm=False, remove_new_objects=False, verify=True, artifact_root=None):
        """Rollback existing object transforms and visibility to a scene snapshot."""
        return self.workspace_safety_diff_service.rollback_to_scene_snapshot(snapshot_id, confirm, remove_new_objects, verify, artifact_root)

    def undo_last_blender_operation(self, confirm=False):
        """Request Blender undo after explicit confirmation."""
        return self.workspace_safety_diff_service.undo_last_blender_operation(confirm)

    def get_safety_status(self):
        """Get the current safety policy status."""
        return self.safety_policy_service.get_safety_status()

    def execute_code(self, code):
        """Execute arbitrary Blender Python code with shared context"""
        return self.raw_code_execution_service.execute_code(code)

    def _store_object_handle(self, handle, obj_name):
        """Store object reference by handle"""
        return self.shared_context_service.store_object_handle(handle, obj_name)

    def _store_material_handle(self, handle, mat_name):
        """Store material reference by handle"""
        return self.shared_context_service.store_material_handle(handle, mat_name)

    def _store_operation_result(self, op_id, result):
        """Store operation result by ID"""
        return self.shared_context_service.store_operation_result(op_id, result)

    def _add_to_history(self, operation, input_data, result):
        """Add operation to history"""
        self.shared_context_service.add_to_history(operation, input_data, result)

    def get_shared_context(self):
        """Get current shared context state"""
        return self.shared_context_service.get_shared_context()

    def clear_shared_context(self, section="all"):
        """Clear shared context (all, variables, objects, materials, operations, history)"""
        return self.shared_context_service.clear_shared_context(section)

    def get_operation_history(self, count=10):
        """Get recent operation history"""
        return self.shared_context_service.get_operation_history(count)

    def create_object_handle(self, handle, object_name):
        """Create a handle for an object to reference in future operations"""
        return self.shared_context_service.create_object_handle(handle, object_name)

    def create_material_handle(self, handle, material_name):
        """Create a handle for a material to reference in future operations"""
        return self.shared_context_service.create_material_handle(handle, material_name)

    def list_object_handles(self):
        """List all object handles and their details"""
        return self.shared_context_service.list_object_handles()

    def list_material_handles(self):
        """List all material handles and their details"""
        return self.shared_context_service.list_material_handles()

    def get_polyhaven_categories(self, asset_type):
        """Get categories for a specific asset type from Polyhaven"""
        try:
            if asset_type not in ["hdris", "textures", "models", "all"]:
                return {"error": f"Invalid asset type: {asset_type}. Must be one of: hdris, textures, models, all"}

            response = requests.get(f"https://api.polyhaven.com/categories/{asset_type}", headers=REQ_HEADERS)
            if response.status_code == 200:
                return {"categories": response.json()}
            else:
                return {"error": f"API request failed with status code {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    def search_polyhaven_assets(self, asset_type=None, categories=None):
        """Search for assets from Polyhaven with optional filtering"""
        try:
            url = "https://api.polyhaven.com/assets"
            params = {}

            if asset_type and asset_type != "all":
                if asset_type not in ["hdris", "textures", "models"]:
                    return {"error": f"Invalid asset type: {asset_type}. Must be one of: hdris, textures, models, all"}
                params["type"] = asset_type

            if categories:
                params["categories"] = categories

            response = requests.get(url, params=params, headers=REQ_HEADERS)
            if response.status_code == 200:
                # Limit the response size to avoid overwhelming Blender
                assets = response.json()
                # Return only the first 20 assets to keep response size manageable
                limited_assets = {}
                for i, (key, value) in enumerate(assets.items()):
                    if i >= 20:  # Limit to 20 assets
                        break
                    limited_assets[key] = value

                return {"assets": limited_assets, "total_count": len(assets), "returned_count": len(limited_assets)}
            else:
                return {"error": f"API request failed with status code {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    def download_polyhaven_asset(self, asset_id, asset_type, resolution="1k", file_format=None):
        try:
            # First get the files information
            files_response = requests.get(f"https://api.polyhaven.com/files/{asset_id}", headers=REQ_HEADERS)
            if files_response.status_code != 200:
                return {"error": f"Failed to get asset files: {files_response.status_code}"}

            files_data = files_response.json()

            # Handle different asset types
            if asset_type == "hdris":
                # For HDRIs, download the .hdr or .exr file
                if not file_format:
                    file_format = "hdr"  # Default format for HDRIs

                if "hdri" in files_data and resolution in files_data["hdri"] and file_format in files_data["hdri"][resolution]:
                    file_info = files_data["hdri"][resolution][file_format]
                    file_url = file_info["url"]

                    # For HDRIs, we need to save to a temporary file first
                    # since Blender can't properly load HDR data directly from memory
                    with tempfile.NamedTemporaryFile(suffix=f".{file_format}", delete=False) as tmp_file:
                        # Download the file
                        response = requests.get(file_url, headers=REQ_HEADERS)
                        if response.status_code != 200:
                            return {"error": f"Failed to download HDRI: {response.status_code}"}

                        tmp_file.write(response.content)
                        tmp_path = tmp_file.name

                    try:
                        # Create a new world if none exists
                        if not bpy.data.worlds:
                            bpy.data.worlds.new("World")

                        world = bpy.data.worlds[0]
                        world.use_nodes = True
                        node_tree = world.node_tree

                        # Clear existing nodes
                        for node in node_tree.nodes:
                            node_tree.nodes.remove(node)

                        # Create nodes
                        tex_coord = node_tree.nodes.new(type='ShaderNodeTexCoord')
                        tex_coord.location = (-800, 0)

                        mapping = node_tree.nodes.new(type='ShaderNodeMapping')
                        mapping.location = (-600, 0)

                        # Load the image from the temporary file
                        env_tex = node_tree.nodes.new(type='ShaderNodeTexEnvironment')
                        env_tex.location = (-400, 0)
                        env_tex.image = bpy.data.images.load(tmp_path)

                        # Use a color space that exists in all Blender versions
                        if file_format.lower() == 'exr':
                            # Try to use Linear color space for EXR files
                            try:
                                env_tex.image.colorspace_settings.name = 'Linear'
                            except:
                                # Fallback to Non-Color if Linear isn't available
                                env_tex.image.colorspace_settings.name = 'Non-Color'
                        else:  # hdr
                            # For HDR files, try these options in order
                            for color_space in ['Linear', 'Linear Rec.709', 'Non-Color']:
                                try:
                                    env_tex.image.colorspace_settings.name = color_space
                                    break  # Stop if we successfully set a color space
                                except:
                                    continue

                        background = node_tree.nodes.new(type='ShaderNodeBackground')
                        background.location = (-200, 0)

                        output = node_tree.nodes.new(type='ShaderNodeOutputWorld')
                        output.location = (0, 0)

                        # Connect nodes
                        node_tree.links.new(tex_coord.outputs['Generated'], mapping.inputs['Vector'])
                        node_tree.links.new(mapping.outputs['Vector'], env_tex.inputs['Vector'])
                        node_tree.links.new(env_tex.outputs['Color'], background.inputs['Color'])
                        node_tree.links.new(background.outputs['Background'], output.inputs['Surface'])

                        # Set as active world
                        bpy.context.scene.world = world

                        # Clean up temporary file
                        try:
                            tempfile._cleanup()  # This will clean up all temporary files
                        except:
                            pass

                        return {
                            "success": True,
                            "message": f"HDRI {asset_id} imported successfully",
                            "image_name": env_tex.image.name
                        }
                    except Exception as e:
                        return {"error": f"Failed to set up HDRI in Blender: {str(e)}"}
                else:
                    return {"error": f"Requested resolution or format not available for this HDRI"}

            elif asset_type == "textures":
                if not file_format:
                    file_format = "jpg"  # Default format for textures

                downloaded_maps = {}

                try:
                    for map_type in files_data:
                        if map_type not in ["blend", "gltf"]:  # Skip non-texture files
                            if resolution in files_data[map_type] and file_format in files_data[map_type][resolution]:
                                file_info = files_data[map_type][resolution][file_format]
                                file_url = file_info["url"]

                                # Use NamedTemporaryFile like we do for HDRIs
                                with tempfile.NamedTemporaryFile(suffix=f".{file_format}", delete=False) as tmp_file:
                                    # Download the file
                                    response = requests.get(file_url, headers=REQ_HEADERS)
                                    if response.status_code == 200:
                                        tmp_file.write(response.content)
                                        tmp_path = tmp_file.name

                                        # Load image from temporary file
                                        image = bpy.data.images.load(tmp_path)
                                        image.name = f"{asset_id}_{map_type}.{file_format}"

                                        # Pack the image into .blend file
                                        image.pack()

                                        # Set color space based on map type
                                        if map_type in ['color', 'diffuse', 'albedo']:
                                            try:
                                                image.colorspace_settings.name = 'sRGB'
                                            except:
                                                pass
                                        else:
                                            try:
                                                image.colorspace_settings.name = 'Non-Color'
                                            except:
                                                pass

                                        downloaded_maps[map_type] = image

                                        # Clean up temporary file
                                        try:
                                            os.unlink(tmp_path)
                                        except:
                                            pass

                    if not downloaded_maps:
                        return {"error": f"No texture maps found for the requested resolution and format"}

                    # Create a new material with the downloaded textures
                    mat = bpy.data.materials.new(name=asset_id)
                    mat.use_nodes = True
                    nodes = mat.node_tree.nodes
                    links = mat.node_tree.links

                    # Clear default nodes
                    for node in nodes:
                        nodes.remove(node)

                    # Create output node
                    output = nodes.new(type='ShaderNodeOutputMaterial')
                    output.location = (300, 0)

                    # Create principled BSDF node
                    principled = nodes.new(type='ShaderNodeBsdfPrincipled')
                    principled.location = (0, 0)
                    links.new(principled.outputs[0], output.inputs[0])

                    # Add texture nodes based on available maps
                    tex_coord = nodes.new(type='ShaderNodeTexCoord')
                    tex_coord.location = (-800, 0)

                    mapping = nodes.new(type='ShaderNodeMapping')
                    mapping.location = (-600, 0)
                    mapping.vector_type = 'TEXTURE'  # Changed from default 'POINT' to 'TEXTURE'
                    links.new(tex_coord.outputs['UV'], mapping.inputs['Vector'])

                    # Position offset for texture nodes
                    x_pos = -400
                    y_pos = 300

                    # Connect different texture maps
                    for map_type, image in downloaded_maps.items():
                        tex_node = nodes.new(type='ShaderNodeTexImage')
                        tex_node.location = (x_pos, y_pos)
                        tex_node.image = image

                        # Set color space based on map type
                        if map_type.lower() in ['color', 'diffuse', 'albedo']:
                            try:
                                tex_node.image.colorspace_settings.name = 'sRGB'
                            except:
                                pass  # Use default if sRGB not available
                        else:
                            try:
                                tex_node.image.colorspace_settings.name = 'Non-Color'
                            except:
                                pass  # Use default if Non-Color not available

                        links.new(mapping.outputs['Vector'], tex_node.inputs['Vector'])

                        # Connect to appropriate input on Principled BSDF
                        if map_type.lower() in ['color', 'diffuse', 'albedo']:
                            links.new(tex_node.outputs['Color'], principled.inputs['Base Color'])
                        elif map_type.lower() in ['roughness', 'rough']:
                            links.new(tex_node.outputs['Color'], principled.inputs['Roughness'])
                        elif map_type.lower() in ['metallic', 'metalness', 'metal']:
                            links.new(tex_node.outputs['Color'], principled.inputs['Metallic'])
                        elif map_type.lower() in ['normal', 'nor']:
                            # Add normal map node
                            normal_map = nodes.new(type='ShaderNodeNormalMap')
                            normal_map.location = (x_pos + 200, y_pos)
                            links.new(tex_node.outputs['Color'], normal_map.inputs['Color'])
                            links.new(normal_map.outputs['Normal'], principled.inputs['Normal'])
                        elif map_type in ['displacement', 'disp', 'height']:
                            # Add displacement node
                            disp_node = nodes.new(type='ShaderNodeDisplacement')
                            disp_node.location = (x_pos + 200, y_pos - 200)
                            links.new(tex_node.outputs['Color'], disp_node.inputs['Height'])
                            links.new(disp_node.outputs['Displacement'], output.inputs['Displacement'])

                        y_pos -= 250

                    # Auto-create material handle for easy chaining
                    material_handle = f"material_{asset_id}"
                    self.shared_context['materials'][material_handle] = mat

                    self._add_to_history("download_polyhaven_asset", f"texture {asset_id}", f"Created material {mat.name}")

                    return {
                        "success": True,
                        "message": f"Texture {asset_id} imported as material",
                        "material": mat.name,
                        "material_handle": material_handle,  # New: handle for chaining
                        "maps": list(downloaded_maps.keys())
                    }

                except Exception as e:
                    return {"error": f"Failed to process textures: {str(e)}"}

            elif asset_type == "models":
                # For models, prefer glTF format if available
                if not file_format:
                    file_format = "gltf"  # Default format for models

                if file_format in files_data and resolution in files_data[file_format]:
                    file_info = files_data[file_format][resolution][file_format]
                    file_url = file_info["url"]

                    # Create a temporary directory to store the model and its dependencies
                    temp_dir = tempfile.mkdtemp()
                    main_file_path = ""

                    try:
                        # Download the main model file
                        main_file_name = file_url.split("/")[-1]
                        main_file_path = os.path.join(temp_dir, main_file_name)

                        response = requests.get(file_url, headers=REQ_HEADERS)
                        if response.status_code != 200:
                            return {"error": f"Failed to download model: {response.status_code}"}

                        with open(main_file_path, "wb") as f:
                            f.write(response.content)

                        # Check for included files and download them
                        if "include" in file_info and file_info["include"]:
                            for include_path, include_info in file_info["include"].items():
                                # Get the URL for the included file - this is the fix
                                include_url = include_info["url"]

                                # Create the directory structure for the included file
                                include_file_path = os.path.join(temp_dir, include_path)
                                os.makedirs(os.path.dirname(include_file_path), exist_ok=True)

                                # Download the included file
                                include_response = requests.get(include_url, headers=REQ_HEADERS)
                                if include_response.status_code == 200:
                                    with open(include_file_path, "wb") as f:
                                        f.write(include_response.content)
                                else:
                                    print(f"Failed to download included file: {include_path}")

                        # Import the model into Blender
                        if file_format == "gltf" or file_format == "glb":
                            bpy.ops.import_scene.gltf(filepath=main_file_path)
                        elif file_format == "fbx":
                            bpy.ops.import_scene.fbx(filepath=main_file_path)
                        elif file_format == "obj":
                            bpy.ops.import_scene.obj(filepath=main_file_path)
                        elif file_format == "blend":
                            # For blend files, we need to append or link
                            with bpy.data.libraries.load(main_file_path, link=False) as (data_from, data_to):
                                data_to.objects = data_from.objects

                            # Link the objects to the scene
                            for obj in data_to.objects:
                                if obj is not None:
                                    bpy.context.collection.objects.link(obj)
                        else:
                            return {"error": f"Unsupported model format: {file_format}"}

                        # Get the names of imported objects
                        imported_objects = [obj.name for obj in bpy.context.selected_objects]

                        # Auto-create handles for imported objects for easy chaining
                        object_handles = {}
                        for i, obj_name in enumerate(imported_objects):
                            handle = f"imported_{asset_id}_{i}"
                            self.shared_context['objects'][handle] = bpy.data.objects[obj_name]
                            object_handles[handle] = obj_name

                        self._add_to_history("download_polyhaven_asset", f"model {asset_id}", f"Imported {len(imported_objects)} objects")

                        return {
                            "success": True,
                            "message": f"Model {asset_id} imported successfully",
                            "imported_objects": imported_objects,
                            "object_handles": object_handles  # New: handles for chaining
                        }
                    except Exception as e:
                        return {"error": f"Failed to import model: {str(e)}"}
                    finally:
                        # Clean up temporary directory
                        with suppress(Exception):
                            shutil.rmtree(temp_dir)
                else:
                    return {"error": f"Requested format or resolution not available for this model"}

            else:
                return {"error": f"Unsupported asset type: {asset_type}"}

        except Exception as e:
            return {"error": f"Failed to download asset: {str(e)}"}

    def set_texture(self, object_name, texture_id):
        """Apply a previously downloaded Polyhaven texture to an object by creating a new material"""
        try:
            # Get the object
            obj = bpy.data.objects.get(object_name)
            if not obj:
                return {"error": f"Object not found: {object_name}"}

            # Make sure object can accept materials
            if not hasattr(obj, 'data') or not hasattr(obj.data, 'materials'):
                return {"error": f"Object {object_name} cannot accept materials"}

            # Find all images related to this texture and ensure they're properly loaded
            texture_images = {}
            for img in bpy.data.images:
                if img.name.startswith(texture_id + "_"):
                    # Extract the map type from the image name
                    map_type = img.name.split('_')[-1].split('.')[0]

                    # Force a reload of the image
                    img.reload()

                    # Ensure proper color space
                    if map_type.lower() in ['color', 'diffuse', 'albedo']:
                        try:
                            img.colorspace_settings.name = 'sRGB'
                        except:
                            pass
                    else:
                        try:
                            img.colorspace_settings.name = 'Non-Color'
                        except:
                            pass

                    # Ensure the image is packed
                    if not img.packed_file:
                        img.pack()

                    texture_images[map_type] = img
                    print(f"Loaded texture map: {map_type} - {img.name}")

                    # Debug info
                    print(f"Image size: {img.size[0]}x{img.size[1]}")
                    print(f"Color space: {img.colorspace_settings.name}")
                    print(f"File format: {img.file_format}")
                    print(f"Is packed: {bool(img.packed_file)}")

            if not texture_images:
                return {"error": f"No texture images found for: {texture_id}. Please download the texture first."}

            # Create a new material
            new_mat_name = f"{texture_id}_material_{object_name}"

            # Remove any existing material with this name to avoid conflicts
            existing_mat = bpy.data.materials.get(new_mat_name)
            if existing_mat:
                bpy.data.materials.remove(existing_mat)

            new_mat = bpy.data.materials.new(name=new_mat_name)
            new_mat.use_nodes = True

            # Set up the material nodes
            nodes = new_mat.node_tree.nodes
            links = new_mat.node_tree.links

            # Clear default nodes
            nodes.clear()

            # Create output node
            output = nodes.new(type='ShaderNodeOutputMaterial')
            output.location = (600, 0)

            # Create principled BSDF node
            principled = nodes.new(type='ShaderNodeBsdfPrincipled')
            principled.location = (300, 0)
            links.new(principled.outputs[0], output.inputs[0])

            # Add texture nodes based on available maps
            tex_coord = nodes.new(type='ShaderNodeTexCoord')
            tex_coord.location = (-800, 0)

            mapping = nodes.new(type='ShaderNodeMapping')
            mapping.location = (-600, 0)
            mapping.vector_type = 'TEXTURE'  # Changed from default 'POINT' to 'TEXTURE'
            links.new(tex_coord.outputs['UV'], mapping.inputs['Vector'])

            # Position offset for texture nodes
            x_pos = -400
            y_pos = 300

            # Connect different texture maps
            for map_type, image in texture_images.items():
                tex_node = nodes.new(type='ShaderNodeTexImage')
                tex_node.location = (x_pos, y_pos)
                tex_node.image = image

                # Set color space based on map type
                if map_type.lower() in ['color', 'diffuse', 'albedo']:
                    try:
                        tex_node.image.colorspace_settings.name = 'sRGB'
                    except:
                        pass  # Use default if sRGB not available
                else:
                    try:
                        tex_node.image.colorspace_settings.name = 'Non-Color'
                    except:
                        pass  # Use default if Non-Color not available

                links.new(mapping.outputs['Vector'], tex_node.inputs['Vector'])

                # Connect to appropriate input on Principled BSDF
                if map_type.lower() in ['color', 'diffuse', 'albedo']:
                    links.new(tex_node.outputs['Color'], principled.inputs['Base Color'])
                elif map_type.lower() in ['roughness', 'rough']:
                    links.new(tex_node.outputs['Color'], principled.inputs['Roughness'])
                elif map_type.lower() in ['metallic', 'metalness', 'metal']:
                    links.new(tex_node.outputs['Color'], principled.inputs['Metallic'])
                elif map_type.lower() in ['normal', 'nor', 'dx', 'gl']:
                    # Add normal map node
                    normal_map = nodes.new(type='ShaderNodeNormalMap')
                    normal_map.location = (x_pos + 200, y_pos)
                    links.new(tex_node.outputs['Color'], normal_map.inputs['Color'])
                    links.new(normal_map.outputs['Normal'], principled.inputs['Normal'])
                elif map_type.lower() in ['displacement', 'disp', 'height']:
                    # Add displacement node
                    disp_node = nodes.new(type='ShaderNodeDisplacement')
                    disp_node.location = (x_pos + 200, y_pos - 200)
                    disp_node.inputs['Scale'].default_value = 0.1  # Reduce displacement strength
                    links.new(tex_node.outputs['Color'], disp_node.inputs['Height'])
                    links.new(disp_node.outputs['Displacement'], output.inputs['Displacement'])

                y_pos -= 250

            # Second pass: Connect nodes with proper handling for special cases
            texture_nodes = {}

            # First find all texture nodes and store them by map type
            for node in nodes:
                if node.type == 'TEX_IMAGE' and node.image:
                    for map_type, image in texture_images.items():
                        if node.image == image:
                            texture_nodes[map_type] = node
                            break

            # Now connect everything using the nodes instead of images
            # Handle base color (diffuse)
            for map_name in ['color', 'diffuse', 'albedo']:
                if map_name in texture_nodes:
                    links.new(texture_nodes[map_name].outputs['Color'], principled.inputs['Base Color'])
                    print(f"Connected {map_name} to Base Color")
                    break

            # Handle roughness
            for map_name in ['roughness', 'rough']:
                if map_name in texture_nodes:
                    links.new(texture_nodes[map_name].outputs['Color'], principled.inputs['Roughness'])
                    print(f"Connected {map_name} to Roughness")
                    break

            # Handle metallic
            for map_name in ['metallic', 'metalness', 'metal']:
                if map_name in texture_nodes:
                    links.new(texture_nodes[map_name].outputs['Color'], principled.inputs['Metallic'])
                    print(f"Connected {map_name} to Metallic")
                    break

            # Handle normal maps
            for map_name in ['gl', 'dx', 'nor']:
                if map_name in texture_nodes:
                    normal_map_node = nodes.new(type='ShaderNodeNormalMap')
                    normal_map_node.location = (100, 100)
                    links.new(texture_nodes[map_name].outputs['Color'], normal_map_node.inputs['Color'])
                    links.new(normal_map_node.outputs['Normal'], principled.inputs['Normal'])
                    print(f"Connected {map_name} to Normal")
                    break

            # Handle displacement
            for map_name in ['displacement', 'disp', 'height']:
                if map_name in texture_nodes:
                    disp_node = nodes.new(type='ShaderNodeDisplacement')
                    disp_node.location = (300, -200)
                    disp_node.inputs['Scale'].default_value = 0.1  # Reduce displacement strength
                    links.new(texture_nodes[map_name].outputs['Color'], disp_node.inputs['Height'])
                    links.new(disp_node.outputs['Displacement'], output.inputs['Displacement'])
                    print(f"Connected {map_name} to Displacement")
                    break

            # Handle ARM texture (Ambient Occlusion, Roughness, Metallic)
            if 'arm' in texture_nodes:
                separate_rgb = nodes.new(type='ShaderNodeSeparateRGB')
                separate_rgb.location = (-200, -100)
                links.new(texture_nodes['arm'].outputs['Color'], separate_rgb.inputs['Image'])

                # Connect Roughness (G) if no dedicated roughness map
                if not any(map_name in texture_nodes for map_name in ['roughness', 'rough']):
                    links.new(separate_rgb.outputs['G'], principled.inputs['Roughness'])
                    print("Connected ARM.G to Roughness")

                # Connect Metallic (B) if no dedicated metallic map
                if not any(map_name in texture_nodes for map_name in ['metallic', 'metalness', 'metal']):
                    links.new(separate_rgb.outputs['B'], principled.inputs['Metallic'])
                    print("Connected ARM.B to Metallic")

                # For AO (R channel), multiply with base color if we have one
                base_color_node = None
                for map_name in ['color', 'diffuse', 'albedo']:
                    if map_name in texture_nodes:
                        base_color_node = texture_nodes[map_name]
                        break

                if base_color_node:
                    mix_node = nodes.new(type='ShaderNodeMixRGB')
                    mix_node.location = (100, 200)
                    mix_node.blend_type = 'MULTIPLY'
                    mix_node.inputs['Fac'].default_value = 0.8  # 80% influence

                    # Disconnect direct connection to base color
                    for link in base_color_node.outputs['Color'].links:
                        if link.to_socket == principled.inputs['Base Color']:
                            links.remove(link)

                    # Connect through the mix node
                    links.new(base_color_node.outputs['Color'], mix_node.inputs[1])
                    links.new(separate_rgb.outputs['R'], mix_node.inputs[2])
                    links.new(mix_node.outputs['Color'], principled.inputs['Base Color'])
                    print("Connected ARM.R to AO mix with Base Color")

            # Handle AO (Ambient Occlusion) if separate
            if 'ao' in texture_nodes:
                base_color_node = None
                for map_name in ['color', 'diffuse', 'albedo']:
                    if map_name in texture_nodes:
                        base_color_node = texture_nodes[map_name]
                        break

                if base_color_node:
                    mix_node = nodes.new(type='ShaderNodeMixRGB')
                    mix_node.location = (100, 200)
                    mix_node.blend_type = 'MULTIPLY'
                    mix_node.inputs['Fac'].default_value = 0.8  # 80% influence

                    # Disconnect direct connection to base color
                    for link in base_color_node.outputs['Color'].links:
                        if link.to_socket == principled.inputs['Base Color']:
                            links.remove(link)

                    # Connect through the mix node
                    links.new(base_color_node.outputs['Color'], mix_node.inputs[1])
                    links.new(texture_nodes['ao'].outputs['Color'], mix_node.inputs[2])
                    links.new(mix_node.outputs['Color'], principled.inputs['Base Color'])
                    print("Connected AO to mix with Base Color")

            # CRITICAL: Make sure to clear all existing materials from the object
            while len(obj.data.materials) > 0:
                obj.data.materials.pop(index=0)

            # Assign the new material to the object
            obj.data.materials.append(new_mat)

            # CRITICAL: Make the object active and select it
            bpy.context.view_layer.objects.active = obj
            obj.select_set(True)

            # CRITICAL: Force Blender to update the material
            bpy.context.view_layer.update()

            # Get the list of texture maps
            texture_maps = list(texture_images.keys())

            # Get info about texture nodes for debugging
            material_info = {
                "name": new_mat.name,
                "has_nodes": new_mat.use_nodes,
                "node_count": len(new_mat.node_tree.nodes),
                "texture_nodes": []
            }

            for node in new_mat.node_tree.nodes:
                if node.type == 'TEX_IMAGE' and node.image:
                    connections = []
                    for output in node.outputs:
                        for link in output.links:
                            connections.append(f"{output.name} → {link.to_node.name}.{link.to_socket.name}")

                    material_info["texture_nodes"].append({
                        "name": node.name,
                        "image": node.image.name,
                        "colorspace": node.image.colorspace_settings.name,
                        "connections": connections
                    })

            return {
                "success": True,
                "message": f"Created new material and applied texture {texture_id} to {object_name}",
                "material": new_mat.name,
                "maps": texture_maps,
                "material_info": material_info
            }

        except Exception as e:
            print(f"Error in set_texture: {str(e)}")
            traceback.print_exc()
            return {"error": f"Failed to apply texture: {str(e)}"}

    def get_polyhaven_status(self):
        """Get the current status of PolyHaven integration"""
        enabled = bpy.context.scene.blendermcp_use_polyhaven
        if enabled:
            return {"enabled": True, "message": "PolyHaven integration is enabled and ready to use."}
        else:
            return {
                "enabled": False,
                "message": """PolyHaven integration is currently disabled. To enable it:
                            1. In the 3D Viewport, find the Overtli-Blender panel in the sidebar (press N if hidden)
                            2. Check the 'Use assets from Poly Haven' checkbox
                            3. Restart the connection to the MCP server"""
        }

    #region Hyper3D
    def get_hyper3d_status(self):
        """Get the current status of Hyper3D Rodin integration"""
        enabled = bpy.context.scene.blendermcp_use_hyper3d
        if enabled:
            if not bpy.context.scene.blendermcp_hyper3d_api_key:
                return {
                    "enabled": False,
                    "message": """Hyper3D Rodin integration is currently enabled, but API key is not given. To enable it:
                                1. In the 3D Viewport, find the Overtli-Blender panel in the sidebar (press N if hidden)
                                2. Keep the 'Use Hyper3D Rodin 3D model generation' checkbox checked
                                3. Choose the right plaform and fill in the API Key
                                4. Restart the connection to the MCP server"""
                }
            mode = bpy.context.scene.blendermcp_hyper3d_mode
            message = f"Hyper3D Rodin integration is enabled and ready to use. Mode: {mode}. " + \
                f"Key type: {'private' if bpy.context.scene.blendermcp_hyper3d_api_key != RODIN_FREE_TRIAL_KEY else 'free_trial'}"
            return {
                "enabled": True,
                "message": message
            }
        else:
            return {
                "enabled": False,
                "message": """Hyper3D Rodin integration is currently disabled. To enable it:
                            1. In the 3D Viewport, find the Overtli-Blender panel in the sidebar (press N if hidden)
                            2. Check the 'Use Hyper3D Rodin 3D model generation' checkbox
                            3. Restart the connection to the MCP server"""
            }

    def create_rodin_job(self, *args, **kwargs):
        match bpy.context.scene.blendermcp_hyper3d_mode:
            case "MAIN_SITE":
                return self.create_rodin_job_main_site(*args, **kwargs)
            case "FAL_AI":
                return self.create_rodin_job_fal_ai(*args, **kwargs)
            case _:
                return f"Error: Unknown Hyper3D Rodin mode!"

    def create_rodin_job_main_site(
            self,
            text_prompt: str=None,
            images: list[tuple[str, str]]=None,
            bbox_condition=None
        ):
        try:
            if images is None:
                images = []
            """Call Rodin API, get the job uuid and subscription key"""
            files = [
                *[("images", (f"{i:04d}{img_suffix}", img)) for i, (img_suffix, img) in enumerate(images)],
                ("tier", (None, "Sketch")),
                ("mesh_mode", (None, "Raw")),
            ]
            if text_prompt:
                files.append(("prompt", (None, text_prompt)))
            if bbox_condition:
                files.append(("bbox_condition", (None, json.dumps(bbox_condition))))
            response = requests.post(
                "https://hyperhuman.deemos.com/api/v2/rodin",
                headers={
                    "Authorization": f"Bearer {bpy.context.scene.blendermcp_hyper3d_api_key}",
                },
                files=files
            )
            data = response.json()
            return data
        except Exception as e:
            return {"error": str(e)}

    def create_rodin_job_fal_ai(
            self,
            text_prompt: str=None,
            images: list[tuple[str, str]]=None,
            bbox_condition=None
        ):
        try:
            req_data = {
                "tier": "Sketch",
            }
            if images:
                req_data["input_image_urls"] = images
            if text_prompt:
                req_data["prompt"] = text_prompt
            if bbox_condition:
                req_data["bbox_condition"] = bbox_condition
            response = requests.post(
                "https://queue.fal.run/fal-ai/hyper3d/rodin",
                headers={
                    "Authorization": f"Key {bpy.context.scene.blendermcp_hyper3d_api_key}",
                    "Content-Type": "application/json",
                },
                json=req_data
            )
            data = response.json()
            return data
        except Exception as e:
            return {"error": str(e)}

    def poll_rodin_job_status(self, *args, **kwargs):
        match bpy.context.scene.blendermcp_hyper3d_mode:
            case "MAIN_SITE":
                return self.poll_rodin_job_status_main_site(*args, **kwargs)
            case "FAL_AI":
                return self.poll_rodin_job_status_fal_ai(*args, **kwargs)
            case _:
                return f"Error: Unknown Hyper3D Rodin mode!"

    def poll_rodin_job_status_main_site(self, subscription_key: str):
        """Call the job status API to get the job status"""
        response = requests.post(
            "https://hyperhuman.deemos.com/api/v2/status",
            headers={
                "Authorization": f"Bearer {bpy.context.scene.blendermcp_hyper3d_api_key}",
            },
            json={
                "subscription_key": subscription_key,
            },
        )
        data = response.json()
        return {
            "status_list": [i["status"] for i in data["jobs"]]
        }

    def poll_rodin_job_status_fal_ai(self, request_id: str):
        """Call the job status API to get the job status"""
        response = requests.get(
            f"https://queue.fal.run/fal-ai/hyper3d/requests/{request_id}/status",
            headers={
                "Authorization": f"KEY {bpy.context.scene.blendermcp_hyper3d_api_key}",
            },
        )
        data = response.json()
        return data

    @staticmethod
    def _clean_imported_glb(filepath, mesh_name=None):
        # Get the set of existing objects before import
        existing_objects = set(bpy.data.objects)

        # Import the GLB file
        bpy.ops.import_scene.gltf(filepath=filepath)

        # Ensure the context is updated
        bpy.context.view_layer.update()

        # Get all imported objects
        imported_objects = list(set(bpy.data.objects) - existing_objects)
        # imported_objects = [obj for obj in bpy.context.view_layer.objects if obj.select_get()]

        if not imported_objects:
            print("Error: No objects were imported.")
            return

        # Identify the mesh object
        mesh_obj = None

        if len(imported_objects) == 1 and imported_objects[0].type == 'MESH':
            mesh_obj = imported_objects[0]
            print("Single mesh imported, no cleanup needed.")
        else:
            if len(imported_objects) == 2:
                empty_objs = [i for i in imported_objects if i.type == "EMPTY"]
                if len(empty_objs) != 1:
                    print("Error: Expected an empty node with one mesh child or a single mesh object.")
                    return
                parent_obj = empty_objs.pop()
                if len(parent_obj.children) == 1:
                    potential_mesh = parent_obj.children[0]
                    if potential_mesh.type == 'MESH':
                        print("GLB structure confirmed: Empty node with one mesh child.")

                        # Unparent the mesh from the empty node
                        potential_mesh.parent = None

                        # Remove the empty node
                        bpy.data.objects.remove(parent_obj)
                        print("Removed empty node, keeping only the mesh.")

                        mesh_obj = potential_mesh
                    else:
                        print("Error: Child is not a mesh object.")
                        return
                else:
                    print("Error: Expected an empty node with one mesh child or a single mesh object.")
                    return
            else:
                print("Error: Expected an empty node with one mesh child or a single mesh object.")
                return

        # Rename the mesh if needed
        try:
            if mesh_obj and mesh_obj.name is not None and mesh_name:
                mesh_obj.name = mesh_name
                if mesh_obj.data.name is not None:
                    mesh_obj.data.name = mesh_name
                print(f"Mesh renamed to: {mesh_name}")
        except Exception as e:
            print("Having issue with renaming, give up renaming.")

        return mesh_obj

    def import_generated_asset(self, *args, **kwargs):
        match bpy.context.scene.blendermcp_hyper3d_mode:
            case "MAIN_SITE":
                return self.import_generated_asset_main_site(*args, **kwargs)
            case "FAL_AI":
                return self.import_generated_asset_fal_ai(*args, **kwargs)
            case _:
                return f"Error: Unknown Hyper3D Rodin mode!"

    def import_generated_asset_main_site(self, task_uuid: str, name: str):
        """Fetch the generated asset, import into blender"""
        response = requests.post(
            "https://hyperhuman.deemos.com/api/v2/download",
            headers={
                "Authorization": f"Bearer {bpy.context.scene.blendermcp_hyper3d_api_key}",
            },
            json={
                'task_uuid': task_uuid
            }
        )
        data_ = response.json()
        temp_file = None
        for i in data_["list"]:
            if i["name"].endswith(".glb"):
                temp_file = tempfile.NamedTemporaryFile(
                    delete=False,
                    prefix=task_uuid,
                    suffix=".glb",
                )

                try:
                    # Download the content
                    response = requests.get(i["url"], stream=True)
                    response.raise_for_status()  # Raise an exception for HTTP errors

                    # Write the content to the temporary file
                    for chunk in response.iter_content(chunk_size=8192):
                        temp_file.write(chunk)

                    # Close the file
                    temp_file.close()

                except Exception as e:
                    # Clean up the file if there's an error
                    temp_file.close()
                    os.unlink(temp_file.name)
                    return {"succeed": False, "error": str(e)}

                break
        else:
            return {"succeed": False, "error": "Generation failed. Please first make sure that all jobs of the task are done and then try again later."}

        try:
            obj = self._clean_imported_glb(
                filepath=temp_file.name,
                mesh_name=name
            )
            result = {
                "name": obj.name,
                "type": obj.type,
                "location": [obj.location.x, obj.location.y, obj.location.z],
                "rotation": [obj.rotation_euler.x, obj.rotation_euler.y, obj.rotation_euler.z],
                "scale": [obj.scale.x, obj.scale.y, obj.scale.z],
            }

            if obj.type == "MESH":
                bounding_box = self._get_aabb(obj)
                result["world_bounding_box"] = bounding_box

            return {
                "succeed": True, **result
            }
        except Exception as e:
            return {"succeed": False, "error": str(e)}

    def import_generated_asset_fal_ai(self, request_id: str, name: str):
        """Fetch the generated asset, import into blender"""
        response = requests.get(
            f"https://queue.fal.run/fal-ai/hyper3d/requests/{request_id}",
            headers={
                "Authorization": f"Key {bpy.context.scene.blendermcp_hyper3d_api_key}",
            }
        )
        data_ = response.json()
        temp_file = None

        temp_file = tempfile.NamedTemporaryFile(
            delete=False,
            prefix=request_id,
            suffix=".glb",
        )

        try:
            # Download the content
            response = requests.get(data_["model_mesh"]["url"], stream=True)
            response.raise_for_status()  # Raise an exception for HTTP errors

            # Write the content to the temporary file
            for chunk in response.iter_content(chunk_size=8192):
                temp_file.write(chunk)

            # Close the file
            temp_file.close()

        except Exception as e:
            # Clean up the file if there's an error
            temp_file.close()
            os.unlink(temp_file.name)
            return {"succeed": False, "error": str(e)}

        try:
            obj = self._clean_imported_glb(
                filepath=temp_file.name,
                mesh_name=name
            )
            result = {
                "name": obj.name,
                "type": obj.type,
                "location": [obj.location.x, obj.location.y, obj.location.z],
                "rotation": [obj.rotation_euler.x, obj.rotation_euler.y, obj.rotation_euler.z],
                "scale": [obj.scale.x, obj.scale.y, obj.scale.z],
            }

            if obj.type == "MESH":
                bounding_box = self._get_aabb(obj)
                result["world_bounding_box"] = bounding_box

            return {
                "succeed": True, **result
            }
        except Exception as e:
            return {"succeed": False, "error": str(e)}
    #endregion

    #region Sketchfab API
    def get_sketchfab_status(self):
        """Get the current status of Sketchfab integration"""
        enabled = bpy.context.scene.blendermcp_use_sketchfab
        api_key = bpy.context.scene.blendermcp_sketchfab_api_key

        # Test the API key if present
        if api_key:
            try:
                headers = {
                    "Authorization": f"Token {api_key}"
                }

                response = requests.get(
                    "https://api.sketchfab.com/v3/me",
                    headers=headers,
                    timeout=30  # Add timeout of 30 seconds
                )

                if response.status_code == 200:
                    user_data = response.json()
                    username = user_data.get("username", "Unknown user")
                    return {
                        "enabled": True,
                        "message": f"Sketchfab integration is enabled and ready to use. Logged in as: {username}"
                    }
                else:
                    return {
                        "enabled": False,
                        "message": f"Sketchfab API key seems invalid. Status code: {response.status_code}"
                    }
            except requests.exceptions.Timeout:
                return {
                    "enabled": False,
                    "message": "Timeout connecting to Sketchfab API. Check your internet connection."
                }
            except Exception as e:
                return {
                    "enabled": False,
                    "message": f"Error testing Sketchfab API key: {str(e)}"
                }

        if enabled and api_key:
            return {"enabled": True, "message": "Sketchfab integration is enabled and ready to use."}
        elif enabled and not api_key:
            return {
                "enabled": False,
                "message": """Sketchfab integration is currently enabled, but API key is not given. To enable it:
                            1. In the 3D Viewport, find the Overtli-Blender panel in the sidebar (press N if hidden)
                            2. Keep the 'Use Sketchfab' checkbox checked
                            3. Enter your Sketchfab API Key
                            4. Restart the connection to the MCP server"""
            }
        else:
            return {
                "enabled": False,
                "message": """Sketchfab integration is currently disabled. To enable it:
                            1. In the 3D Viewport, find the Overtli-Blender panel in the sidebar (press N if hidden)
                            2. Check the 'Use assets from Sketchfab' checkbox
                            3. Enter your Sketchfab API Key
                            4. Restart the connection to the MCP server"""
            }

    def search_sketchfab_models(self, query, categories=None, count=20, downloadable=True):
        """Search for models on Sketchfab based on query and optional filters"""
        try:
            api_key = bpy.context.scene.blendermcp_sketchfab_api_key
            if not api_key:
                return {"error": "Sketchfab API key is not configured"}

            # Build search parameters with exact fields from Sketchfab API docs
            params = {
                "type": "models",
                "q": query,
                "count": count,
                "downloadable": downloadable,
                "archives_flavours": False
            }

            if categories:
                params["categories"] = categories

            # Make API request to Sketchfab search endpoint
            # The proper format according to Sketchfab API docs for API key auth
            headers = {
                "Authorization": f"Token {api_key}"
            }


            # Use the search endpoint as specified in the API documentation
            response = requests.get(
                "https://api.sketchfab.com/v3/search",
                headers=headers,
                params=params,
                timeout=30  # Add timeout of 30 seconds
            )

            if response.status_code == 401:
                return {"error": "Authentication failed (401). Check your API key."}

            if response.status_code != 200:
                return {"error": f"API request failed with status code {response.status_code}"}

            response_data = response.json()

            # Safety check on the response structure
            if response_data is None:
                return {"error": "Received empty response from Sketchfab API"}

            # Handle 'results' potentially missing from response
            results = response_data.get("results", [])
            if not isinstance(results, list):
                return {"error": f"Unexpected response format from Sketchfab API: {response_data}"}

            return response_data

        except requests.exceptions.Timeout:
            return {"error": "Request timed out. Check your internet connection."}
        except json.JSONDecodeError as e:
            return {"error": f"Invalid JSON response from Sketchfab API: {str(e)}"}
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"error": str(e)}

    def download_sketchfab_model(self, uid):
        """Download a model from Sketchfab by its UID"""
        try:
            api_key = bpy.context.scene.blendermcp_sketchfab_api_key
            if not api_key:
                return {"error": "Sketchfab API key is not configured"}

            # Use proper authorization header for API key auth
            headers = {
                "Authorization": f"Token {api_key}"
            }

            # Request download URL using the exact endpoint from the documentation
            download_endpoint = f"https://api.sketchfab.com/v3/models/{uid}/download"

            response = requests.get(
                download_endpoint,
                headers=headers,
                timeout=30  # Add timeout of 30 seconds
            )

            if response.status_code == 401:
                return {"error": "Authentication failed (401). Check your API key."}

            if response.status_code != 200:
                return {"error": f"Download request failed with status code {response.status_code}"}

            data = response.json()

            # Safety check for None data
            if data is None:
                return {"error": "Received empty response from Sketchfab API for download request"}

            # Extract download URL with safety checks
            gltf_data = data.get("gltf")
            if not gltf_data:
                return {"error": "No gltf download URL available for this model. Response: " + str(data)}

            download_url = gltf_data.get("url")
            if not download_url:
                return {"error": "No download URL available for this model. Make sure the model is downloadable and you have access."}

            # Download the model (already has timeout)
            model_response = requests.get(download_url, timeout=60)  # 60 second timeout

            if model_response.status_code != 200:
                return {"error": f"Model download failed with status code {model_response.status_code}"}

            # Save to temporary file
            temp_dir = tempfile.mkdtemp()
            zip_file_path = os.path.join(temp_dir, f"{uid}.zip")

            with open(zip_file_path, "wb") as f:
                f.write(model_response.content)

            # Extract the zip file with enhanced security
            with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                # More secure zip slip prevention
                for file_info in zip_ref.infolist():
                    # Get the path of the file
                    file_path = file_info.filename

                    # Convert directory separators to the current OS style
                    # This handles both / and \ in zip entries
                    target_path = os.path.join(temp_dir, os.path.normpath(file_path))

                    # Get absolute paths for comparison
                    abs_temp_dir = os.path.abspath(temp_dir)
                    abs_target_path = os.path.abspath(target_path)

                    # Ensure the normalized path doesn't escape the target directory
                    if not abs_target_path.startswith(abs_temp_dir):
                        with suppress(Exception):
                            shutil.rmtree(temp_dir)
                        return {"error": "Security issue: Zip contains files with path traversal attempt"}

                    # Additional explicit check for directory traversal
                    if ".." in file_path:
                        with suppress(Exception):
                            shutil.rmtree(temp_dir)
                        return {"error": "Security issue: Zip contains files with directory traversal sequence"}

                # If all files passed security checks, extract them
                zip_ref.extractall(temp_dir)

            # Find the main glTF file
            gltf_files = [f for f in os.listdir(temp_dir) if f.endswith('.gltf') or f.endswith('.glb')]

            if not gltf_files:
                with suppress(Exception):
                    shutil.rmtree(temp_dir)
                return {"error": "No glTF file found in the downloaded model"}

            main_file = os.path.join(temp_dir, gltf_files[0])

            # Import the model
            bpy.ops.import_scene.gltf(filepath=main_file)

            # Get the names of imported objects
            imported_objects = [obj.name for obj in bpy.context.selected_objects]

            # Clean up temporary files
            with suppress(Exception):
                shutil.rmtree(temp_dir)

            return {
                "success": True,
                "message": "Model imported successfully",
                "imported_objects": imported_objects
            }

        except requests.exceptions.Timeout:
            return {"error": "Request timed out. Check your internet connection and try again with a simpler model."}
        except json.JSONDecodeError as e:
            return {"error": f"Invalid JSON response from Sketchfab API: {str(e)}"}
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"error": f"Failed to download model: {str(e)}"}
    #endregion

    #region Geometry Nodes
    def get_geometry_nodes_capabilities(self):
        return self.geometry_nodes_intelligence_service.get_geometry_nodes_capabilities()

    def list_geometry_node_groups(self, include_builtin=False, include_users=True, include_interface=True, include_node_summary=True, max_groups=None):
        return self.geometry_nodes_intelligence_service.list_geometry_node_groups(include_builtin, include_users, include_interface, include_node_summary, max_groups)

    def get_geometry_node_group_deep_info(self, node_group_name, include_nodes=True, include_links=True, include_interface=True, include_modifier_users=True, max_nodes=None):
        return self.geometry_nodes_intelligence_service.get_geometry_node_group_deep_info(node_group_name, include_nodes, include_links, include_interface, include_modifier_users, max_nodes)

    def list_geometry_nodes_modifiers(self, object_name=None, include_inputs=True, include_group_info=True):
        return self.geometry_nodes_intelligence_service.list_geometry_nodes_modifiers(object_name, include_inputs, include_group_info)

    def get_geometry_nodes_modifier_info(self, object_name, modifier_name, include_inputs=True, include_group_info=True):
        return self.geometry_nodes_intelligence_service.get_geometry_nodes_modifier_info(object_name, modifier_name, include_inputs, include_group_info)

    def get_supported_geometry_node_templates(self):
        return self.geometry_nodes_template_service.get_supported_geometry_node_templates()

    def create_geometry_node_group_from_template(self, template_name, node_group_name, parameters=None, material_name=None, replace_existing=False, verify=False, artifact_root=None):
        return self.geometry_nodes_template_service.create_geometry_node_group_from_template(template_name, node_group_name, parameters, material_name, replace_existing, verify, artifact_root)

    def create_custom_geometry_node_recipe(self, node_group_name, recipe, replace_existing=False, verify=False, artifact_root=None):
        return self.geometry_nodes_recipe_service.create_custom_geometry_node_recipe(node_group_name, recipe, replace_existing, verify, artifact_root)

    def apply_geometry_nodes_modifier(self, object_name, node_group_name, modifier_name=None, input_values=None, verify=False):
        return self.geometry_nodes_modifier_service.apply_geometry_nodes_modifier(object_name, node_group_name, modifier_name, input_values, verify)

    def set_geometry_nodes_modifier_input(self, object_name, modifier_name, input_values):
        return self.geometry_nodes_modifier_service.set_geometry_nodes_modifier_input(object_name, modifier_name, input_values)

    def create_procedural_asset(self, asset_type="curve_rope", asset_name=None, template_name=None, parameters=None, collection_name=None, material_name=None, verify=False, artifact_root=None):
        return self.procedural_asset_generator_service.create_procedural_asset(asset_type, asset_name, template_name, parameters, collection_name, material_name, verify, artifact_root)

    def create_scatter_system(self, target_object_name=None, asset_name=None, template_name="scatter_on_surface", parameters=None, collection_name=None, material_name=None, verify=False, artifact_root=None):
        return self.procedural_asset_generator_service.create_scatter_system(target_object_name, asset_name, template_name, parameters, collection_name, material_name, verify, artifact_root)

    def create_curve_generator(self, asset_name=None, template_name="beveled_curve_path", parameters=None, collection_name=None, material_name=None, verify=False, artifact_root=None):
        return self.procedural_asset_generator_service.create_curve_generator(asset_name, template_name, parameters, collection_name, material_name, verify, artifact_root)

    def create_radial_array_system(self, source_object_name=None, asset_name=None, parameters=None, collection_name=None, material_name=None, verify=False, artifact_root=None):
        return self.procedural_asset_generator_service.create_radial_array_system(source_object_name, asset_name, parameters, collection_name, material_name, verify, artifact_root)

    def create_panel_generator(self, asset_name=None, template_name="panel_grid", parameters=None, collection_name=None, material_name=None, verify=False, artifact_root=None):
        return self.procedural_asset_generator_service.create_panel_generator(asset_name, template_name, parameters, collection_name, material_name, verify, artifact_root)

    def create_cable_or_rope_generator(self, asset_name=None, template_name="curve_rope", parameters=None, collection_name=None, material_name=None, verify=False, artifact_root=None):
        return self.procedural_asset_generator_service.create_cable_or_rope_generator(asset_name, template_name, parameters, collection_name, material_name, verify, artifact_root)

    def create_terrain_noise_system(self, asset_name=None, parameters=None, collection_name=None, material_name=None, verify=False, artifact_root=None):
        return self.procedural_asset_generator_service.create_terrain_noise_system(asset_name, parameters, collection_name, material_name, verify, artifact_root)

    def validate_geometry_node_group(self, node_group_name, expected_template=None):
        return self.geometry_nodes_validation_service.validate_geometry_node_group(node_group_name, expected_template)

    def create_geometry_nodes_preview(self, node_group_name=None, object_name=None, label=None, include_scene_snapshot=True, artifact_root=None):
        return self.geometry_nodes_preview_service.create_geometry_nodes_preview(node_group_name, object_name, label, include_scene_snapshot, artifact_root)

    def create_geometry_nodes_scene_kit(self, kit_id=None, label=None, object_names=None, node_group_names=None, include_preview=True, overwrite=True, artifact_root=None):
        return self.geometry_nodes_preview_service.create_geometry_nodes_scene_kit(kit_id, label, object_names, node_group_names, include_preview, overwrite, artifact_root)

    def delete_geometry_node_groups(self, node_group_names=None, prefix=None, confirm=False):
        return self.geometry_nodes_validation_service.delete_geometry_node_groups(node_group_names, prefix, confirm)

    def remove_geometry_nodes_modifiers(self, object_name=None, modifier_names=None, prefix=None, confirm=False):
        return self.geometry_nodes_modifier_service.remove_geometry_nodes_modifiers(object_name, modifier_names, prefix, confirm)

    def run_geometry_nodes_workflow_batch(self, label=None, operations=None, create_before_snapshot=True, create_after_snapshot=True, stop_on_error=True, max_operations=40, batch_allow_destructive=False, artifact_root=None):
        return self.geometry_nodes_workflow_batch_service.run_geometry_nodes_workflow_batch(label, operations, create_before_snapshot, create_after_snapshot, stop_on_error, max_operations, batch_allow_destructive, artifact_root)

    def complete_geometry_node(self, object_name, nodes, links, input_sockets=None):
        """Complete geometry node network creation"""
        return self.geometry_nodes_service.complete_geometry_node(object_name, nodes, links, input_sockets)

    def _create_geometry_nodes_object(self, object_name):
        """Create a basic object for geometry nodes"""
        return self.geometry_nodes_service._create_geometry_nodes_object(object_name)

    def _setup_node_group_interface(self, node_group, input_sockets):
        """Setup the node group interface for inputs/outputs"""
        return self.geometry_nodes_service._setup_node_group_interface(node_group, input_sockets)

    def get_geometry_nodes_status(self):
        """Get the status of geometry nodes support"""
        return self.geometry_nodes_service.get_geometry_nodes_status()

    #region Script Registry Tools

    def _get_script_directory(self, category):
        """Get the script directory path for a given category"""
        return self.script_registry_service._get_script_directory(category)

    def _get_metadata_path(self, script_dir):
        """Get the metadata file path for a script directory"""
        return self.script_registry_service._get_metadata_path(script_dir)

    def _load_metadata(self, script_dir):
        """Load metadata for a script directory"""
        return self.script_registry_service._load_metadata(script_dir)

    def _save_script_metadata(self, script_dir, script_name, permanent):
        """Save metadata for a script"""
        return self.script_registry_service._save_script_metadata(script_dir, script_name, permanent)

    def register_context_script(self, script_name, script_content, category="default", permanent=False):
        """Register a Python script for later execution"""
        return self.script_registry_service.register_context_script(script_name, script_content, category, permanent)

    def execute_context_script(self, script_name, category="default"):
        """Execute a previously registered script"""
        return self.script_registry_service.execute_context_script(script_name, category)

    def list_context_scripts(self, category=None):
        """List all registered scripts"""
        return self.script_registry_service.list_context_scripts(category)

    def clear_context_scripts(self, category=None, script_name=None, clear_permanent=False):
        """Clear scripts from the registry"""
        return self.script_registry_service.clear_context_scripts(category, script_name, clear_permanent)

    #endregion
    #endregion

# Blender UI Panel
