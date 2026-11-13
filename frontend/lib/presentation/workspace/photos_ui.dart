import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:get_it/get_it.dart';
import 'package:image_picker/image_picker.dart';

import '../../data/datasources/api/api_error.dart';
import 'ops_api.dart';
import 'strings.dart';

/// Photos of written homework (SA-2). Images are fetched as bytes through the
/// signed-in client: on the web an image URL cannot carry the session token.
Future<Uint8List> _bytes(String path) async {
  try {
    final r = await GetIt.I<Dio>().get<List<int>>(path, options: Options(responseType: ResponseType.bytes));
    return Uint8List.fromList(r.data!);
  } on DioException catch (e) {
    throw OpsError.from(e);
  }
}

class PhotoThumb extends StatelessWidget {
  final String path;
  final VoidCallback? onDelete;
  const PhotoThumb({super.key, required this.path, this.onDelete});

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<Uint8List>(
      future: _bytes(path),
      builder: (context, snap) {
        final image = snap.hasData
            ? Image.memory(snap.data!, width: 96, height: 96, fit: BoxFit.cover)
            : SizedBox(width: 96, height: 96,
                child: Center(child: snap.hasError ? const Icon(Icons.broken_image) : const CircularProgressIndicator()));
        return Stack(children: [
          InkWell(
            onTap: snap.hasData
                ? () => showDialog(context: context, builder: (_) => Dialog(child: InteractiveViewer(child: Image.memory(snap.data!))))
                : null,
            child: ClipRRect(borderRadius: BorderRadius.circular(8), child: image),
          ),
          if (onDelete != null)
            Positioned(right: 0, top: 0, child: IconButton(tooltip: tr('Remove photo'),
              visualDensity: VisualDensity.compact, icon: const Icon(Icons.close, size: 18), onPressed: onDelete)),
        ]);
      },
    );
  }
}

/// The student's photos for one homework: add from the camera or gallery,
/// remove before marking.
class MyHomeworkPhotos extends StatefulWidget {
  final String homeworkId;
  final bool editable;
  const MyHomeworkPhotos({super.key, required this.homeworkId, required this.editable});

  @override
  State<MyHomeworkPhotos> createState() => _MyHomeworkPhotosState();
}

class _MyHomeworkPhotosState extends State<MyHomeworkPhotos> {
  late Future<List<Map<String, dynamic>>> _future = _load();
  bool _busy = false;

  Future<List<Map<String, dynamic>>> _load() => Ops.list('/my-homework/${widget.homeworkId}/photos');

  Future<void> _add(ImageSource source) async {
    final picked = await ImagePicker().pickImage(source: source, maxWidth: 2000, imageQuality: 80);
    if (picked == null) return;
    setState(() => _busy = true);
    try {
      final bytes = await picked.readAsBytes();
      final mime = picked.mimeType ?? (picked.name.toLowerCase().endsWith('.png') ? 'image/png' : 'image/jpeg');
      final parts = mime.split('/');
      await GetIt.I<Dio>().post('/my-homework/${widget.homeworkId}/photos',
          data: FormData.fromMap({
            'file': MultipartFile.fromBytes(bytes, filename: picked.name, contentType: DioMediaType(parts[0], parts[1])),
          }));
      setState(() { _future = _load(); });
    } on DioException catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(serverErrorMessage(e))));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<List<Map<String, dynamic>>>(
      future: _future,
      builder: (context, snap) {
        final photos = snap.data ?? const [];
        return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          if (photos.isNotEmpty || widget.editable)
            Text(tr('Written work'), style: Theme.of(context).textTheme.titleSmall),
          const SizedBox(height: 6),
          Wrap(spacing: 8, runSpacing: 8, children: [
            for (final p in photos)
              PhotoThumb(
                path: '/my-homework/${widget.homeworkId}/photos/${p['id']}',
                onDelete: widget.editable
                    ? () async {
                        await Ops.delete('/my-homework/${widget.homeworkId}/photos/${p['id']}');
                        setState(() { _future = _load(); });
                      }
                    : null,
              ),
            if (widget.editable && photos.length < 6) ...[
              OutlinedButton.icon(onPressed: _busy ? null : () => _add(ImageSource.camera),
                  icon: const Icon(Icons.photo_camera_outlined), label: Text(tr('Take photo'))),
              OutlinedButton.icon(onPressed: _busy ? null : () => _add(ImageSource.gallery),
                  icon: const Icon(Icons.photo_library_outlined), label: Text(tr('Choose photo'))),
            ],
          ]),
          if (widget.editable && photos.isNotEmpty)
            Padding(padding: const EdgeInsets.only(top: 4),
                child: Text(tr('Your teacher will mark the written work.'), style: Theme.of(context).textTheme.bodySmall)),
        ]);
      },
    );
  }
}
