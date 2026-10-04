{{flutter_js}}
{{flutter_build_config}}

// Flutter's default load, plus: the branded splash in index.html goes once
// the app is running.
_flutter.loader.load({
  onEntrypointLoaded: async function (engineInitializer) {
    const appRunner = await engineInitializer.initializeEngine();
    await appRunner.runApp();
    const splash = document.getElementById('splash');
    if (splash) splash.remove();
  },
});
