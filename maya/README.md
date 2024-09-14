# OpenAssetIO Resolver for Maya

This project demonstrates how to resolve file paths inside [Maya](https://www.autodesk.com/products/maya/overview) using [OpenAssetIO](https://openassetio.github.io/OpenAssetIO/), leveraging the `OpenMayaMPx.MPxFileResolver`.

> [!IMPORTANT]
> This is a prototype and not meant to be a feature-complete or stable plugin. It is designed as a foundation for integrating OpenAssetIO into Maya, with further development and customization expected for production environments.

## Getting Started

To use the plugin, first ensure the `maya` directory from this repository is included in Maya’s module search path. Set (or append to) the `MAYA_MODULE_PATH` environment variable to point to this directory.

Additionally, the resolver requires `openassetio` to be available at Maya's runtime. You can install the required Python dependencies using Maya's bundled Python interpreter (`mayapy`):
```bash
mayapy -m pip install -r maya/requirements.txt
```
Once installed, enable the plugin by starting Maya and navigating to `Windows > Settings/Preferences > Plug-in Manager`. From there, load the `OpenAssetIOMayaResolver.py` plugin.

> [!NOTE]
> The plugin expects an OpenAssetIO manager to be available at runtime. Ensure the manager is installed and accessible via the `OPENASSETIO_PLUGIN_PATH` environment variable, and configured as the [default manager](http://docs.openassetio.org/OpenAssetIO/glossary.html#default_config_var).

### URI Scheme Handling

The Maya resolver requires a valid URI scheme for file resolution. The plugin automatically handles this by extracting the entity reference prefix from the manager using the `info()` method, and ensuring that any protocol-like components (e.g., "://") are excluded. For example, a prefix like `bal:///` will be normalized to `bal`. If no such components are found, the resolver will use the entity reference prefix as is.

This ensures that Maya can interpret the scheme correctly without encountering errors from improper formatting.

## Usage
Once the plugin is loaded and configured, Maya will automatically call the resolver methods whenever it encounters a URI-based file path during file resolution tasks (file open, `setAttr`, texture loading, etc.). The plugin then resolves the `LocatableContentTrait` for the file path and returns its location.

For example, to create a reference node from an entity reference, run:
```python
import maya.cmds as cmds

cmds.file("bal:///cat", type="Alembic", reference=True)
```

The reference can then be managed (reloaded, entity reference modified, etc.) using the Maya Reference Editor: `File > Reference Editor`.
