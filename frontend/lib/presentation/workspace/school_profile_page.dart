import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:gap/gap.dart';
import 'package:get_it/get_it.dart';
import 'package:image_picker/image_picker.dart';

import '../../data/datasources/api/api_error.dart';
import '../shared/widgets/common_widgets.dart';
import 'ops_api.dart';
import 'strings.dart';
import '../shared/widgets/shell.dart';

const _base = '/curriculum/school-profile';

/// The school's own name, address, affiliation line and logo -- what every
/// paper, answer key and report prints at the top (REQUIREMENTS EX-5, audit
/// D41: until this, a school that had not opened the Template Maker printed
/// "Default CBSE Template" where its name goes). The principal's.
class SchoolProfilePage extends StatefulWidget {
  /// Picks the logo image; a test passes one that returns bytes directly.
  final Future<(Uint8List, String, String)?> Function()? pickLogo;

  const SchoolProfilePage({super.key, this.pickLogo});

  @override
  State<SchoolProfilePage> createState() => _SchoolProfilePageState();
}

class _SchoolProfilePageState extends State<SchoolProfilePage> {
  late Future<Map<String, dynamic>> _future = _load();
  final _name = TextEditingController();
  final _address = TextEditingController();
  final _affiliation = TextEditingController();
  Future<Uint8List?>? _logo;
  bool _busy = false;
  String? _error;
  String? _note;

  Future<Map<String, dynamic>> _load() async {
    final p = await Ops.map(_base);
    _name.text = p['name'] as String? ?? '';
    _address.text = p['address'] as String? ?? '';
    _affiliation.text = p['affiliation'] as String? ?? '';
    _logo = p['hasLogo'] == true ? _logoBytes() : null;
    return p;
  }

  Future<Uint8List?> _logoBytes() => Ops.bytes('$_base/logo');

  @override
  void dispose() {
    _name.dispose();
    _address.dispose();
    _affiliation.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    if (_name.text.trim().isEmpty) {
      setState(() => _error = tr('Give the school its name, as it should print on papers.'));
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
      _note = null;
    });
    try {
      await Ops.put(_base, body: {
        'name': _name.text.trim(),
        'address': _address.text.trim().isEmpty ? null : _address.text.trim(),
        'affiliation': _affiliation.text.trim().isEmpty ? null : _affiliation.text.trim(),
      });
      if (mounted) setState(() { _note = tr('Saved. New papers print this name.'); _future = _load(); });
    } catch (e) {
      if (mounted) setState(() => _error = serverErrorMessage(e));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  static Future<(Uint8List, String, String)?> _pickFromGallery() async {
    final picked = await ImagePicker().pickImage(source: ImageSource.gallery, maxWidth: 800);
    if (picked == null) return null;
    final bytes = await picked.readAsBytes();
    final mime = picked.mimeType ?? (picked.name.toLowerCase().endsWith('.png') ? 'image/png' : 'image/jpeg');
    return (bytes, picked.name, mime);
  }

  Future<void> _upload() async {
    final picked = await (widget.pickLogo ?? _pickFromGallery)();
    if (picked == null) return;
    final (bytes, name, mime) = picked;
    setState(() {
      _busy = true;
      _error = null;
      _note = null;
    });
    try {
      final parts = mime.split('/');
      await GetIt.I<Dio>().post('$_base/logo', data: FormData.fromMap({
        'file': MultipartFile.fromBytes(bytes, filename: name, contentType: DioMediaType(parts[0], parts[1])),
      }));
      if (mounted) setState(() { _note = tr('Logo saved.'); _future = _load(); });
    } on DioException catch (e) {
      if (mounted) setState(() => _error = serverErrorMessage(e));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _removeLogo() async {
    setState(() => _busy = true);
    try {
      await Ops.delete('$_base/logo');
      if (mounted) setState(() { _note = tr('Logo removed.'); _future = _load(); });
    } catch (e) {
      if (mounted) setState(() => _error = serverErrorMessage(e));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: destinationAppBar(context, title: Text(tr('School profile'))),
      body: FutureBuilder<Map<String, dynamic>>(
        future: _future,
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) return const LoadingIndicator();
          if (snap.hasError) {
            return ErrorDisplay(message: serverErrorMessage(snap.error!),
                onRetry: () => setState(() { _future = _load(); }));
          }
          final named = snap.data!['name'] != null;
          return ListView(padding: const EdgeInsets.all(16), children: [
            Text(tr('Printed at the top of every paper, answer key and report.'), style: theme.textTheme.bodySmall),
            if (!named) ...[
              const Gap(8),
              Text(key: const ValueKey('profile-unnamed'),
                  tr('No name set yet: papers print no school name, or only a name given in the Template Maker.'),
                  style: TextStyle(color: theme.colorScheme.error)),
            ],
            const Gap(12),
            TextField(key: const ValueKey('profile-name'), controller: _name, maxLength: 120,
                decoration: InputDecoration(labelText: tr('School name'), hintText: 'Sunrise Public School')),
            const Gap(8),
            TextField(key: const ValueKey('profile-address'), controller: _address, maxLength: 200,
                decoration: InputDecoration(labelText: tr('Address (optional)'))),
            const Gap(8),
            TextField(key: const ValueKey('profile-affiliation'), controller: _affiliation, maxLength: 120,
                decoration: InputDecoration(labelText: tr('Affiliation line (optional)'),
                    hintText: 'CBSE Affiliation No. 1234567')),
            if (_error != null) ...[
              const Gap(8),
              Text(_error!, key: const ValueKey('profile-error'), style: TextStyle(color: theme.colorScheme.error)),
            ],
            if (_note != null) ...[const Gap(8), Text(_note!, style: theme.textTheme.bodySmall)],
            const Gap(8),
            FilledButton(key: const ValueKey('profile-save'), onPressed: _busy ? null : _save,
                style: phoneTapTarget(context), child: Text(tr('Save'))),
            const Gap(24),
            Text(tr('Logo'), style: theme.textTheme.titleSmall),
            const Gap(8),
            if (_logo != null)
              FutureBuilder<Uint8List?>(
                future: _logo,
                builder: (context, logo) {
                  if (logo.connectionState != ConnectionState.done) return const LinearProgressIndicator();
                  if (logo.hasError || logo.data == null) {
                    return Text(tr('The logo could not be shown.'), style: TextStyle(color: theme.colorScheme.error));
                  }
                  return Align(alignment: Alignment.centerLeft,
                      child: Image.memory(logo.data!, key: const ValueKey('profile-logo'), height: 72));
                },
              )
            else
              Text(tr('No logo yet. A PNG or JPEG of at most 1 MB prints beside the name.'),
                  style: theme.textTheme.bodySmall),
            const Gap(8),
            Wrap(spacing: 8, children: [
              FilledButton.tonalIcon(
                key: const ValueKey('profile-logo-upload'),
                onPressed: _busy || !named ? null : _upload,
                style: phoneTapTarget(context),
                icon: const Icon(Icons.image_outlined),
                label: Text(_logo == null ? tr('Add a logo') : tr('Change the logo')),
              ),
              if (_logo != null)
                TextButton(onPressed: _busy ? null : _removeLogo, style: phoneTapTarget(context),
                    child: Text(tr('Remove the logo'))),
            ]),
          ]);
        },
      ),
    );
  }
}
