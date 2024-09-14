from __future__ import annotations

import weakref
from functools import partial

import maya.OpenMaya as OpenMaya
import maya.OpenMayaMPx as OpenMayaMPx
from openassetio import constants, errors
from openassetio.hostApi import HostInterface, Manager, ManagerFactory
from openassetio.log import LoggerInterface, SeverityFilter
from openassetio.pluginSystem import (
    CppPluginSystemManagerImplementationFactory,
    HybridPluginSystemManagerImplementationFactory,
    PythonPluginSystemManagerImplementationFactory,
)


class OpenAssetIOResolver(OpenMayaMPx.MPxFileResolver):
    def __init__(self, manager: Manager, uriScheme: str):
        super().__init__()

        self._manager = manager
        self._context = manager.createContext()

        self._uriScheme = uriScheme

    @staticmethod
    def className() -> str:
        """Returns the name of this class."""

        return "OpenAssetIOResolver"

    @staticmethod
    def theCreator(
        manager: Manager, uriScheme: str
    ) -> weakref.ProxyType[OpenAssetIOResolver]:
        """Returns a pointer to a function that will return a pointer to a new instance of
        this resolver.
        """

        return OpenMayaMPx.asMPxPtr(OpenAssetIOResolver(manager, uriScheme))

    def uriScheme(self) -> str:
        """This method is called to query the URI scheme that is handled by this
        resolver.
        """

        return self._uriScheme

    def resolveURIWithContext(
        self,
        uriFilePath: OpenMaya.MURI,
        mode: OpenMayaMPx.MPxFileResolver.MPxFileResolverMode,
        contextNodeFullName: str,
    ) -> str:
        """This method is called by Maya to convert a URI into a file path that Maya can
        access.

        It receives an MURI object with the URI and, if applicable, the owner's fullname
        (context). The resolver interprets the URI and may use the context to determine
        the physical file path for Maya. The context may be empty if the URI is an
        application property not tied to a specific scene element.

        The output is a fully qualified file path, though successful resolution doesn't
        guarantee the file's existence. The resolution mode provides additional context
        for the request; refer to MPxFileResolverMode for more information.
        """

        if mode & OpenMayaMPx.MPxFileResolver.kNone:
            # When kNone is used, the resolver should simply return the resolved path as
            # efficiently as possible. The path returned by the resolver will not be
            # checked for existence.
            ...

        elif mode & OpenMayaMPx.MPxFileResolver.kInput:
            # In this case, the resolver plug-in may need to do additional work to ensure
            # that the resolved path is available to the application. The path returned by
            # the resolver will be checked for existence.
            ...

        else:
            ...

        return uriFilePath.getPath()

    def performAfterSaveURI(self, uriValue: OpenMaya.MURI, resolvedFullName: str):
        """The method will be called by Maya after a scene file associated with this URI
        resolver is saved (i.e. a scene having a URI file path corresponding to the URI
        scheme implemented by this resolver.)

        The arguments to the method provide information about the file that was just
        saved: The URI file path is the unresolved path to the file, the resolved path
        gives the physical location of the file.
        """


class MayaOpenAssetIOResolverHost(HostInterface):
    def identifier(self) -> str:
        return "com.ilpvfx.maya.resolver"

    def displayName(self) -> str:
        return "Maya Resolver"


class MayaOpenAssetIOResolverLogger(LoggerInterface):
    def log(self, severity: LoggerInterface.Severity, message: str):
        """Converts log messages from OpenAssetIO's logging framework to Maya's display
        messaging system.
        """

        match severity:
            case LoggerInterface.Severity.kCritical | LoggerInterface.Severity.kError:
                OpenMaya.MGlobal.displayError(message)

            case LoggerInterface.Severity.kInfo | LoggerInterface.Severity.kProgress:
                OpenMaya.MGlobal.displayInfo(message)

            case LoggerInterface.Severity.kWarning:
                OpenMaya.MGlobal.displayWarning(message)


def getDefaultManager() -> Manager | None:
    """Creates and returns the default OpenAssetIO Manager instance using a hybrid
    C++ and Python plugin system. This manager is used to interface with assets
    in Maya through OpenAssetIO.
    """

    logger = SeverityFilter(MayaOpenAssetIOResolverLogger())

    # Create a hybrid plugin system that combines both C++ and Python plugin systems.
    # This allows the manager to load and interact with plugins from both languages.
    factory = HybridPluginSystemManagerImplementationFactory(
        [
            CppPluginSystemManagerImplementationFactory(logger),
            PythonPluginSystemManagerImplementationFactory(logger),
        ],
        logger,
    )

    # Create the host interface, which identifies this system (Maya) to the manager.
    host = MayaOpenAssetIOResolverHost()

    return ManagerFactory.defaultManagerForInterface(host, factory, logger)


def initializePlugin(plugin: OpenMaya.MObject):
    """Initializes the plugin in Maya by registering a URI-based file resolver.

    This function checks for the availability of a default OpenAssetIO manager and
    verifies that the manager has the necessary resolution capabilities. It also
    retrieves the entity reference prefix from the manager's info and uses it to
    register the URI file resolver.
    """

    pluginFn = OpenMayaMPx.MFnPlugin(plugin)

    try:
        if not (manager := getDefaultManager()):
            raise errors.ConfigurationException(
                "No default OpenAssetIO manager configured"
            )

        if not manager.hasCapability(manager.Capability.kResolution):
            raise errors.ConfigurationException(
                f"Entity resolution not supported by manager: {manager.displayName()!r}"
            )

        # Retrieve the entity reference prefix from the manager's info.
        prefix = manager.info().get(constants.kInfoKey_EntityReferencesMatchPrefix)
        if not prefix:
            raise errors.ConfigurationException(
                f"Unable to retrieve prefix for manager: {manager.displayName()!r}"
            )

        # Derive the URI scheme from the prefix, defaulting to the prefix if no scheme is
        # found and ensure that any protocol-like components (e.g., "://") are excluded.
        uriScheme = OpenMaya.MURI(prefix).getScheme() or prefix

        pluginFn.registerURIFileResolver(
            OpenAssetIOResolver.className(),
            uriScheme,
            partial(OpenAssetIOResolver.theCreator, manager, uriScheme),
        )

    except Exception:
        OpenMaya.MGlobal.displayError(
            "Failed to register file resolver: '{}'".format(
                OpenAssetIOResolver.className()
            )
        )

        raise


def uninitializePlugin(plugin: OpenMaya.MObject):
    pluginFn = OpenMayaMPx.MFnPlugin(plugin)

    try:
        pluginFn.deregisterURIFileResolver(OpenAssetIOResolver.className())

    except Exception:
        OpenMaya.MGlobal.displayError(
            "Failed to deregister file resolver: '{}'".format(
                OpenAssetIOResolver.className()
            )
        )

        raise
