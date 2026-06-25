# Channel Packing

Phase 8A adds planning, validation, and bounded runtime support for packed texture maps.

Supported layouts:

- `ORM`: R=AO, G=Roughness, B=Metallic.
- `RMA`: R=Roughness, G=Metallic, B=AO.
- `MRA`: R=Metallic, G=Roughness, B=AO.
- `GLTF_METALLIC_ROUGHNESS`: G=Roughness, B=Metallic.
- `CUSTOM`: caller-provided channel mapping.

Packed outputs are classified as `derived`, not native bake passes. They use `Non-Color` color-space intent and default to `textures/packed/`.

`validate_packed_texture` checks whether the packed image or file exists, reports layout channel metadata, and returns file hash information when a file is available. Overwriting packed outputs requires approval.
