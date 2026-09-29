import 'dart:async';
import 'dart:js_interop';
import 'dart:ui_web' as ui_web;

import 'package:flutter/widgets.dart';
import 'package:web/web.dart' as web;

import '../../../data/datasources/api/api_error.dart';

// Google Identity Services, loaded on first use from Google's own URL (the
// only place it is served from); https://developers.google.com/identity/gsi/web
@JS('google.accounts.id.initialize')
external void _initialize(_IdConfig config);

@JS('google.accounts.id.renderButton')
external void _renderButton(web.HTMLElement parent, _ButtonOptions options);

extension type _IdConfig._(JSObject _) implements JSObject {
  // Google's own option names, which the object literal must carry as written.
  // ignore: non_constant_identifier_names
  external factory _IdConfig({String client_id, JSFunction callback, bool auto_select});
}

extension type _ButtonOptions._(JSObject _) implements JSObject {
  external factory _ButtonOptions({String type, String theme, String size, String text, String shape, int width});
}

extension type _CredentialResponse._(JSObject _) implements JSObject {
  external String get credential;
}

Future<void>? _loading;

Future<void> _loadScript() => _loading ??= () {
      final done = Completer<void>();
      final script = web.HTMLScriptElement()
        ..src = 'https://accounts.google.com/gsi/client'
        ..async = true;
      script.onload = ((web.Event _) => done.complete()).toJS;
      script.onerror = ((web.Event _) {
        _loading = null; // let the next visit try again
        done.completeError(StateError('Google sign-in could not load. Check the connection, or use your password.'));
      }).toJS;
      web.document.head!.append(script);
      return done.future;
    }();

var _views = 0;

Widget googleButton({required String clientId, required void Function(String credential) onCredential,
        required void Function(String message) onProblem}) =>
    _GsiButton(clientId: clientId, onCredential: onCredential, onProblem: onProblem);

class _GsiButton extends StatefulWidget {
  final String clientId;
  final void Function(String credential) onCredential;
  final void Function(String message) onProblem;
  const _GsiButton({required this.clientId, required this.onCredential, required this.onProblem});

  @override
  State<_GsiButton> createState() => _GsiButtonState();
}

class _GsiButtonState extends State<_GsiButton> {
  // One platform view per button, registered once, not on every rebuild.
  late final String _viewType = 'gsi-button-${_views++}';

  @override
  void initState() {
    super.initState();
    ui_web.platformViewRegistry.registerViewFactory(_viewType, (int _) {
      final host = web.HTMLDivElement();
      _loadScript().then((_) {
        _initialize(_IdConfig(
            client_id: widget.clientId,
            auto_select: false,
            callback: ((_CredentialResponse r) => widget.onCredential(r.credential)).toJS));
        _renderButton(host, _ButtonOptions(type: 'standard', theme: 'outline', size: 'large', text: 'signin_with',
            shape: 'pill', width: 280));
      }, onError: (Object e) => widget.onProblem(serverErrorMessage(e)));
      return host;
    });
  }

  @override
  Widget build(BuildContext context) =>
      SizedBox(width: 280, height: 44, child: HtmlElementView(viewType: _viewType));
}
