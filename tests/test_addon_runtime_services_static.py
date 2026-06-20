from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADDON_TEXT = (ROOT / "addon.py").read_text(encoding="utf-8")


def test_addon_defines_runtime_service_classes() -> None:
    for name in [
        "class SceneObservationService",
        "class ViewportScreenshotService",
        "class ProviderStatusService",
        "class PolyHavenService",
        "class SketchfabService",
        "class Hyper3DService",
    ]:
        assert name in ADDON_TEXT


def test_addon_initializes_runtime_service_instances() -> None:
    for name in [
        "self.scene_observation_service = SceneObservationService(self)",
        "self.viewport_screenshot_service = ViewportScreenshotService(self)",
        "self.provider_status_service = ProviderStatusService(self)",
        "self.polyhaven_service = PolyHavenService(self)",
        "self.sketchfab_service = SketchfabService(self)",
        "self.hyper3d_service = Hyper3DService(self)",
    ]:
        assert name in ADDON_TEXT


def test_addon_binds_runtime_service_command_methods() -> None:
    for name in [
        "self.get_scene_info = self.scene_observation_service.get_scene_info",
        "self.get_object_info = self.scene_observation_service.get_object_info",
        "self.get_viewport_screenshot = self.viewport_screenshot_service.get_viewport_screenshot",
        "self.get_polyhaven_status = self.provider_status_service.get_polyhaven_status",
        "self.get_hyper3d_status = self.provider_status_service.get_hyper3d_status",
        "self.get_sketchfab_status = self.provider_status_service.get_sketchfab_status",
        "self.get_polyhaven_categories = self.polyhaven_service.get_polyhaven_categories",
        "self.search_polyhaven_assets = self.polyhaven_service.search_polyhaven_assets",
        "self.download_polyhaven_asset = self.polyhaven_service.download_polyhaven_asset",
        "self.set_texture = self.polyhaven_service.set_texture",
        "self.search_sketchfab_models = self.sketchfab_service.search_sketchfab_models",
        "self.download_sketchfab_model = self.sketchfab_service.download_sketchfab_model",
        "self.create_rodin_job = self.hyper3d_service.create_rodin_job",
        "self.poll_rodin_job_status = self.hyper3d_service.poll_rodin_job_status",
        "self.import_generated_asset = self.hyper3d_service.import_generated_asset",
    ]:
        assert name in ADDON_TEXT


def test_addon_runtime_services_preserve_existing_contracts() -> None:
    for name in [
        "get_scene_info",
        "get_object_info",
        "get_viewport_screenshot",
        "get_polyhaven_status",
        "get_hyper3d_status",
        "get_sketchfab_status",
        "get_polyhaven_categories",
        "search_polyhaven_assets",
        "download_polyhaven_asset",
        "set_texture",
        "search_sketchfab_models",
        "download_sketchfab_model",
        "create_rodin_job",
        "poll_rodin_job_status",
        "import_generated_asset",
        "blendermcp_use_polyhaven",
        "blendermcp_use_hyper3d",
        "blendermcp_use_sketchfab",
        "execute_code",
        "complete_geometry_node",
        "get_geometry_nodes_status",
    ]:
        assert name in ADDON_TEXT
