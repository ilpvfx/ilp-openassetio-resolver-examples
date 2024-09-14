from __future__ import annotations

import weakref

import maya.OpenMaya as OpenMaya
import maya.OpenMayaMPx as OpenMayaMPx


class OpenAssetIOResolver(OpenMayaMPx.MPxFileResolver):
    @staticmethod
    def className() -> str:
        """Returns the name of this class."""

        return "OpenAssetIOResolver"

    @staticmethod
    def theCreator() -> weakref.ProxyType[OpenAssetIOResolver]:
        """Returns a pointer to a function that will return a pointer to a new instance of
        this resolver.
        """

        return OpenMayaMPx.asMPxPtr(OpenAssetIOResolver())

    def uriScheme(self) -> str:
        """This method is called to query the URI scheme that is handled by this
        resolver.
        """

        return "foo"

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


def initializePlugin(plugin: OpenMaya.MObject):
    pluginFn = OpenMayaMPx.MFnPlugin(plugin)

    try:
        pluginFn.registerURIFileResolver(
            OpenAssetIOResolver.className(), "foo", OpenAssetIOResolver.theCreator
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
